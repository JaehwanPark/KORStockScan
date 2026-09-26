import json
from pathlib import Path
import pytest

from src.engine.automation import runtime_policy_bootstrap as bootstrap
from src.engine import runtime_approval_summary as summary_mod
from src.engine import verify_threshold_cycle_postclose_chain as verifier
from src.engine.automation import scalp_trailing_mechanical_policy_apply as scalp_publisher


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


def test_bootstrap_rejects_missing_trailing_receipt_and_env_owner(monkeypatch, tmp_path):
    monkeypatch.setattr(bootstrap, "BOOTSTRAP_DIR", tmp_path / "bootstrap")
    monkeypatch.setattr(bootstrap, "LEGACY_RUNTIME_DIR", tmp_path / "legacy")
    monkeypatch.setattr(bootstrap, "OPERATOR_LOCK_DIR", tmp_path / "locks")
    _write(tmp_path / "legacy" / "threshold_runtime_env_2026-09-18.json", {
        "target_date": "2026-09-18", "env_overrides": {"BASE": "1"}
    })
    _write(tmp_path / "legacy" / "threshold_runtime_env_verify_2026-09-18.json", {
        "target_date": "2026-09-18", "status": "pass", "passed": True
    })
    manifest = bootstrap.write_bootstrap("2026-09-19")
    manifest.pop("scalp_trailing_mechanical_policy_receipt")
    manifest["manifest_sha256"] = bootstrap._digest_json({
        key: value for key, value in manifest.items() if key != "manifest_sha256"
    })
    _write(bootstrap.manifest_path("2026-09-19"), manifest)
    result = bootstrap.verify_bootstrap("2026-09-19", write=False)
    assert "scalp_trailing_mechanical_policy_receipt_missing" in result["findings"]

    manifest = bootstrap.write_bootstrap("2026-09-19")
    manifest["env_key_owners"].pop("KORSTOCKSCAN_SCALP_TRAILING_START_PCT")
    manifest["manifest_sha256"] = bootstrap._digest_json({
        key: value for key, value in manifest.items() if key != "manifest_sha256"
    })
    _write(bootstrap.manifest_path("2026-09-19"), manifest)
    result = bootstrap.verify_bootstrap("2026-09-19", write=False)
    assert "scalp_trailing_mechanical_env_or_owner_missing" in result["findings"]


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
    assert bootstrap.verify_bootstrap("2026-09-19", write=True)["passed"] is True
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


