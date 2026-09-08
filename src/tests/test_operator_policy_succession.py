"""Exact-key succession never grants a new economic, safety or order owner."""

import json
from pathlib import Path

import pytest

from src.engine import threshold_cycle_preopen_apply as preopen
from src.engine.automation import operator_policy_succession as mod
from src.tests.test_score_recovery_net_approval import (
    PROFILE,
    candidate,
    frequent_small_net_metrics,
    econ,
)


@pytest.fixture
def scope(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    locks = tmp_path / "locks"
    runtime.mkdir()
    locks.mkdir()
    monkeypatch.setattr(preopen, "RUNTIME_ENV_DIR", runtime)
    monkeypatch.setattr(preopen, "OPERATOR_RUNTIME_ENV_LOCK_DIR", locks)
    lock = {
        "family": mod.SCORE,
        "stage": "entry",
        "enabled": True,
        "lock_id": "original-score",
        "priority": 10,
        "lock_until_explicit_close": True,
        "env_overrides": {
            mod.SCORE_PREFIX + k.upper(): str(v) for k, v in PROFILE.items()
        },
    }
    lock["env_overrides"][mod.SCORE_PREFIX + "ENABLED"] = "true"
    (locks / "score.json").write_text(json.dumps(lock))
    return runtime, locks, lock


def ready_candidate():
    metrics = frequent_small_net_metrics()
    c = candidate(metrics)
    c.update(
        stage="entry",
        priority=10,
        allowed_runtime_apply=True,
        safety_revert_required=False,
        calibration_state="adjust_up",
        target_env_keys=[
            "AI_SCORE65_74_RECOVERY_PROBE_" + s
            for s in (
                "ENABLED",
                "MIN_SCORE",
                "MAX_SCORE",
                "MIN_BUY_PRESSURE",
                "MIN_TICK_ACCEL",
                "MIN_MICRO_VWAP_BP",
            )
        ],
    )
    c["current_values"]["enabled"] = True
    c["recommended_values"].update(econ.evaluate_policy(metrics)["profile"])
    return c


def review(c):
    return {
        "items_by_family": {
            mod.SCORE: {
                "guard_accepted": True,
                "route_action": "threshold_candidate",
                "reviewed_current_profile": econ.profile(c["current_values"]),
                "reviewed_recommended_profile": econ.profile(c["recommended_values"]),
                "reviewed_policy_search_sha256": econ.policy_search_digest(
                    c["source_metrics"]
                ),
            }
        }
    }


def select(c, lock, target="2026-09-09", ai=None):
    return preopen._select_auto_apply_candidates(
        [c],
        ai_review=review(c) if ai is None else ai,
        require_ai=True,
        target_date=target,
        operator_locks=[lock],
    )


def publish(scope, c=None, target="2026-09-09"):
    runtime, locks, lock = scope
    selected, decisions, env = select(c or ready_candidate(), lock, target)
    manifest = {
        "target_date": target,
        "source_date": "2026-09-08",
        "auto_apply_selected": selected,
        "auto_apply_decisions": decisions,
    }
    preopen._write_runtime_env(target, manifest, env)
    path = runtime / f"threshold_runtime_env_{target}.json"
    return json.loads(path.read_text()), decisions


def test_ready_small_frequent_net_policy_supersedes_explicit_close_lock(scope):
    runtime, locks, lock = scope
    original = (locks / "score.json").read_bytes()
    manifest, decisions = publish(scope)
    d = decisions[0]
    assert d["selection_change_class"] == "operator_lock_superseded"
    assert d["operator_runtime_env_lock"]["applied"] is False
    values = mod.validate_receipt(manifest, runtime, locks)
    assert values[mod.SCORE_PREFIX + "MIN_BUY_PRESSURE"] == "60"
    assert (locks / "score.json").read_bytes() == original


def test_original_overlay_cannot_overwrite_verified_policy(scope, capsys):
    runtime, locks, _ = scope
    path = runtime / "operator_runtime_overrides.env"
    path.write_text(
        f"export {mod.SCORE_PREFIX}MIN_BUY_PRESSURE=65\nexport KORSTOCKSCAN_SCALP_HARD_STOP=1\n"
    )
    before = path.read_bytes()
    manifest, _ = publish(scope)
    assert (
        mod.main(
            [
                "--target-date",
                "2026-09-09",
                "--runtime-dir",
                str(runtime),
                "--lock-dir",
                str(locks),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert mod.SCORE_PREFIX + "MIN_BUY_PRESSURE=60" in output
    assert "HARD_STOP" not in output
    assert path.read_bytes() == before
    assert mod.validate_receipt(manifest, runtime, locks)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_ai",
        "negative_ev",
        "stale_ai",
        "baseline_mismatch",
        "hold_sample",
        "safety",
        "manual_veto",
        "off",
    ],
)
def test_unqualified_or_protected_lock_does_not_succeed(scope, mutation):
    _, _, lock = scope
    c = ready_candidate()
    ai = review(c)
    if mutation == "missing_ai":
        ai = {}
    elif mutation == "stale_ai":
        ai["items_by_family"][mod.SCORE]["reviewed_policy_search_sha256"] = "old"
    elif mutation == "negative_ev":
        c["source_metrics"] = frequent_small_net_metrics(holdout_net=-70)
        ai = review(c)
    elif mutation == "baseline_mismatch":
        lock["env_overrides"][mod.SCORE_PREFIX + "MIN_BUY_PRESSURE"] = "70"
    elif mutation == "hold_sample":
        c["calibration_state"] = "hold_sample"
    elif mutation == "safety":
        c["safety_revert_required"] = True
    elif mutation == "manual_veto":
        lock["manual_veto"] = True
    elif mutation == "off":
        lock["env_overrides"][mod.SCORE_PREFIX + "ENABLED"] = "false"
    _, decisions, _ = select(c, lock, ai=ai)
    assert not decisions[0].get("operator_policy_succession")


def test_historical_target_never_gets_new_authority(scope):
    _, _, lock = scope
    _, decisions, _ = select(ready_candidate(), lock, "2026-09-08")
    assert decisions[0]["selection_change_class"] == "operator_lock_preserved"


def test_same_day_reentry_and_next_day_sample_gap_keep_successor(scope):
    first, _ = publish(scope)
    c = ready_candidate()
    c["calibration_state"] = "hold_sample"
    for day in ("2026-09-09", "2026-09-10"):
        after, decisions = publish(scope, c, day)
        assert decisions[0]["selection_change_class"] == "policy_carried_forward"
        assert after["env_overrides"][mod.SCORE_PREFIX + "MIN_BUY_PRESSURE"] == "60"
        assert (
            after["operator_policy_succession"]["policies"][0]["applied_target_date"]
            == "2026-09-09"
        )
        mod.validate_receipt(after, *scope[:2])


@pytest.mark.parametrize(
    "kind", ["hash", "date", "env", "owner", "runtime_file", "missing_receipt"]
)
def test_receipt_corruption_fails_closed(scope, kind):
    runtime, locks, _ = scope
    manifest, _ = publish(scope)
    receipt = manifest["operator_policy_succession"]
    if kind == "hash":
        receipt["sha256"] = "bad"
    elif kind == "date":
        manifest["target_date"] = "2026-09-10"
    elif kind == "env":
        manifest["env_overrides"][mod.SCORE_PREFIX + "MIN_BUY_PRESSURE"] = "55"
    elif kind == "owner":
        manifest["selected_families"] = []
    elif kind == "runtime_file":
        (runtime / "threshold_runtime_env_2026-09-09.env").write_text("")
    else:
        manifest.pop("operator_policy_succession")
    with pytest.raises(ValueError):
        mod.validate_receipt(manifest, runtime, locks)


def test_new_operator_instruction_is_not_silently_overridden(scope):
    runtime, locks, _ = scope
    manifest, _ = publish(scope)
    (runtime / "operator_runtime_overrides.env").write_text(
        f"export {mod.SCORE_PREFIX}ENABLED=false\n"
    )
    with pytest.raises(ValueError, match="source_changed"):
        mod.validate_receipt(manifest, runtime, locks)


def test_unrelated_operator_setting_does_not_invalidate_policy(scope):
    runtime, locks, _ = scope
    manifest, _ = publish(scope)
    (runtime / "operator_runtime_overrides.env").write_text(
        "export UNRELATED_OPERATOR_SETTING=changed\n"
    )
    assert mod.validate_receipt(manifest, runtime, locks)


def test_exact_key_allowlist_rejects_safety_quantity_and_provider(scope):
    runtime, _, lock = scope
    c = ready_candidate()
    current = mod.current_locked_values(lock, runtime, "2026-09-09")
    for key in (
        "KORSTOCKSCAN_SCALP_HARD_STOP",
        "KORSTOCKSCAN_ORDER_QTY",
        mod.SCORE_PREFIX + "MAX_QUOTE_STALE_AGE_MS",
    ):
        assert (
            mod.succession_reason(
                c,
                lock,
                {key: "1"},
                current,
                ordinary_allowed=True,
                target_date="2026-09-09",
            )
            == "candidate_key_ownership_mismatch"
        )


def test_all_installed_json_locks_have_explicit_classification():
    root = Path(__file__).resolve().parents[2]
    locks = [
        json.loads(p.read_text())
        for p in (root / "data/threshold_cycle/operator_runtime_env_locks").glob(
            "*.json"
        )
    ]
    report = mod.inventory(locks)
    assert report["lock_count"] == len(locks)
    assert locks
    assert not [
        r for r in report["locks"] if r["classification"] == "unclassified_protected"
    ]
    assert all(
        mod.classify({"family": f}) != "strategy_auto_successor"
        for f in mod.PROTECTED_FAMILIES
    )


def test_launcher_reasserts_only_receipted_policy_after_operator_layers():
    text = (Path(__file__).resolve().parents[1] / "run_bot.sh").read_text()
    start = text.index('DATED_OPERATOR_RUNTIME_OVERRIDES="')
    apply = text.index(
        'apply_verified_operator_policy_successions "$RUNTIME_TARGET_DATE"', start
    )
    assert (
        start
        < apply
        < text.index(
            'verify_threshold_runtime_env_handoff "$RUNTIME_TARGET_DATE"', apply
        )
    )


def test_dated_instruction_expiration_does_not_require_manual_reapproval(scope):
    runtime, _, _ = scope
    (runtime / "operator_runtime_overrides_2026-09-09.env").write_text(
        f"export {mod.SCORE_PREFIX}MIN_BUY_PRESSURE=65\n"
    )
    publish(scope)
    c = ready_candidate()
    c["calibration_state"] = "hold_sample"
    manifest, _ = publish(scope, c, "2026-09-10")
    assert manifest["env_overrides"][mod.SCORE_PREFIX + "MIN_BUY_PRESSURE"] == "60"


def test_successor_is_formal_entry_owner_not_operator_exemption(scope):
    _, decisions = publish(scope)
    assert preopen._entry_live_tuning_owner_family(decisions) == mod.SCORE


def test_effective_floor_change_invalidates_old_economic_profile(scope):
    runtime, locks, _ = scope
    manifest, _ = publish(scope)
    (runtime / "operator_runtime_overrides.env").write_text(
        f"export {mod.SCORE_PREFIX}EFFECTIVE_MIN_MICRO_VWAP_FLOOR_BP=20\n"
    )
    with pytest.raises(ValueError, match="source_changed"):
        mod.validate_receipt(manifest, runtime, locks)


def test_same_stage_conflict_cannot_use_lock_to_approve_successor(scope):
    _, _, lock = scope
    c = ready_candidate()
    competing = {**lock, "family": "unregistered_entry_owner", "priority": 1}
    _, decisions, _ = preopen._select_auto_apply_candidates(
        [c],
        ai_review=review(c),
        require_ai=True,
        target_date="2026-09-09",
        operator_locks=[lock, competing],
    )
    d = next(d for d in decisions if d["family"] == mod.SCORE)
    assert not d.get("operator_policy_succession")


def test_pyramid_recomputes_existing_grid_before_succession(scope):
    runtime, _, _ = scope
    key = next(iter(mod.POLICY_KEYS[mod.PYRAMID]))
    c = dict(
        family=mod.PYRAMID,
        stage="scale_in",
        allowed_runtime_apply=True,
        current_value=1.1,
        recommended_value=1.0,
        current_values={"min_profit_pct": 1.1},
        recommended_values={"min_profit_pct": 1.0},
        bounds={"min": 0.1, "max": 3.0},
        max_step_per_day=0.2,
        runtime_update_mode="single_cumulative_quality_update",
        evidence_digest="evidence",
        cumulative_quality_window={
            "window_policy": "clean_baseline_cumulative",
            "source_dates": ["2026-09-07", "2026-09-08"],
            "end_date": "2026-09-08",
        },
        source_quality_gate="pass",
        decision_evidence_gate="pass",
        source_metrics={
            "profit_threshold_grid": [
                {
                    "min_profit_pct": 1.1,
                    "eligible_count": 20,
                    "equal_weight_expected_net_profit_contribution_pct": 0.1,
                },
                {
                    "min_profit_pct": 1.0,
                    "eligible_count": 20,
                    "equal_weight_expected_net_profit_contribution_pct": 0.2,
                },
            ]
        },
    )
    lock = {
        "family": mod.PYRAMID,
        "stage": "scale_in",
        "enabled": True,
        "env_overrides": {key: "1.1"},
    }

    def reason():
        return mod.succession_reason(
            c,
            lock,
            {key: "1.0"},
            mod.current_locked_values(lock, runtime, "2026-09-09"),
            ordinary_allowed=True,
            target_date="2026-09-09",
        )

    assert reason() == ""
    c["source_metrics"]["profit_threshold_grid"][1][
        "equal_weight_expected_net_profit_contribution_pct"
    ] = -0.1
    assert reason() == "family_economic_replay_not_ready"


def test_runtime_summary_does_not_call_successor_original_operator_lock(scope):
    from src.engine import runtime_approval_summary as summary

    _, decisions = publish(scope)
    assert "검증 정책" in summary._current_application(
        mod.SCORE, "adjust_up", True, decisions[0]
    )
    assert "과거 lock 복원" in summary._state_interpretation(
        "hold_sample", True, decisions[0]
    )


@pytest.mark.parametrize(
    "family,closer",
    [
        ("early_accel_recheck_runtime", "_close_early_accel_recheck_for_live_owner"),
        (
            "pre_submit_liquidity_relief_runtime",
            "_close_pre_submit_liquidity_relief_for_live_owner",
        ),
        (
            "weak_context_late_entry_guard_runtime",
            "_close_weak_context_late_entry_guard_for_live_owner",
        ),
        (
            "scalping_scanner_real_source_guard_runtime",
            "_close_scalping_scanner_real_source_guard_for_live_owner",
        ),
        (
            "score65_74_recovery_probe_strong_micro_override_runtime",
            "_close_score65_74_strong_micro_override_for_live_owner",
        ),
    ],
)
def test_formal_successor_uses_existing_legacy_integration_hooks(scope, family, closer):
    _, decisions = publish(scope)
    owner = preopen._entry_live_tuning_owner_family(decisions)
    old = {
        "family": family,
        "selected": True,
        "env_overrides": {},
        "operator_runtime_env_lock": {"applied": True, "lock_id": "legacy"},
    }
    selected, final, _ = getattr(preopen, closer)(
        selected=[*decisions, old],
        decisions=[*decisions, old],
        env_overrides={},
        owner_family=owner,
    )
    assert not any(d["family"] == family for d in selected)
    assert next(d for d in final if d["family"] == family)["selected"] is False
    assert (
        mod.classify({"family": family}) == "existing_formal_entry_owner_supersession"
    )


def test_wrong_stage_cannot_hide_entry_canary_conflict(scope):
    _, _, lock = scope
    c = ready_candidate()
    c["stage"] = "holding_exit"
    _, decisions, _ = select(c, lock)
    assert not decisions[0].get("operator_policy_succession")
    assert (
        decisions[0]["operator_policy_succession_blocker"]
        == "successor_owner_or_stage_mismatch"
    )


def test_multi_assignment_manual_veto_is_not_ignored(scope):
    runtime, _, lock = scope
    path = runtime / "operator_runtime_overrides.env"
    path.write_text(f"export {mod.SCORE_PREFIX}ENABLED=false UNRELATED=1\n")
    _, decisions, _ = select(ready_candidate(), lock)
    assert not decisions[0].get("operator_policy_succession")
    assert mod.read_operator_env(path)[mod.SCORE_PREFIX + "ENABLED"] == "false"


def test_unsupported_owned_shell_expression_fails_closed(scope):
    runtime, _, _ = scope
    path = runtime / "operator_runtime_overrides.env"
    path.write_text(f"unset {mod.SCORE_PREFIX}ENABLED\n")
    with pytest.raises(ValueError, match="expression_not_supported"):
        mod.read_operator_env(path)


def test_avg_down_approved_provenance_survives_family_owned_hold(scope):
    from src.tests.test_threshold_cycle_preopen_apply import _valid_avg_down_candidate

    runtime, locks, _ = scope
    c = _valid_avg_down_candidate()
    c["source_date"] = c["target_date"] = "2026-09-08"
    c["cumulative_quality_window"].update(
        end_date="2026-09-08", source_dates=["2026-09-08"]
    )
    key = "KORSTOCKSCAN_SHALLOW_VOLATILITY_AVG_DOWN_MIN_BUY_PRESSURE"
    lock = {
        "family": mod.AVG_DOWN,
        "stage": "scale_in",
        "enabled": True,
        "lock_id": "avg-lock",
        "priority": 37,
        "env_overrides": {key: "85"},
    }
    (locks / "avg.json").write_text(json.dumps(lock))
    ai = {
        "items_by_family": {
            mod.AVG_DOWN: {
                **c,
                "guard_accepted": True,
                "route_action": "threshold_candidate",
            }
        }
    }
    for day in ("2026-09-09", "2026-09-10"):
        selected, decisions, env = preopen._select_auto_apply_candidates(
            [c], ai_review=ai, require_ai=True, target_date=day, operator_locks=[lock]
        )
        manifest = {
            "source_date": "2026-09-08",
            "auto_apply_selected": selected,
            "auto_apply_decisions": decisions,
        }
        preopen._write_runtime_env(day, manifest, env)
        written = json.loads(
            (runtime / f"threshold_runtime_env_{day}.json").read_text()
        )
        values = mod.validate_receipt(written, runtime, locks)
        assert values[key] == "80"
        assert (
            values["KORSTOCKSCAN_AVG_DOWN_RUNTIME_QUALITY_UPDATE_ID"]
            == "avg-down-quality-1"
        )
        c.update(
            calibration_state="hold_runtime_scope",
            allowed_runtime_apply=False,
            current_value=80.0,
            sample_floor_passed=False,
            recommended_values_changed=False,
        )
    assert decisions[0]["selection_change_class"] == "policy_carried_forward"
