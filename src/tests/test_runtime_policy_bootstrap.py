import json
from pathlib import Path

from src.engine.automation import runtime_policy_bootstrap as bootstrap
from src.engine import runtime_approval_summary as summary_mod
from src.engine import verify_threshold_cycle_postclose_chain as verifier


def _write(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


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
    policy = {
            "report_type": "rising_missed_tp1_policy",
            "runtime_family": "rising_missed_tp1_selector",
            "effective_date": "2026-09-19",
            "allowed_runtime_apply": True,
            "runtime_effect": True,
            "runtime_env_overrides": {
                "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED": "true",
                "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE": "2026-09-19",
                "KORSTOCKSCAN_RISING_MISSED_TP1_POSITIVE_SUPPORT_MIN": "1",
            },
        }
    policy["policy_sha256"] = bootstrap._direct_policy_digest(policy)
    policy["runtime_env_overrides"][
        "KORSTOCKSCAN_RISING_MISSED_TP1_POLICY_SHA256"
    ] = policy["policy_sha256"]
    _write(receipt, policy)

    manifest = bootstrap.build_manifest("2026-09-19", receipt_paths=[receipt])

    assert manifest["env_overrides"]["KORSTOCKSCAN_RISING_MISSED_TP1_POSITIVE_SUPPORT_MIN"] == "1"
    assert manifest["env_key_owners"]["KORSTOCKSCAN_RISING_MISSED_TP1_POSITIVE_SUPPORT_MIN"] == "direct_policy:rising_missed_tp1_selector"
    assert manifest["direct_family_receipts"][0]["family"] == "rising_missed_tp1_selector"


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


def test_bootstrap_accepts_hash_bound_incumbent_preserved_receipt(monkeypatch, tmp_path):
    legacy_dir = tmp_path / "threshold_cycle" / "runtime_env"
    monkeypatch.setattr(bootstrap, "BOOTSTRAP_DIR", tmp_path / "bootstrap")
    monkeypatch.setattr(bootstrap, "LEGACY_RUNTIME_DIR", legacy_dir)
    monkeypatch.setattr(bootstrap, "OPERATOR_LOCK_DIR", tmp_path / "locks")
    _write(legacy_dir / "threshold_runtime_env_2026-09-18.json", {"target_date": "2026-09-18", "env_overrides": {"BASE": "1"}})
    _write(legacy_dir / "threshold_runtime_env_verify_2026-09-18.json", {"status": "pass"})
    receipt = tmp_path / "rising.json"
    policy = {
        "report_type": "rising_missed_tp1_policy",
        "runtime_family": "rising_missed_tp1_selector",
        "effective_date": "2026-09-19",
        "status": "incumbent_preserved",
        "allowed_runtime_apply": True,
        "runtime_effect": False,
        "runtime_env_overrides": {},
    }
    policy["policy_sha256"] = bootstrap._direct_policy_digest(policy)
    _write(receipt, policy)

    manifest = bootstrap.build_manifest("2026-09-19", receipt_paths=[receipt])

    assert len(manifest["direct_family_receipts"]) == 1
    assert manifest["direct_family_receipts"][0]["runtime_env_overrides"] == {}
    assert manifest["env_overrides"]["BASE"] == "1"


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
    _write(
        data_dir / "report" / "threshold_cycle_postclose_status" / f"threshold_cycle_postclose_{target}.status.json",
        {"target_date": target, "status": "succeeded"},
    )
    report = verifier.build_threshold_cycle_postclose_verification(target)
    assert report["status"] == "pass"
    joined = json.dumps(report)
    assert "threshold_cycle_calibration" not in joined
    assert "threshold_cycle_ev_2026" not in joined
