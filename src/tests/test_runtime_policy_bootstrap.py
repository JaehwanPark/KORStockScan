import json
from pathlib import Path

from src.engine.automation import runtime_policy_bootstrap as bootstrap
from src.engine import runtime_approval_summary as summary_mod
from src.engine import verify_threshold_cycle_postclose_chain as verifier


def _write(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _rising_source_report(
    monkeypatch, tmp_path: Path, source_date: str, *, status: str
) -> dict:
    report_dir = tmp_path / "report" / "rising_missed_classifier_prior"
    monkeypatch.setattr(bootstrap, "RISING_MISSED_REPORT_DIR", report_dir)
    report = {
        "schema_version": 2,
        "report_type": "rising_missed_classifier_prior",
        "target_date": source_date,
        "status": status,
        "economic_evaluation": {
            "comparison_status": status,
            "allowed_runtime_apply": status == "validated_edge",
            "validated_candidate_count": 1 if status == "validated_edge" else 0,
        },
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    report["artifact_sha256"] = bootstrap._digest_json(report)
    _write(report_dir / f"rising_missed_classifier_prior_{source_date}.json", report)
    return report


def test_bootstrap_carries_incumbent_applies_lock_and_scrubs_retired(monkeypatch, tmp_path):
    boot_dir = tmp_path / "runtime" / "policy_bootstrap"
    legacy_dir = tmp_path / "threshold_cycle" / "runtime_env"
    lock_dir = tmp_path / "threshold_cycle" / "operator_runtime_env_locks"
    monkeypatch.setattr(bootstrap, "BOOTSTRAP_DIR", boot_dir)
    monkeypatch.setattr(bootstrap, "LEGACY_RUNTIME_DIR", legacy_dir)
    monkeypatch.setattr(bootstrap, "OPERATOR_LOCK_DIR", lock_dir)
    _write(
        legacy_dir / "threshold_runtime_env_2026-09-18.json",
        {
            "target_date": "2026-09-18",
            "env_overrides": {
                "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED": "true",
                "KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED": "true",
            },
            "selected_families": ["score65_74_recovery_probe", "limit_down_watch"],
        },
    )
    _write(
        legacy_dir / "threshold_runtime_env_verify_2026-09-18.json",
        {"target_date": "2026-09-18", "status": "pass", "passed": True},
    )
    _write(
        lock_dir / "score.json",
        {
            "lock_id": "score-lock",
            "family": "score65_74_recovery_probe",
            "enabled": True,
            "env_overrides": {
                "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_SCORE": "69"
            },
        },
    )
    _write(
        lock_dir / "expired.json",
        {
            "lock_id": "expired-lock",
            "family": "expired_family",
            "enabled": True,
            "target_date": "2026-09-18",
            "env_key": "KORSTOCKSCAN_EXPIRED_SHOULD_NOT_LOAD",
            "env_value": "true",
        },
    )
    receipt = tmp_path / "runtime" / "direct_family_2026-09-19.json"
    _write(
        receipt,
        {
            "report_type": "direct_family",
            "target_date": "2026-09-19",
            "status": "approved",
            "allowed_runtime_apply": True,
            "runtime_effect": True,
        },
    )
    manifest = bootstrap.write_bootstrap("2026-09-19", receipt_paths=[receipt])
    assert manifest["assertions"] == {
        "provider_called": False,
        "broker_called": False,
        "order_submitted": False,
        "economic_candidate_created": False,
    }
    assert manifest["env_overrides"]["KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_SCORE"] == "69"
    assert (
        manifest["env_overrides"][
            "KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED"
        ]
        == "true"
    )
    assert (
        manifest["env_overrides"]["KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE"]
        == "2026-09-19"
    )
    assert (
        manifest["env_key_owners"]["KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE"]
        == "runtime_policy_bootstrap_exact_date_handoff"
    )
    assert manifest["env_overrides"]["KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED"] == "false"
    assert "limit_down_watch" not in manifest["selected_families"]
    assert "KORSTOCKSCAN_EXPIRED_SHOULD_NOT_LOAD" not in manifest["env_overrides"]
    assert manifest["direct_family_receipts"][0]["family"] == "direct_family"
    assert any(
        row.get("reason") == "outside_active_window"
        for row in manifest["operator_locks_rejected"]
    )
    assert bootstrap.verify_bootstrap("2026-09-19")["status"] == "pass"
    receipt.write_text("{}", encoding="utf-8")
    assert "source_receipt_hash_mismatch" in " ".join(
        bootstrap.verify_bootstrap("2026-09-19", write=False)["findings"]
    )
    _write(
        receipt,
        {
            "report_type": "direct_family",
            "target_date": "2026-09-19",
            "status": "approved",
            "allowed_runtime_apply": True,
            "runtime_effect": True,
        },
    )
    bootstrap.env_path("2026-09-19").write_text("tampered\n", encoding="utf-8")
    assert bootstrap.verify_bootstrap("2026-09-19")["status"] == "fail"


def test_bootstrap_preserves_explicit_operator_handoff_veto(monkeypatch, tmp_path):
    boot_dir = tmp_path / "runtime" / "policy_bootstrap"
    legacy_dir = tmp_path / "threshold_cycle" / "runtime_env"
    monkeypatch.setattr(bootstrap, "BOOTSTRAP_DIR", boot_dir)
    monkeypatch.setattr(bootstrap, "LEGACY_RUNTIME_DIR", legacy_dir)
    monkeypatch.setattr(bootstrap, "OPERATOR_LOCK_DIR", tmp_path / "locks")
    _write(
        legacy_dir / "threshold_runtime_env_2026-09-18.json",
        {"target_date": "2026-09-18", "env_overrides": {"BASE": "1"}},
    )
    _write(
        legacy_dir / "threshold_runtime_env_verify_2026-09-18.json",
        {"status": "pass"},
    )
    (legacy_dir / "operator_runtime_overrides.env").write_text(
        "export KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED=false\n",
        encoding="utf-8",
    )

    manifest = bootstrap.write_bootstrap("2026-09-19")

    assert (
        manifest["env_overrides"][
            "KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED"
        ]
        == "false"
    )
    assert (
        manifest["env_key_owners"][
            "KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED"
        ]
        == "operator_runtime_override"
    )
    verification = bootstrap.verify_bootstrap("2026-09-19", write=False)
    assert verification["status"] == "fail"
    assert "exact_date_runtime_auto_apply_disabled" in verification["findings"]


def test_pid_verification_compares_launcher_context_overlay(monkeypatch, tmp_path):
    boot_dir = tmp_path / "runtime" / "policy_bootstrap"
    legacy_dir = tmp_path / "threshold_cycle" / "runtime_env"
    monkeypatch.setattr(bootstrap, "BOOTSTRAP_DIR", boot_dir)
    monkeypatch.setattr(bootstrap, "LEGACY_RUNTIME_DIR", legacy_dir)
    monkeypatch.setattr(bootstrap, "OPERATOR_LOCK_DIR", tmp_path / "locks")
    _write(
        legacy_dir / "threshold_runtime_env_2026-09-18.json",
        {
            "target_date": "2026-09-18",
            "env_overrides": {
                "KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ENABLED": "true"
            },
        },
    )
    _write(
        legacy_dir / "threshold_runtime_env_verify_2026-09-18.json",
        {"status": "pass"},
    )
    bootstrap.write_bootstrap("2026-09-19")
    expected = bootstrap.operator_policy_succession.read_operator_env(
        bootstrap.env_path("2026-09-19")
    )
    expected["KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ENABLED"] = "false"
    monkeypatch.setattr(
        bootstrap,
        "_launcher_ai_context_overlay",
        lambda target_date: {
            "KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ENABLED": "false"
        },
    )
    monkeypatch.setattr(bootstrap, "_read_proc_env", lambda pid: expected)

    verification = bootstrap.verify_bootstrap("2026-09-19", pid=123, write=False)

    assert verification["status"] == "pass"
    assert verification["pid_passed"] is True
    assert verification["pid_mismatches"] == []


def test_verify_cli_persists_receipt_only_when_explicit(monkeypatch, capsys):
    calls = []

    def fake_verify(target_date, *, pid=None, write=True):
        calls.append((target_date, pid, write))
        return {"status": "pass"}

    monkeypatch.setattr(bootstrap, "verify_bootstrap", fake_verify)

    assert bootstrap.main(
        ["--verify", "--target-date", "2026-09-21", "--pid", "123"]
    ) == 0
    assert calls[-1] == ("2026-09-21", 123, False)
    capsys.readouterr()

    assert bootstrap.main(
        [
            "--verify",
            "--target-date",
            "2026-09-21",
            "--pid",
            "123",
            "--write-verify-artifact",
        ]
    ) == 0
    assert calls[-1] == ("2026-09-21", 123, True)


def test_bootstrap_rerun_does_not_create_self_referential_incumbent(
    monkeypatch, tmp_path
):
    boot_dir = tmp_path / "runtime" / "policy_bootstrap"
    legacy_dir = tmp_path / "threshold_cycle" / "runtime_env"
    monkeypatch.setattr(bootstrap, "BOOTSTRAP_DIR", boot_dir)
    monkeypatch.setattr(bootstrap, "LEGACY_RUNTIME_DIR", legacy_dir)
    monkeypatch.setattr(
        bootstrap,
        "OPERATOR_LOCK_DIR",
        tmp_path / "threshold_cycle" / "operator_runtime_env_locks",
    )
    _write(
        legacy_dir / "threshold_runtime_env_2026-09-19.json",
        {
            "target_date": "2026-09-19",
            "env_overrides": {"KORSTOCKSCAN_ACTIVE_POLICY": "true"},
            "selected_families": ["active_policy"],
        },
    )
    _write(
        legacy_dir / "threshold_runtime_env_verify_2026-09-19.json",
        {"target_date": "2026-09-19", "status": "pass", "passed": True},
    )

    first = bootstrap.write_bootstrap("2026-09-19")
    assert bootstrap.verify_bootstrap("2026-09-19")["status"] == "pass"
    second = bootstrap.write_bootstrap("2026-09-19")

    assert second["source_incumbent"]["path"] == first["source_incumbent"]["path"]
    assert bootstrap.verify_bootstrap("2026-09-19")["status"] == "pass"


def test_bootstrap_rejects_report_only_receipt(monkeypatch, tmp_path):
    legacy_dir = tmp_path / "threshold_cycle" / "runtime_env"
    monkeypatch.setattr(bootstrap, "BOOTSTRAP_DIR", tmp_path / "bootstrap")
    monkeypatch.setattr(bootstrap, "LEGACY_RUNTIME_DIR", legacy_dir)
    monkeypatch.setattr(bootstrap, "OPERATOR_LOCK_DIR", tmp_path / "locks")
    _write(
        legacy_dir / "threshold_runtime_env_2026-09-18.json",
        {
            "target_date": "2026-09-18",
            "env_overrides": {"KORSTOCKSCAN_ACTIVE_POLICY": "true"},
        },
    )
    _write(
        legacy_dir / "threshold_runtime_env_verify_2026-09-18.json",
        {"status": "pass"},
    )
    receipt = tmp_path / "machine.json"
    _write(
        receipt,
        {
            "report_type": "machine_microstructure_policy_approval",
            "target_date": "2026-09-19",
            "allowed_runtime_apply": False,
            "runtime_effect": False,
        },
    )

    manifest = bootstrap.build_manifest("2026-09-19", receipt_paths=[receipt])

    assert manifest["direct_family_receipts"] == []
    assert manifest["direct_family_receipts_rejected"][0]["family"] == (
        "machine_microstructure"
    )
    assert manifest["direct_family_receipts_rejected"][0]["reason"] == (
        "runtime_apply_not_authorized"
    )


def test_bootstrap_applies_bounded_rising_missed_policy_before_operator_locks(
    monkeypatch, tmp_path
):
    legacy_dir = tmp_path / "threshold_cycle" / "runtime_env"
    lock_dir = tmp_path / "threshold_cycle" / "operator_runtime_env_locks"
    monkeypatch.setattr(bootstrap, "BOOTSTRAP_DIR", tmp_path / "bootstrap")
    monkeypatch.setattr(bootstrap, "LEGACY_RUNTIME_DIR", legacy_dir)
    monkeypatch.setattr(bootstrap, "OPERATOR_LOCK_DIR", lock_dir)
    _write(
        legacy_dir / "threshold_runtime_env_2026-09-18.json",
        {"target_date": "2026-09-18", "env_overrides": {"BASE": "1"}},
    )
    _write(
        legacy_dir / "threshold_runtime_env_verify_2026-09-18.json",
        {"status": "pass"},
    )
    receipt = tmp_path / "rising.json"
    source = _rising_source_report(
        monkeypatch, tmp_path, "2026-09-18", status="validated_edge"
    )
    policy = {
            "report_type": "rising_missed_tp1_policy",
            "runtime_family": "rising_missed_tp1_selector",
            "source_date": "2026-09-18",
            "effective_date": "2026-09-19",
            "status": "validated_edge",
            "selected_axis": "positive_support_min",
            "allowed_runtime_apply": True,
            "runtime_effect": True,
            "source_report_sha256": source["artifact_sha256"],
            "consumer_schema": "rising_missed_tp1_selector_bounded_env_v1",
            "runtime_env_overrides": {
                "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED": "true",
                "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE": "2026-09-19",
                "KORSTOCKSCAN_RISING_MISSED_TP1_POSITIVE_SUPPORT_MIN": "1",
            },
        }
    policy["policy_sha256"] = bootstrap.direct_policy_digest(policy)
    policy["runtime_env_overrides"][
        "KORSTOCKSCAN_RISING_MISSED_TP1_POLICY_SHA256"
    ] = policy["policy_sha256"]
    _write(receipt, policy)

    manifest = bootstrap.build_manifest("2026-09-19", receipt_paths=[receipt])

    assert manifest["env_overrides"]["KORSTOCKSCAN_RISING_MISSED_TP1_POSITIVE_SUPPORT_MIN"] == "1"
    assert manifest["env_key_owners"]["KORSTOCKSCAN_RISING_MISSED_TP1_POSITIVE_SUPPORT_MIN"] == "direct_policy:rising_missed_tp1_selector"
    assert manifest["direct_family_receipts"][0]["family"] == "rising_missed_tp1_selector"

    bootstrap.write_bootstrap("2026-09-19", receipt_paths=[receipt])
    assert bootstrap.verify_bootstrap("2026-09-19", write=False)["passed"] is True
    source["economic_evaluation"]["validated_candidate_count"] = 0
    _write(
        bootstrap.RISING_MISSED_REPORT_DIR / "rising_missed_classifier_prior_2026-09-18.json",
        source,
    )
    verification = bootstrap.verify_bootstrap("2026-09-19", write=False)
    assert verification["passed"] is False
    assert "rising_missed_source_binding_invalid:source_report_sha256_mismatch" in verification["findings"]


def test_bootstrap_rejects_out_of_bounds_rising_missed_policy(monkeypatch, tmp_path):
    legacy_dir = tmp_path / "threshold_cycle" / "runtime_env"
    monkeypatch.setattr(bootstrap, "BOOTSTRAP_DIR", tmp_path / "bootstrap")
    monkeypatch.setattr(bootstrap, "LEGACY_RUNTIME_DIR", legacy_dir)
    monkeypatch.setattr(bootstrap, "OPERATOR_LOCK_DIR", tmp_path / "locks")
    _write(legacy_dir / "threshold_runtime_env_2026-09-18.json", {"target_date": "2026-09-18", "env_overrides": {"BASE": "1"}})
    _write(legacy_dir / "threshold_runtime_env_verify_2026-09-18.json", {"status": "pass"})
    receipt = tmp_path / "rising.json"
    _write(receipt, {
        "report_type": "rising_missed_tp1_policy",
        "runtime_family": "rising_missed_tp1_selector",
        "effective_date": "2026-09-19",
        "allowed_runtime_apply": True,
        "selected_axis": "positive_support_min",
        "runtime_env_overrides": {
            "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED": "true",
            "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE": "2026-09-19",
            "KORSTOCKSCAN_RISING_MISSED_TP1_POSITIVE_SUPPORT_MIN": "0",
            "KORSTOCKSCAN_RISING_MISSED_TP1_POLICY_SHA256": "b" * 64,
        },
    })

    manifest = bootstrap.build_manifest("2026-09-19", receipt_paths=[receipt])

    assert manifest["direct_family_receipts"] == []
    assert manifest["direct_family_receipts_rejected"][0]["reason"] == "runtime_env_value_out_of_bounds"


def test_bootstrap_rejects_multi_axis_rising_policy(monkeypatch, tmp_path):
    legacy_dir = tmp_path / "threshold_cycle" / "runtime_env"
    monkeypatch.setattr(bootstrap, "BOOTSTRAP_DIR", tmp_path / "bootstrap")
    monkeypatch.setattr(bootstrap, "LEGACY_RUNTIME_DIR", legacy_dir)
    monkeypatch.setattr(bootstrap, "OPERATOR_LOCK_DIR", tmp_path / "locks")
    _write(
        legacy_dir / "threshold_runtime_env_2026-09-18.json",
        {"target_date": "2026-09-18", "env_overrides": {"BASE": "1"}},
    )
    _write(
        legacy_dir / "threshold_runtime_env_verify_2026-09-18.json",
        {"status": "pass"},
    )
    source = _rising_source_report(
        monkeypatch, tmp_path, "2026-09-18", status="validated_edge"
    )
    receipt = tmp_path / "rising.json"
    policy = {
        "report_type": "rising_missed_tp1_policy",
        "runtime_family": "rising_missed_tp1_selector",
        "source_date": "2026-09-18",
        "effective_date": "2026-09-19",
        "status": "validated_edge",
        "selected_axis": "positive_support_min",
        "allowed_runtime_apply": True,
        "runtime_effect": True,
        "source_report_sha256": source["artifact_sha256"],
        "consumer_schema": "rising_missed_tp1_selector_bounded_env_v1",
        "runtime_env_overrides": {
            "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED": "true",
            "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE": "2026-09-19",
            "KORSTOCKSCAN_RISING_MISSED_TP1_POSITIVE_SUPPORT_MIN": "1",
            "KORSTOCKSCAN_RISING_MISSED_TP1_SPREAD_CAUTION_RATIO": "0.0015",
        },
    }
    policy["policy_sha256"] = bootstrap.direct_policy_digest(policy)
    policy["runtime_env_overrides"][
        "KORSTOCKSCAN_RISING_MISSED_TP1_POLICY_SHA256"
    ] = policy["policy_sha256"]
    _write(receipt, policy)

    manifest = bootstrap.build_manifest("2026-09-19", receipt_paths=[receipt])

    assert manifest["direct_family_receipts"] == []
    assert manifest["direct_family_receipts_rejected"][0]["reason"] == (
        "runtime_env_single_axis_required"
    )


def test_bootstrap_accepts_hash_bound_incumbent_preserved_receipt(monkeypatch, tmp_path):
    legacy_dir = tmp_path / "threshold_cycle" / "runtime_env"
    monkeypatch.setattr(bootstrap, "BOOTSTRAP_DIR", tmp_path / "bootstrap")
    monkeypatch.setattr(bootstrap, "LEGACY_RUNTIME_DIR", legacy_dir)
    monkeypatch.setattr(bootstrap, "OPERATOR_LOCK_DIR", tmp_path / "locks")
    _write(legacy_dir / "threshold_runtime_env_2026-09-18.json", {"target_date": "2026-09-18", "env_overrides": {"BASE": "1"}})
    _write(legacy_dir / "threshold_runtime_env_verify_2026-09-18.json", {"status": "pass"})
    receipt = tmp_path / "rising.json"
    source = _rising_source_report(
        monkeypatch, tmp_path, "2026-09-18", status="measured_no_edge"
    )
    policy = {
        "report_type": "rising_missed_tp1_policy",
        "runtime_family": "rising_missed_tp1_selector",
        "source_date": "2026-09-18",
        "effective_date": "2026-09-19",
        "status": "incumbent_preserved",
        "allowed_runtime_apply": True,
        "runtime_effect": False,
        "source_report_sha256": source["artifact_sha256"],
        "consumer_schema": "rising_missed_tp1_selector_bounded_env_v1",
        "runtime_env_overrides": {},
    }
    policy["policy_sha256"] = bootstrap.direct_policy_digest(policy)
    _write(receipt, policy)

    manifest = bootstrap.build_manifest("2026-09-19", receipt_paths=[receipt])

    assert len(manifest["direct_family_receipts"]) == 1
    assert manifest["direct_family_receipts"][0]["runtime_env_overrides"] == {}
    assert manifest["env_overrides"]["BASE"] == "1"


def test_bootstrap_rejects_rising_policy_without_bound_source_report(
    monkeypatch, tmp_path
):
    legacy_dir = tmp_path / "threshold_cycle" / "runtime_env"
    monkeypatch.setattr(bootstrap, "BOOTSTRAP_DIR", tmp_path / "bootstrap")
    monkeypatch.setattr(bootstrap, "LEGACY_RUNTIME_DIR", legacy_dir)
    monkeypatch.setattr(bootstrap, "OPERATOR_LOCK_DIR", tmp_path / "locks")
    monkeypatch.setattr(
        bootstrap,
        "RISING_MISSED_REPORT_DIR",
        tmp_path / "report" / "rising_missed_classifier_prior",
    )
    _write(
        legacy_dir / "threshold_runtime_env_2026-09-18.json",
        {"target_date": "2026-09-18", "env_overrides": {"BASE": "1"}},
    )
    _write(
        legacy_dir / "threshold_runtime_env_verify_2026-09-18.json",
        {"status": "pass"},
    )
    receipt = tmp_path / "rising.json"
    policy = {
        "report_type": "rising_missed_tp1_policy",
        "runtime_family": "rising_missed_tp1_selector",
        "source_date": "2026-09-18",
        "effective_date": "2026-09-19",
        "status": "incumbent_preserved",
        "allowed_runtime_apply": True,
        "runtime_effect": False,
        "source_report_sha256": "a" * 64,
        "consumer_schema": "rising_missed_tp1_selector_bounded_env_v1",
        "runtime_env_overrides": {},
    }
    policy["policy_sha256"] = bootstrap.direct_policy_digest(policy)
    _write(receipt, policy)

    manifest = bootstrap.build_manifest("2026-09-19", receipt_paths=[receipt])

    assert manifest["direct_family_receipts"] == []
    assert manifest["direct_family_receipts_rejected"][0]["reason"] == (
        "source_report_unreadable"
    )


def test_bootstrap_seeds_from_legacy_common_handoff_only_when_family_checks_pass(
    monkeypatch, tmp_path
):
    legacy_dir = tmp_path / "threshold_cycle" / "runtime_env"
    monkeypatch.setattr(bootstrap, "BOOTSTRAP_DIR", tmp_path / "bootstrap")
    monkeypatch.setattr(bootstrap, "LEGACY_RUNTIME_DIR", legacy_dir)
    monkeypatch.setattr(bootstrap, "OPERATOR_LOCK_DIR", tmp_path / "locks")
    manifest_path = legacy_dir / "threshold_runtime_env_2026-09-18.json"
    verify_path = legacy_dir / "threshold_runtime_env_verify_2026-09-18.json"
    _write(
        manifest_path,
        {
            "target_date": "2026-09-18",
            "env_overrides": {"KORSTOCKSCAN_ACTIVE_POLICY": "true"},
            "selected_families": ["active_policy"],
        },
    )
    verification = {
        "target_date": "2026-09-18",
        "status": "fail",
        "passed": False,
        "fail_reason": "runtime_env_handoff_missing",
        "runtime_policy_fail_count": 0,
        "dated_runtime_override_fail_count": 0,
        "unverified_selected_family_count": 0,
        "missing_family_count": 0,
        "selected_families": ["active_policy"],
        "findings": [
            {
                "family": "integrated_entry_axis_bundle",
                "severity": "runtime_policy_unusable",
                "detail": "integrated_axis_unconfigured",
            }
        ],
    }
    _write(verify_path, verification)

    manifest = bootstrap.build_manifest("2026-09-21")

    assert manifest["env_overrides"]["KORSTOCKSCAN_ACTIVE_POLICY"] == "true"
    assert manifest["source_incumbent_verification_basis"] == (
        "legacy_common_handoff_migration"
    )

    verification["runtime_policy_fail_count"] = 1
    _write(verify_path, verification)
    try:
        bootstrap.build_manifest("2026-09-21")
    except ValueError as exc:
        assert str(exc) == "approved_incumbent_runtime_env_missing"
    else:
        raise AssertionError("active family verification failure must stay blocked")


def test_direct_summary_and_verifier_do_not_require_retired_common_reports(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(summary_mod, "DATA_DIR", data_dir)
    monkeypatch.setattr(summary_mod, "REPORT_DIR", data_dir / "report" / "runtime_approval_summary")
    target = "2026-09-19"
    for owner, path in summary_mod._paths(target).items():
        if owner == "runtime_bootstrap":
            continue
        _write(path, {"report_type": owner, "target_date": target, "status": "pass"})
    summary = summary_mod.build_runtime_approval_summary(target)
    assert summary["status"] == summary_mod.DIRECT_EVIDENCE_COMPLETE
    assert summary["daily_threshold_cycle_retired"] is True
    assert summary["threshold_cycle_ev_retired"] is True

    monkeypatch.setattr(verifier, "DATA_DIR", data_dir)
    monkeypatch.setattr(verifier, "REPORT_DIR", data_dir / "report")
    monkeypatch.setattr(verifier, "OUTPUT_DIR", data_dir / "report" / "threshold_cycle_postclose_verification")
    terminal_path = data_dir / "report" / "threshold_cycle_postclose_status" / f"threshold_cycle_postclose_{target}.status.json"
    # Retirement of common reports never waives native terminal provenance.
    _write(terminal_path, {"target_date": target, "status": "succeeded"})
    assert verifier.build_threshold_cycle_postclose_verification(target)["status"] == "fail"
    proof = tmp_path / "main-precommit.json"
    identity = {"run_id": "current-run", "code_commit": "a" * 40}
    _write(proof, {"date": target, "status": "pass", "verification_scope": "main_precommit", **identity})
    _write(terminal_path, {
        "target_date": target, "status": "succeeded", "exit_code": 0, **identity,
        "started_at": f"{target}T20:10:00+09:00", "finished_at": f"{target}T21:00:00+09:00",
        "verification_receipt": {"path": str(proof), "sha256": verifier._sha(proof)},
    })
    report = verifier.build_threshold_cycle_postclose_verification(target)
    assert report["status"] == "pass"
    joined = json.dumps(report)
    assert "threshold_cycle_calibration" not in joined
    assert "threshold_cycle_ev_2026" not in joined