def test_mechanical_selection_binds_postclose_parent_and_33_market_keys(
    monkeypatch, tmp_path,
):
    from src.engine.scalping.trailing_mechanical_policy import (
        CLASSIFIER_VERSION, CONFIG_DEFAULTS, DEFAULTS, SELECTED_SCHEMA,
        START_MARKETS, classifier_hash,
        market_values_hash, selected_policy_env,
    )
    monkeypatch.setattr(bootstrap, "DATA_DIR", tmp_path)
    monkeypatch.setattr(bootstrap, "BOOTSTRAP_DIR", tmp_path / "bootstrap")
    monkeypatch.setattr(bootstrap, "LEGACY_RUNTIME_DIR", tmp_path / "threshold_cycle" / "runtime_env")
    monkeypatch.setattr(bootstrap, "OPERATOR_LOCK_DIR", tmp_path / "locks")
    legacy = bootstrap.LEGACY_RUNTIME_DIR
    _write(legacy / "threshold_runtime_env_2026-09-18.json",
           {"target_date": "2026-09-18", "env_overrides": {"BASE": "1"}})
    _write(legacy / "threshold_runtime_env_verify_2026-09-18.json", {"status": "pass"})
    parent = bootstrap.scalp_trailing_bootstrap_receipt({"BASE": "1"}, source="rollback_incumbent") [
        "market_values_sha256"
    ]
    vector = {market: dict(DEFAULTS) for market in START_MARKETS}
    classifier_values = {market: dict(CONFIG_DEFAULTS) for market in START_MARKETS}
    vector["REGULAR"]["SCALP_TRAILING_START_PCT"] = 0.5
    digest = market_values_hash(vector)
    report = {
        "date": "2026-09-18", "meta": {"snapshot_profile": "postclose_exit"},
        "completed_population_quality": {"complete": True},
        "mechanical_population_quality": {"complete": True},
        "trailing_mechanical_market_tuning": {
            "schema": "scalp_trailing_mechanical_market_tuning_v2",
            "population_complete": True,
            "holdout_days": ["2026-09-17", "2026-09-18"],
            "status": "research_candidate_holdout_positive_review_required",
            "joint_three_market": {digest: {
                "values": vector,
                "train": {"n": 30, "paired_ev_pct": 0.1,
                          "large_loss_worsened_ids": []},
                "holdout": {"n": 10, "paired_ev_pct": 0.1,
                            "large_loss_worsened_ids": [],
                            "execution_slippage_sensitivity": {
                                "100": {"paired_ev_pct": 0.01}}},
            }},
            "research_candidate": {
                "values": vector, "classifier_parameters": classifier_values,
                "market_values_sha256": digest,
                "decision_authority": "research_candidate_requires_policy_selection",
            },
                "joint_selection_evidence": {
                    "winner_sha256": digest, "tail_review_required": False,
                    "holdout_conservative_delta_krw": 100,
                    "holdout_conservative_worst_slippage_delta_krw": 10,
                    "holdout_worst_slippage_min_day_ev_pct": 0.01,
                },
        },
    }
    report_path = (tmp_path / "report" / "monitor_snapshots"
                   / "holding_exit_observation_2026-09-18.json")
    _write(report_path, report)
    manifest_path = (tmp_path / "report" / "monitor_snapshots" / "manifests"
                     / "monitor_snapshot_manifest_2026-09-18_postclose_exit.json")
    _write(manifest_path, {
        "profile": "postclose_exit", "target_date": "2026-09-18",
        "snapshot_paths": {"holding_exit_observation": str(report_path)},
        "snapshot_sha256": {"holding_exit_observation": bootstrap._digest_bytes(
            report_path.read_bytes())},
    })
    policy = {
        "schema": SELECTED_SCHEMA,
        "family": "scalp_trailing_mechanical_three_axis_selector",
        "source_date": "2026-09-18", "target_date": "2026-09-19",
        "source_report_sha256": bootstrap._digest_bytes(report_path.read_bytes()),
        "source_manifest_sha256": bootstrap._digest_bytes(manifest_path.read_bytes()),
        "allowed_runtime_apply": True, "runtime_effect": True,
        "apply_scope": "one_stage_canary", "market_values": vector,
        "changed_market": "REGULAR",
        "market_values_sha256": digest,
        "classifier_version": CLASSIFIER_VERSION,
        "classifier_sha256": classifier_hash(),
        "classifier_parameters": classifier_values,
        "rollback_market_values_sha256": parent,
        "selection_review": {
            "status": "reviewed_one_stage_canary", "candidate_sha256": digest,
            "source_quality": "pass", "execution_model": "pass",
            "same_stage_owner": "scalp_trailing_take_profit",
            "rollback_sha256": parent,
        },
    }
    policy["runtime_env_overrides"] = selected_policy_env(
        policy, report, target_date="2026-09-19",
        report_sha256=policy["source_report_sha256"],
    )
    assert len(policy["runtime_env_overrides"]) == 33
    policy_path = tmp_path / "selected.json"
    _write(policy_path, policy)
    manifest = bootstrap.build_manifest("2026-09-19", receipt_paths=[policy_path])
    assert manifest["direct_family_receipts"][0]["family"] == "scalp_trailing_mechanical_three_axis_selector"
    assert manifest["holding_path_vote_baseline_receipt"] == bootstrap.path_policy_baseline_receipt()
    assert manifest["scalp_trailing_mechanical_policy_receipt"]["market_values_sha256"] == digest
    assert manifest["scalp_trailing_mechanical_policy_receipt"]["schema"] == (
        "scalp_trailing_mechanical_selected_receipt_v2"
    )
    bootstrap.write_bootstrap("2026-09-19", receipt_paths=[policy_path])
    assert bootstrap.verify_bootstrap("2026-09-19", write=True)["passed"] is True
    valid_policy_bytes = policy_path.read_bytes()
    original_report_bytes = report_path.read_bytes()
    report["trailing_mechanical_market_tuning"]["joint_selection_evidence"][
        "holdout_conservative_delta_krw"
    ] = 0
    _write(report_path, report)
    verification = bootstrap.verify_bootstrap("2026-09-19", write=False)
    assert verification["passed"] is False
    assert any(finding.startswith("scalp_trailing_source_binding_invalid:")
               for finding in verification["findings"])
    report_path.write_bytes(original_report_bytes)
    policy["rollback_market_values_sha256"] = "f" * 64
    policy["selection_review"]["rollback_sha256"] = "f" * 64
    _write(policy_path, policy)
    with pytest.raises(ValueError, match="rollback_parent_hash_mismatch"):
        bootstrap.build_manifest("2026-09-19", receipt_paths=[policy_path])
    policy_path.write_bytes(valid_policy_bytes)
    carried = bootstrap.build_manifest("2026-09-25")
    assert carried["scalp_trailing_mechanical_policy_receipt"]["market_values_sha256"] == digest
    assert carried["env_overrides"]["KORSTOCKSCAN_SCALP_TRAILING_START_PCT_REGULAR"] == "0.5"
    assert carried["scalp_trailing_selection_lineage"]["status"] == "carried_selected"
    assert carried["scalp_trailing_selection_lineage"]["origin_target_date"] == "2026-09-19"


def test_mechanical_publisher_requires_sealed_postclose_report_and_one_market(
    monkeypatch, tmp_path,
):
    from src.engine.scalping.trailing_mechanical_policy import (
        CONFIG_DEFAULTS, DEFAULTS, START_MARKETS, baseline_receipt,
        market_values_hash,
    )
    report_dir = tmp_path / "monitor_snapshots"
    monkeypatch.setattr(scalp_publisher, "REPORT_DIR", report_dir)
    parent = baseline_receipt({}, source="rollback_incumbent")
    monkeypatch.setattr(scalp_publisher, "build_manifest", lambda _: {
        "scalp_trailing_mechanical_policy_receipt": parent,
    })
    values = {market: dict(DEFAULTS) for market in START_MARKETS}
    classifier_values = {market: dict(CONFIG_DEFAULTS) for market in START_MARKETS}
    classifier_values["REGULAR"]["strong_queue_min"] = 0.1
    digest = market_values_hash(values, classifier_values)
    report = {
        "date": "2026-09-25", "meta": {"snapshot_profile": "postclose_exit"},
        "completed_population_quality": {"complete": True},
        "mechanical_population_quality": {"complete": True},
        "trailing_mechanical_market_tuning": {
            "schema": "scalp_trailing_mechanical_market_tuning_v2",
            "population_complete": True,
            "holdout_days": ["2026-09-24", "2026-09-25"],
            "status": "research_candidate_holdout_positive_review_required",
            "classifier_policy_research": {
                "grid_sha256": "a" * 64,
                "research_candidate": {"market_values_sha256": digest},
                "candidates": {digest: {
                    "values": values,
                    "classifier_parameters": classifier_values,
                    "changed_train_ids": [str(i) for i in range(10)],
                    "changed_holdout_ids": [str(i) for i in range(5)],
                    "changed_train_symbol_count": 2,
                    "changed_holdout_symbol_count": 2,
                    "train": {"n": 30, "paired_ev_pct": 0.1,
                              "large_loss_worsened_ids": []},
                    "holdout": {"n": 10, "paired_ev_pct": 0.1,
                                "large_loss_worsened_ids": [],
                                "execution_slippage_sensitivity": {
                                    "100": {"paired_ev_pct": 0.01}}},
                }},
            },
            "research_candidate": {
                "values": values, "classifier_parameters": classifier_values,
                "market_values_sha256": digest,
                "decision_authority": "research_candidate_requires_policy_selection",
            },
            "joint_selection_evidence": {
                "winner_sha256": digest, "tail_review_required": False,
                "holdout_conservative_delta_krw": 100,
                "holdout_conservative_worst_slippage_delta_krw": 50,
                "holdout_worst_slippage_min_day_ev_pct": 0.01,
            },
        },
    }
    report_path = report_dir / "holding_exit_observation_2026-09-25.json"
    _write(report_path, report)
    trade_path = report_dir / "trade_review_2026-09-25.json"
    post_sell_path = report_dir / "post_sell_feedback_2026-09-25.json"
    _write(trade_path, {"date": "2026-09-25"})
    _write(post_sell_path, {"date": "2026-09-25"})
    manifest_path = (report_dir / "manifests"
                     / "monitor_snapshot_manifest_2026-09-25_postclose_exit.json")
    _write(manifest_path, {
        "target_date": "2026-09-25", "profile": "postclose_exit",
        "snapshot_kinds": ["trade_review", "post_sell_feedback", "holding_exit_observation"],
        "snapshot_paths": {
            "trade_review": str(trade_path),
            "post_sell_feedback": str(post_sell_path),
            "holding_exit_observation": str(report_path),
        },
        "snapshot_sha256": {
            "trade_review": bootstrap._digest_bytes(trade_path.read_bytes()),
            "post_sell_feedback": bootstrap._digest_bytes(post_sell_path.read_bytes()),
            "holding_exit_observation": bootstrap._digest_bytes(report_path.read_bytes()),
        },
    })
    selected = scalp_publisher.build_selection("2026-09-28")
    assert selected["allowed_runtime_apply"] is True
    assert selected["changed_market"] == "REGULAR"
    assert len(selected["runtime_env_overrides"]) == 33
    report["trailing_mechanical_market_tuning"]["classifier_policy_research"][
        "candidates"][digest]["train"]["n"] = 1
    _write(report_path, report)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["snapshot_sha256"]["holding_exit_observation"] = bootstrap._digest_bytes(
        report_path.read_bytes())
    _write(manifest_path, manifest)
    assert scalp_publisher.build_selection("2026-09-28")["status"] == (
        "hold_selection_contract"
    )
    report["trailing_mechanical_market_tuning"]["classifier_policy_research"][
        "candidates"][digest]["train"]["n"] = 30
    _write(report_path, report)
    manifest["snapshot_sha256"]["holding_exit_observation"] = bootstrap._digest_bytes(
        report_path.read_bytes())
    _write(manifest_path, manifest)
    post_sell_path.write_text("{}", encoding="utf-8")
    assert scalp_publisher.build_selection("2026-09-28")["status"] == "hold_source_gap"
    _write(post_sell_path, {"date": "2026-09-25"})
    report_path.write_text("{}", encoding="utf-8")
    held = scalp_publisher.build_selection("2026-09-28")
    assert held["status"] == "hold_source_gap"
    assert held["allowed_runtime_apply"] is False
