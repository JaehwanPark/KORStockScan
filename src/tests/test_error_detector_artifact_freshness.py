from __future__ import annotations

import hashlib
import pytest

import os
import time
import json
from types import SimpleNamespace
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch

from src.engine.error_detectors.artifact_freshness import (
    ArtifactFreshnessDetector,
    ARTIFACT_REGISTRY,
    _reconcile_update_kospi_master_difference,
    _machine_result_semantics,
    _auxiliary_result_semantics,
    _holding_profit_exit_semantics,
    _initial_quantity_semantics,
)
from src.engine.scalping.micro_reversion.symbol_master import SymbolLookupStatus

_TRADING_MOCK = "src.engine.error_detectors.artifact_freshness.is_krx_trading_day"


def _quantity_semantic_fixture(tmp_path, monkeypatch, *, shape="two_leg_0_1tick",
                               complete_stage=False):
    from src.engine.scalping import initial_quantity_activation as activation
    from src.engine.scalping import initial_quantity_policy as producer

    current = tmp_path / "data/runtime/initial_quantity/current.json"
    current.parent.mkdir(parents=True)
    current.write_text(json.dumps({"effective_from": "2026-09-24"}))
    policy = current.with_name("policy.json")
    policy.write_text(json.dumps({"policy_content_sha256": "c" * 64,
        "type_policies": {
        "KRX_PARENT": {"selected_shape": shape,
                       "timeout_mode": "selected_total_wait_sec",
                       "selected_total_wait_sec": 60}}}))
    monkeypatch.setattr(activation, "selected_initial_quantity_env",
                        lambda *_: {activation.ENV_FILE: str(policy),
                                    activation.ENV_SHA: "a" * 64})
    if complete_stage:
        monkeypatch.setattr(producer, "refresh_quantity_stage_terminal_valid",
                            lambda _: True)
        stage = (tmp_path / "data/report/initial_entry_quantity_type_policy" /
                 "refresh_postclose_2026-09-28" /
                 "initial_quantity_refresh_stage_2026-09-28.json")
        stage.parent.mkdir(parents=True)
        stage.write_text(json.dumps({"all_completed_initial_trades": 0,
                                     "decision": "carry_parent"}))
    return current


def test_initial_quantity_semantics_separates_missing_policy_and_valid_empty(
        tmp_path, monkeypatch):
    assert _initial_quantity_semantics(tmp_path, "2026-09-23")["status"] == (
        "not_required_before_introduction")
    assert _initial_quantity_semantics(tmp_path, "2026-09-28")["status"] == (
        "source_invalid")
    _quantity_semantic_fixture(tmp_path, monkeypatch)
    from src.engine.scalping import initial_quantity_policy as producer
    monkeypatch.setattr(producer, "refresh_quantity_stage_terminal_valid",
                        lambda _: True)
    stage = (tmp_path / "data/report/initial_entry_quantity_type_policy" /
             "refresh_postclose_2026-09-28" /
             "initial_quantity_refresh_stage_2026-09-28.json")
    stage.parent.mkdir(parents=True)
    stage.write_text(json.dumps({"all_completed_initial_trades": 0,
                                 "decision": "carry_parent"}))
    result = _initial_quantity_semantics(tmp_path, "2026-09-28")
    assert result["status"] == "valid_empty"
    assert result["postclose_stage_status"] == "valid_empty"
    assert result["runtime_pid_status"] == "not_observed"
    monkeypatch.setattr(producer, "refresh_quantity_stage_terminal_valid",
                        lambda _: False)
    invalid = _initial_quantity_semantics(tmp_path, "2026-09-28")
    assert invalid["status"] == "source_invalid"
    assert invalid["postclose_stage_status"] == "source_invalid"


def test_initial_quantity_semantics_checks_bundle_quantity_shape_and_deadline(
        tmp_path, monkeypatch):
    from src.engine.scalping.initial_quantity_bundle_state import (
        bundle_state_path, new_bundle_state,
    )
    from src.engine.scalping.initial_quantity_timeout import build_bundle_timeout_schedule

    _quantity_semantic_fixture(tmp_path, monkeypatch, complete_stage=True)
    schedule = build_bundle_timeout_schedule(
        quantity_type="KRX_PARENT", policy_sha256="a" * 64,
        decision_at="2026-09-28T09:29:50+09:00",
        order_start_at="2026-09-28T09:30:00+09:00",
        total_wait_sec=60, leg_count=2, cancel_confirm_reserve_sec=5)
    bundle = new_bundle_state(
        attempt_id="monitor-attempt", code="005930", target_id="123",
        schedule=schedule, requested_qty=3,
        planned_legs=[{"leg_index": index, "qty": qty, "price": 0,
                       "route": "KRX", "tag": f"initial_quantity_leg_{index}"}
                      for index, qty in enumerate((2, 1))])
    directory = tmp_path / "data/runtime/initial_quantity/bundles"
    directory.mkdir()
    path = bundle_state_path(directory, bundle["attempt_id"])
    path.write_text(json.dumps(bundle))
    before = _initial_quantity_semantics(
        tmp_path, "2026-09-28",
        now_epoch=schedule["bundle_deadline_epoch"] - 1)
    assert before["status"] == "pending_terminal"
    assert before["findings"] == []
    after = _initial_quantity_semantics(
        tmp_path, "2026-09-28",
        now_epoch=schedule["bundle_deadline_epoch"] + 1)
    assert after["findings"] == ["initial_quantity_bundle_terminal_overdue"]
    policy_path = tmp_path / "data/runtime/initial_quantity/policy.json"
    selected = json.loads(policy_path.read_text())
    selected["type_policies"]["KRX_PARENT"]["selected_total_wait_sec"] = 30
    policy_path.write_text(json.dumps(selected))
    mismatch = _initial_quantity_semantics(
        tmp_path, "2026-09-28",
        now_epoch=schedule["bundle_deadline_epoch"] - 1)
    assert mismatch["findings"] == ["initial_quantity_bundle_policy_mismatch"]
    selected["type_policies"]["KRX_PARENT"]["selected_total_wait_sec"] = 60
    policy_path.write_text(json.dumps(selected))
    bad = dict(bundle, requested_qty=4)
    path.write_text(json.dumps(bad))
    assert _initial_quantity_semantics(
        tmp_path, "2026-09-28")["status"] == "source_invalid"


def test_initial_quantity_semantics_rejects_missing_and_corrupt_pid_archive(
        tmp_path, monkeypatch):
    _quantity_semantic_fixture(tmp_path, monkeypatch, complete_stage=True)
    verify_path = (tmp_path / "data/runtime/policy_bootstrap" /
                   "runtime_policy_bootstrap_verify_2026-09-28.json")
    verify_path.parent.mkdir(parents=True)
    verify_path.write_text(json.dumps({"target_date": "2026-09-28",
                                       "pid_passed": True}))
    missing = _initial_quantity_semantics(tmp_path, "2026-09-28")
    assert missing["runtime_pid_status"] == "not_observed"
    assert missing["findings"] == ["initial_quantity_pid_archive_missing"]

    body = {"schema_version": "initial_quantity_pid_verification_v1",
            "target_date": "2026-09-28", "pid": 123,
            "policy_file_sha256": "a" * 64,
            "policy_content_sha256": "c" * 64,
            "policy_file": str(tmp_path / "data/runtime/initial_quantity/policy.json"),
            "manifest_sha256": "b" * 64,
            "verification": {"target_date": "2026-09-28", "pid": 123,
                             "manifest_sha256": "b" * 64,
                             "status": "pass", "passed": True,
                             "pid_passed": True, "pid_env_available": True,
                             "findings": [], "pid_mismatches": []}}
    digest = hashlib.sha256(json.dumps(body, ensure_ascii=True,
        allow_nan=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    archive = (tmp_path / "data/runtime/policy_bootstrap" /
               "verified_initial_quantity_pid/2026-09-28" /
               f"initial_quantity_pid_123_{digest[:12]}.json")
    archive.parent.mkdir(parents=True)
    archive.write_text(json.dumps({**body, "receipt_content_sha256": digest}))
    verified = _initial_quantity_semantics(tmp_path, "2026-09-28")
    assert verified["runtime_pid_status"] == "verified_receipt"
    assert verified["findings"] == []
    archive.write_text(json.dumps({**body, "policy_file_sha256": "c" * 64,
                                   "receipt_content_sha256": digest}))
    corrupt = _initial_quantity_semantics(tmp_path, "2026-09-28")
    assert corrupt["status"] == "source_invalid"
    assert "initial_quantity_pid_receipt_invalid" in corrupt["findings"]


def test_initial_quantity_semantics_uses_applied_ancestor_after_postclose_cas(
        tmp_path, monkeypatch):
    from src.engine.scalping import initial_quantity_activation as activation

    current = _quantity_semantic_fixture(tmp_path, monkeypatch, complete_stage=True)
    parent = current.with_name("parent.json")
    current.rename(parent)
    current.write_text(json.dumps({"effective_from": "2026-09-29",
                                   "parent_current_file": str(parent)}))
    seen = []

    def selected(path, target):
        seen.append((path.name, target))
        return {activation.ENV_FILE: str(path.with_name("policy.json")),
                activation.ENV_SHA: "a" * 64}

    monkeypatch.setattr(activation, "selected_initial_quantity_env", selected)
    assert _initial_quantity_semantics(tmp_path, "2026-09-28")["status"] == (
        "valid_empty")
    assert seen == [("current.json", "2026-09-29"),
                    ("parent.json", "2026-09-24"),
                    ("parent.json", "2026-09-28")]


def test_initial_quantity_semantics_marks_missing_past_date_stage(
        tmp_path, monkeypatch):
    import src.engine.error_detectors.artifact_freshness as mod

    _quantity_semantic_fixture(tmp_path, monkeypatch)

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 9, 29, 7, 0, tzinfo=tz)

    monkeypatch.setattr(mod, "datetime", Clock)
    result = _initial_quantity_semantics(tmp_path, "2026-09-28")
    assert result["status"] == "source_gap"
    assert result["postclose_stage_status"] == "source_gap"
    assert result["findings"] == ["initial_quantity_stage_missing_after_date"]


def test_initial_quantity_semantics_attributes_corrupt_journal_to_its_date(
        tmp_path, monkeypatch):
    _quantity_semantic_fixture(tmp_path, monkeypatch, complete_stage=True)
    directory = tmp_path / "data/runtime/initial_quantity/bundles"
    directory.mkdir()
    path = directory / ("d" * 64 + ".json")
    path.write_text("{broken")
    prior = datetime(2026, 9, 27, 10, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    os.utime(path, (prior.timestamp(), prior.timestamp()))
    assert _initial_quantity_semantics(tmp_path, "2026-09-28")["findings"] == []
    current = datetime(2026, 9, 28, 10, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    os.utime(path, (current.timestamp(), current.timestamp()))
    assert _initial_quantity_semantics(tmp_path, "2026-09-28")["findings"] == [
        "initial_quantity_bundle_invalid"]


def test_artifact_detector_surfaces_initial_quantity_semantic_findings(
        tmp_path, monkeypatch):
    import src.engine.error_detectors.artifact_freshness as mod

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 9, 28, 21, 30)

    monkeypatch.setattr(mod, "datetime", Clock)
    monkeypatch.setattr(mod, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(mod, "ARTIFACT_REGISTRY", [])
    monkeypatch.setattr(mod, "is_krx_trading_day", lambda *_: True)
    monkeypatch.setattr(mod, "load_installed_crontab", lambda: "")
    for name in ("_holding_profit_exit_semantics", "_machine_result_semantics",
                 "_auxiliary_result_semantics"):
        monkeypatch.setattr(mod, name, lambda *_: {"status": "not_assessed",
                                                  "findings": []})
    monkeypatch.setattr(mod, "_initial_quantity_semantics", lambda *_, **__: {
        "status": "pending_terminal",
        "findings": ["initial_quantity_bundle_terminal_overdue"]})
    result = mod.ArtifactFreshnessDetector(dry_run=True).check()
    assert result.details["initial_quantity_semantics"]["status"] == (
        "pending_terminal")
    assert result.severity == "warning"


def test_holding_profit_semantics_does_not_retroactively_reject_old_report(tmp_path):
    path = tmp_path / "data/report/holding_exit_sentinel/holding_exit_sentinel_2026-09-23.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"target_date":"2026-09-23"}')
    assert _holding_profit_exit_semantics(tmp_path, "2026-09-23")["status"] == (
        "not_required_before_introduction")
    assert _holding_profit_exit_semantics(tmp_path, "2026-09-28")["status"] == "not_assessed"
    current_md = path.with_name("holding_exit_sentinel_2026-09-28.md")
    current_md.write_text("# observed\n")
    assert _holding_profit_exit_semantics(tmp_path, "2026-09-28")["findings"] == [
        "holding_semantic_json_missing_with_markdown_report"]


def test_machine_semantics_requires_full_report_when_sidecar_exists(tmp_path):
    folder = tmp_path / "data/report/ai_decision_action_outcome_calibration"
    folder.mkdir(parents=True)
    (folder / "winrate_policy_2026-09-28.json").write_text("{}")
    assert _machine_result_semantics(tmp_path, "2026-09-28")["findings"] == [
        "machine_full_report_missing_with_winrate_sidecar"]


def test_machine_result_semantics_detects_successful_stage_with_unbound_economics(tmp_path, monkeypatch):
    day = "2026-09-23"
    root = tmp_path / "data/report"
    report_path = root / "ai_decision_action_outcome_calibration" / f"ai_decision_action_outcome_calibration_{day}.json"
    report_path.parent.mkdir(parents=True)
    report = {"target_date": day, "machine_full_evaluation": {"scope_evaluations": {
        "KRX|KRX_REGULAR": {"full_population_count": 10,
            "current_structure_eligible_count": 4, "paired_comparable_count": 0,
            "downstream_operating_evidence_complete": False,
            "row_exclusion_reason_counts": {"source_contract_invalid": 3}},
    }}}
    report["artifact_content_sha256"] = hashlib.sha256(json.dumps(report,
        ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    report_path.write_text(json.dumps(report), encoding="utf-8")
    compact_path = root / "ai_entry_setup_paired_replay_batch" / f"compact_auxiliary_paired_economic_{day}.source.json"
    compact_path.parent.mkdir(parents=True)
    compact = {"target_date": day, "rows": [
        {"exclusion_reason": "terminal_path_not_evaluable"},
        {"exclusion_reason": "exact_stop_distance_missing_or_invalid"},
    ]}
    compact["artifact_content_sha256"] = hashlib.sha256(json.dumps(compact,
        ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    compact_path.write_text(json.dumps(compact), encoding="utf-8")
    result = _machine_result_semantics(tmp_path, day)
    assert result["status"] == "warning"
    assert result["findings"] == ["compact_operating_rows_all_excluded",
        "machine_operating_economics_incomplete", "machine_operating_paired_unbound",
        "machine_source_contract_exclusions"]
    assert result["compact_exclusions"] == {"terminal_path_not_evaluable": 1,
        "exact_stop_distance_missing_or_invalid": 1}
    import src.engine.error_detectors.artifact_freshness as detector_module
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 9, 24, 12, 0)
    monkeypatch.setattr(detector_module, "datetime", Clock)
    monkeypatch.setattr(detector_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(detector_module, "ARTIFACT_REGISTRY", [])
    monkeypatch.setattr(detector_module, "load_installed_crontab", lambda: "")
    monkeypatch.setattr(detector_module, "is_krx_trading_day", lambda _: True)
    detector = ArtifactFreshnessDetector(dry_run=True)
    detector.postclose_source_date = day
    detection = detector.check()
    assert detection.severity == "warning"
    assert detection.details["machine_result_semantics"]["findings"] == result["findings"]
    report["machine_full_evaluation"]["scope_evaluations"]["KRX|KRX_REGULAR"].update(
        paired_comparable_count=4, downstream_operating_evidence_complete=True,
        row_exclusion_reason_counts={})
    report["artifact_content_sha256"] = hashlib.sha256(json.dumps({
        k: v for k, v in report.items() if k != "artifact_content_sha256"},
        ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    report_path.write_text(json.dumps(report), encoding="utf-8")
    compact_path.unlink()
    assert _machine_result_semantics(tmp_path, day)["status"] == "pass"
    assert detector.check().severity == "pass"
    compact_path.with_suffix(".json.gz").write_bytes(b"not-gzip")
    assert _machine_result_semantics(tmp_path, day)["findings"] == ["compact_projection_invalid"]
    compact_path.with_suffix(".json.gz").unlink()
    report_path.write_bytes(b"\xff")
    assert _machine_result_semantics(tmp_path, day)["status"] == "source_invalid"
    report_path.unlink()
    report_path.symlink_to("missing-report.json")
    assert _machine_result_semantics(tmp_path, day)["findings"] == [
        "machine_report_untrusted_path_or_size"]


def test_machine_result_semantics_rejects_unknown_winrate_sidecar_schema(tmp_path, monkeypatch):
    day = '2026-09-23'
    directory = tmp_path / 'data/report/ai_decision_action_outcome_calibration'
    directory.mkdir(parents=True)
    full = {'target_date': day, 'machine_full_evaluation': {'scope_evaluations': {}}}
    full['artifact_content_sha256'] = hashlib.sha256(json.dumps(full,
        ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    (directory / f'ai_decision_action_outcome_calibration_{day}.json').write_text(json.dumps(full))
    (directory / f'winrate_policy_{day}.json').write_text(json.dumps({'schema': 'unknown'}))

    result = _machine_result_semantics(tmp_path, day)

    assert result['findings'] == ['winrate_report_schema_invalid']
    from src.engine.scalping import ai_action_outcome_calibration as calibration
    from src.engine.scalping import mechanistic_entry_runtime_policy as runtime_policy
    zero = dict(input_attempt_count=0, accepted_attempt_count=0,
        source_contract_excluded_count=0, source_contract_exclusion_reasons={},
        excluded_attempt_counts={}, gross_label_difference_count=0)
    report = calibration._with_artifact_content_sha256(dict(
        schema='main_entry_winrate_policy_report_v1', target_date=day,
        selection_basis='win_rate_only', disposition='successor_selected',
        situation_attempt_counts={}, **zero,
        market_census={'KRX|KRX_REGULAR': dict(market='REGULAR', **zero),
            'PREMARKET_KRX_LIKE|PREMARKET_KRX_LIKE': dict(market='PREMARKET', **zero),
            'KRX_NXT_INTEGRATED|KRX_NXT_AFTERMARKET': dict(market='AFTERMARKET', **zero)}))
    (directory / f'winrate_policy_{day}.json').write_text(json.dumps(report))
    terminal = calibration._with_artifact_content_sha256(dict(
        report_sha256=report['artifact_content_sha256'],
        staged={'target_date': '2026-09-28'}))
    (directory / f'winrate_policy_terminal_{day}.json').write_text(json.dumps(terminal))
    machine = {'policy': 'candidate'}
    monkeypatch.setattr(runtime_policy, 'load', lambda **_: dict(
        machine_policy=machine,
        winrate_selection=dict(report_sha256=report['artifact_content_sha256'],
            disposition='successor_selected', machine_policy_sha256=runtime_policy.digest(machine)),
        scope_policies={'KRX|KRX_REGULAR': {'machine_disposition': 'successor_selected'}}))
    assert 'winrate_successor_hurdle_invalid' in _machine_result_semantics(tmp_path, day)['findings']


def test_auxiliary_semantics_separates_source_gap_from_invalid_selection(tmp_path):
    from src.engine.scalping import compact_auxiliary_paired_replay as paired
    day = "2026-09-26"
    path = (tmp_path / "data/report/ai_entry_setup_paired_replay_batch"
            / f"compact_auxiliary_paired_economic_{day}.json")
    path.parent.mkdir(parents=True)
    scope = {"status": "incumbent_carry", "eligible_count": 2,
             "holdout_day": None, "selected": {}}
    stage = paired.sealed({"schema": "auxiliary_ai_stage_evaluation_v1",
        "source_date": day, "source_projection_sha256": "a" * 64,
        "source_manifest_sha256": "b" * 64, "source_tuning_allowed": True,
        "screened_total": 3, "eligible_count": 2, "excluded_count": 1,
        "eligible_keys": ["one", "two"], "scope_results": {"KRX|KRX_REGULAR": scope},
        "runtime_effect": False, "actual_order_submitted": False})

    def write(current):
        report = paired.sealed({"schema": paired.SCHEMA, "target_date": day,
            "source_projection_sha256": "a" * 64,
            "source_manifest_sha256": "b" * 64,
            "runtime_effect": False, "auxiliary_stage": current})
        path.write_text(json.dumps(report))

    write(stage)
    result = _auxiliary_result_semantics(tmp_path, day)
    assert result["status"] == "source_gap"
    assert result["findings"] == ["auxiliary_independent_holdout_missing"]
    assert result["runtime_effect"] is False

    scope["status"] = "candidate_selected"
    scope["selected"] = {"train_count": 1, "holdout_count": 0,
        "train_paired_delta_ev_pct": 0.2, "holdout_paired_delta_ev_pct": 0.1,
        "successful_pass_changed_count": 0, "prompt_response_missing_count": 0}
    stage = paired.sealed({k: v for k, v in stage.items()
                           if k != "artifact_content_sha256"} | {"scope_results": {"KRX|KRX_REGULAR": scope}})
    write(stage)
    result = _auxiliary_result_semantics(tmp_path, day)
    assert result["status"] == "review_required"
    assert "auxiliary_selected_without_independent_evidence" in result["findings"]

    scope["holdout_day"] = "2026-09-25"
    scope["eligible_count"] = 8
    scope["selected"].update(train_count=5, holdout_count=3,
        paired_delta_ev_pct=0.15, policy={"schema": "auxiliary_soft_policy_v1"},
        policy_sha256=paired.digest({"schema": "auxiliary_soft_policy_v1"}),
        prompt_version="entry_machine_auxiliary_compact_v3",
        train_positive_count=1, train_negative_count=1,
        holdout_positive_count=1, holdout_negative_count=1,
        train_pass_count=1, holdout_pass_count=1,
        train_changed_count=2, holdout_changed_count=1)
    stage = paired.sealed({k: v for k, v in stage.items()
                           if k != "artifact_content_sha256"} | {
                               "screened_total": 9, "eligible_count": 8,
                               "eligible_keys": [f"key-{i}" for i in range(8)],
                               "candidate_population_keys": [f"key-{i}" for i in range(8)],
                               "scope_results": {"KRX|KRX_REGULAR": scope}})
    write(stage)
    result = _auxiliary_result_semantics(tmp_path, day)
    assert result["status"] == "candidate_selected"
    assert result["scopes"]["KRX|KRX_REGULAR"]["actual_fill_or_realized_pnl"] is False

    broken = paired.sealed({k: v for k, v in stage.items()
                            if k != "artifact_content_sha256"} | {
                                "candidate_population_keys": ["key-0"]})
    write(broken)
    assert _auxiliary_result_semantics(tmp_path, day)["findings"] == [
        "auxiliary_candidate_population_invalid"]
    write(stage)

    report = json.loads(path.read_text())
    report["auxiliary_stage"]["eligible_count"] = 3
    path.write_text(json.dumps(paired.sealed(report)))
    assert _auxiliary_result_semantics(tmp_path, day)["findings"] == [
        "auxiliary_stage_report_contract_invalid"]


def test_auxiliary_completed_terminal_requires_exact_report_generation(tmp_path):
    day = "2026-09-26"
    path = (tmp_path / "data/report/ai_entry_setup_paired_replay_batch"
            / f"compact_auxiliary_paired_economic_{day}.json")
    terminal_path = (tmp_path / "data/report/postclose_stage_terminal" / day
                     / "main_auxiliary_policy.json")
    terminal_path.parent.mkdir(parents=True)
    terminal = {"schema": "postclose_stage_terminal_v2",
                "stage_id": "main_auxiliary_policy", "source_date": day,
                "status": "succeeded", "exit_code": 0,
                "sources": {"compact_auxiliary_paired_economic": {
                    "path": str(path.resolve()), "sha256": "a" * 64}}}
    terminal["receipt_sha256"] = hashlib.sha256(json.dumps(terminal,
        ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    terminal_path.write_text(json.dumps(terminal))
    assert _auxiliary_result_semantics(tmp_path, day)["findings"] == [
        "auxiliary_completed_report_missing"]
    path.parent.mkdir(parents=True)
    path.write_text("{}")
    assert _auxiliary_result_semantics(tmp_path, day)["findings"] == [
        "auxiliary_completed_report_generation_mismatch"]


def test_auxiliary_semantics_checks_bound_labels_and_primary_economics(tmp_path):
    from src.engine.scalping import compact_auxiliary_paired_replay as paired
    day = "2026-09-30"
    label_path = (tmp_path / "data/report/ai_decision_outcome_labels"
                  / f"ai_decision_outcome_labels_{day}.json")
    label_path.parent.mkdir(parents=True)
    labels = {"schema": "ai_decision_outcome_labels_v1", "target_date": day,
              "labels": [{"decision_stage": "entry_screen",
                          "evaluation_label_contract": {"diagnostic_price_path": {"status": "source_gap"}}}],
              "label_contract_status_counts": {"source_gap": 1}}
    label_path.write_text(json.dumps(labels))
    report_path = (tmp_path / "data/report/ai_entry_setup_paired_replay_batch"
                   / f"compact_auxiliary_paired_economic_{day}.json")
    report_path.parent.mkdir(parents=True)
    stage = paired.sealed({"schema": "auxiliary_ai_stage_evaluation_v1",
        "source_date": day, "source_projection_sha256": "a" * 64,
        "source_manifest_sha256": "b" * 64, "source_tuning_allowed": True,
        "screened_total": 1, "eligible_count": 0, "excluded_count": 1,
        "eligible_keys": [], "scope_results": {},
        "runtime_effect": False, "actual_order_submitted": False})
    report = paired.sealed({"schema": paired.SCHEMA, "target_date": day,
        "source_projection_sha256": "a" * 64, "source_manifest_sha256": "b" * 64,
        "runtime_effect": False, "auxiliary_stage": stage,
        "source_label_report_sha256": paired.digest(labels),
        "status": "source_contract_blocked",
        "metrics": {"screened_total": 1, "paired_comparable_count": 0,
                    "source_excluded_count": 1},
        "prospective_source_contract": {"first_source_gap": "writer_plan_hash_missing",
            "source_lineage_counts": {"prompt_exact_input_present": 1,
                                      "writer_trace_plan_joined": 0}}})
    report_path.write_text(json.dumps(report))
    result = _auxiliary_result_semantics(tmp_path, day)
    assert result["status"] == "source_gap"
    assert set(result["findings"]) == {
        "auxiliary_economic_population_empty", "auxiliary_primary_economics_source_blocked",
        "auxiliary_exact_plan_lineage_missing", "auxiliary_outcome_label_source_gap"}
    labels["labels"][0]["decision_stage"] = "holding"
    label_path.write_text(json.dumps(labels))
    assert _auxiliary_result_semantics(tmp_path, day) == {
        "status": "source_invalid", "findings": ["auxiliary_label_report_binding_invalid"]}
    labels["labels"][0]["evaluation_label_contract"]["diagnostic_price_path"]["status"] = "available"
    labels["label_contract_status_counts"] = {"available": 1}
    label_path.write_text(json.dumps(labels))
    report["source_label_report_sha256"] = paired.digest(labels)
    report["status"] = "incumbent_carried"
    report["metrics"]["paired_comparable_count"] = 1
    report["metrics"]["source_excluded_count"] = 0
    report["prospective_source_contract"]["first_source_gap"] = None
    report_path.write_text(json.dumps(paired.sealed(report)))
    recovered = _auxiliary_result_semantics(tmp_path, day)
    assert recovered["findings"] == ["auxiliary_economic_population_empty"]
    assert recovered["outcome_label_source_gap_count"] == 0
    report.pop("source_label_report_sha256")
    report_path.write_text(json.dumps(paired.sealed(report)))
    assert "auxiliary_outcome_label_binding_missing" in (
        _auxiliary_result_semantics(tmp_path, day)["findings"])


def _update_kospi_partial_payload() -> dict:
    return {
        "target_date": "2026-09-15",
        "status": "completed_with_warnings",
        "failed_steps": [],
        "warning_steps": ["update_kospi_data"],
        "steps": [
            {
                "name": "update_kospi_data",
                "status": "completed_with_warnings",
                "details": {
                    "reason": "market_eligibility_partial",
                    "eligibility": {
                        "complete": True,
                        "status": "partial",
                        "requested_code_count": 4,
                        "received_code_count": 2,
                        "missing_codes": ["000010", "000090"],
                        "market_source_meta": [
                            {"market": "0", "complete": True},
                            {"market": "10", "complete": True},
                        ],
                    },
                },
            }
        ],
    }


def test_update_kospi_warning_reconciles_verified_non_active_master_difference(
    tmp_path: Path,
) -> None:
    master_path = (
        tmp_path
        / "data/report/micro_reversion_economic_reference"
        / "micro_reversion_symbol_master_2026-09-15.json"
    )
    master_path.parent.mkdir(parents=True)
    master_path.write_text("{}\n", encoding="utf-8")
    status_path = tmp_path / "update_kospi_status.json"
    status_path.write_text(
        json.dumps(_update_kospi_partial_payload()), encoding="utf-8"
    )
    fake_master = SimpleNamespace(
        lookup=lambda code, *, as_of: SimpleNamespace(status=SymbolLookupStatus.MISSING)
    )
    details: dict = {}
    module = "src.engine.error_detectors.artifact_freshness"

    with (
        patch(f"{module}.PROJECT_ROOT", tmp_path),
        patch(
            "src.engine.scalping.micro_reversion.symbol_master."
            "VerifiedSymbolMaster.from_json_path",
            return_value=fake_master,
        ) as loader,
    ):
        assert (
            ArtifactFreshnessDetector._validate_json_status(
                {
                    "id": "update_kospi_status",
                    "json_status_field": "status",
                    "json_ok_values": ["completed", "skipped_non_trading_day"],
                },
                status_path,
                details,
            )
            == ""
        )

    loader.assert_called_once_with(master_path, require_canonical_owner=True)
    assert (
        details["update_kospi_status_warning_reconciliation"]
        == "benign_master_difference"
    )
    assert details["update_kospi_status_master_difference_count"] == 2
    assert details["update_kospi_status_master_difference_unresolved"] == {}


def test_update_kospi_warning_keeps_active_or_conflicting_code_visible(
    tmp_path: Path,
) -> None:
    master_path = (
        tmp_path
        / "data/report/micro_reversion_economic_reference"
        / "micro_reversion_symbol_master_2026-09-15.json"
    )
    master_path.parent.mkdir(parents=True)
    master_path.write_text("{}\n", encoding="utf-8")
    fake_master = SimpleNamespace(
        lookup=lambda code, *, as_of: SimpleNamespace(
            status=(
                SymbolLookupStatus.VERIFIED
                if code == "000010"
                else SymbolLookupStatus.MISSING
            )
        )
    )
    details: dict = {}
    module = "src.engine.error_detectors.artifact_freshness"

    with (
        patch(f"{module}.PROJECT_ROOT", tmp_path),
        patch(
            "src.engine.scalping.micro_reversion.symbol_master."
            "VerifiedSymbolMaster.from_json_path",
            return_value=fake_master,
        ),
    ):
        assert not _reconcile_update_kospi_master_difference(
            _update_kospi_partial_payload(), details
        )

    assert details["update_kospi_status_master_difference_unresolved"] == {
        "000010": "verified"
    }


@pytest.mark.parametrize(
    "case,expected",
    [("running", "warning"), ("after_old_window", "warning")]
    + [
        (case, "fail")
        for case in (
            "failed",
            "wrong_date",
            "missing_date",
            "invalid_json",
            "missing_status",
            "nonzero_exit",
            "boolean_exit",
            "missing_start",
            "future_start",
            "old_start",
            "invalid_start",
            "wrong_schema",
            "boolean_schema",
            "runtime_authority",
            "terminal_fail",
            "terminal_done",
            "no_start_marker",
            "no_live_pid",
            "deadline",
            "past_source",
        )
    ],
)
def test_postclose_running_status_requires_bounded_exact_live_owner(
    tmp_path, case, expected
):
    module = "src.engine.error_detectors.artifact_freshness"
    now = datetime(2026, 9, 10, 21, 40, 2)
    if case == "after_old_window":
        now = datetime(2026, 9, 10, 22, 30)
    elif case == "deadline":
        now = datetime(2026, 9, 10, 23, 20)
    elif case == "past_source":
        now = datetime(2026, 9, 11, 0, 5)
    payload = {
        "schema_version": 1,
        "report_type": "threshold_cycle_postclose_status",
        "target_date": "2026-09-10",
        "status": "running",
        "reason": "started",
        "exit_code": 0,
        "runtime_effect": False,
        "started_at": "2026-09-10T20:10:04+09:00",
    }
    changes = {
        "failed": {"status": "failed"},
        "wrong_date": {"target_date": "2026-09-09"},
        "missing_date": {"target_date": None},
        "missing_status": {"status": None},
        "nonzero_exit": {"exit_code": 1},
        "boolean_exit": {"exit_code": False},
        "missing_start": {"started_at": None},
        "future_start": {"started_at": "2026-09-10T23:00:00+09:00"},
        "old_start": {"started_at": "2026-09-09T20:10:04+09:00"},
        "invalid_start": {"started_at": "invalid"},
        "wrong_schema": {"schema_version": 99},
        "boolean_schema": {"schema_version": True},
        "runtime_authority": {"runtime_effect": True},
    }
    payload.update(changes.get(case, {}))
    status_path = tmp_path / "status.json"
    status_path.write_text("{" if case == "invalid_json" else json.dumps(payload))
    log_path = tmp_path / "postclose.log"
    marker = "[START] threshold-cycle postclose target_date=2026-09-10\n"
    if case == "no_start_marker":
        marker = "[START] threshold-cycle postclose target_date=2026-09-09\n"
    elif case.startswith("terminal_"):
        terminal = "FAIL" if case == "terminal_fail" else "DONE"
        marker += f"[{terminal}] threshold-cycle postclose target_date=2026-09-10\n"
    log_path.write_text(marker)
    artifact = dict(
        next(a for a in ARTIFACT_REGISTRY if a["id"] == "threshold_postclose_status")
    )
    artifact["path_template"] = str(status_path)
    artifact["suppress_missing_while_cron_in_progress"] = {"log": str(log_path)}
    with (
        patch(_TRADING_MOCK, return_value=True),
        patch(f"{module}.ARTIFACT_REGISTRY", [artifact]),
        patch(f"{module}.datetime", wraps=datetime) as clock,
        patch(f"{module}.time.time", return_value=now.timestamp()),
        patch.object(
            ArtifactFreshnessDetector,
            "_has_matching_live_process",
            return_value=case != "no_live_pid",
        ),
    ):
        clock.now.return_value = now
        detector = ArtifactFreshnessDetector()
        if case == "past_source":
            detector.postclose_source_date = "2026-09-10"
        result = detector.check()
    assert result.severity == expected
    if expected == "warning":
        assert result.details["threshold_postclose_status_content_status"] == "running"
        assert (
            result.details["threshold_postclose_status_upstream_status"]
            == "running_before_deadline"
        )
    else:
        assert result.details["threshold_postclose_status_status"] == "fail"


@pytest.mark.parametrize(
    "argv,expected",
    [
        (
            ["bash", "/release/deploy/run_threshold_cycle_postclose.sh", "2026-09-10"],
            True,
        ),
        (
            [
                "bash",
                "/release/deploy/.run_threshold_cycle_postclose.snapshot.abc.sh",
                "2026-09-10",
            ],
            True,
        ),
        (
            ["bash", "/release/deploy/run_threshold_cycle_postclose.sh", "2026-09-09"],
            False,
        ),
        (["bash", "-c", "echo run_threshold_cycle_postclose.sh 2026-09-10"], False),
        (["python", "unrelated.py", "2026-09-10"], False),
    ],
)
def test_bounded_postclose_process_matches_argv_date_and_snapshot(
    tmp_path, argv, expected
):
    proc_root = tmp_path / "proc"
    process = proc_root / "99999999"
    process.mkdir(parents=True)
    (process / "cmdline").write_bytes("\0".join(argv).encode() + b"\0")
    with patch(
        "src.engine.error_detectors.artifact_freshness.Path",
        side_effect=lambda value: proc_root if value == "/proc" else Path(value),
    ):
        result = ArtifactFreshnessDetector._has_matching_live_process(
            {"process_patterns": ["run_threshold_cycle_postclose.sh"]},
            target_date="2026-09-10",
        )
    assert result is expected


class TestArtifactFreshnessDetector:
    def test_preopen_artifacts_allow_one_detector_interval_for_producer_race(self):
        preopen_artifacts = {
            artifact["id"]: artifact
            for artifact in ARTIFACT_REGISTRY
            if artifact["id"] == "runtime_policy_bootstrap"
        }

        assert set(preopen_artifacts) == {"runtime_policy_bootstrap"}
        assert all(
            artifact["window_start"] == (7, 35)
            and artifact["window_grace_sec"] == 300
            and artifact["critical"] is True
            for artifact in preopen_artifacts.values()
        )

    def test_preopen_stale_artifact_fails_after_producer_grace(self, tmp_path):
        fixed_now = datetime(2026, 8, 12, 7, 40, 1)
        artifact_path = tmp_path / "threshold_runtime_env_2026-08-12.json"
        artifact_path.write_text("{}\n", encoding="utf-8")
        stale_mtime = fixed_now.timestamp() - 36_000
        os.utime(artifact_path, (stale_mtime, stale_mtime))
        artifact = {
            "id": "threshold_runtime_env",
            "path_template": str(artifact_path),
            "max_staleness_sec": 900,
            "critical": True,
            "window_start": (7, 35),
            "window_end": (7, 50),
            "window_grace_sec": 300,
            "trading_day_only": True,
        }

        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
            patch(
                "src.engine.error_detectors.artifact_freshness.datetime"
            ) as datetime_mock,
            patch(
                "src.engine.error_detectors.artifact_freshness.time.time",
                return_value=fixed_now.timestamp(),
            ),
        ):
            datetime_mock.now.return_value = fixed_now
            result = ArtifactFreshnessDetector().check()

        assert result.severity == "fail"
        assert result.details["threshold_runtime_env_status"] == "fail"

    def test_classify_pass(self):
        detector = ArtifactFreshnessDetector()
        severity, summary = detector._classify([], [])
        assert severity == "pass"

    def test_classify_warning(self):
        detector = ArtifactFreshnessDetector()
        severity, summary = detector._classify([], ["stale file"])
        assert severity == "warning"

    def test_classify_fail(self):
        detector = ArtifactFreshnessDetector()
        severity, summary = detector._classify(["missing"], [])
        assert severity == "fail"

    def test_fresh_file_passes(self, tmp_path):
        log_file = tmp_path / "fresh.log"
        log_file.write_text("content", encoding="utf-8")
        artifact = {
            "id": "test_fresh",
            "path_template": str(log_file),
            "max_staleness_sec": 600,
            "critical": True,
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity in ("pass", "warning", "fail")

    def test_missing_critical_file_fails(self):
        artifact = {
            "id": "test_missing",
            "path_template": "/nonexistent/path/file.json",
            "max_staleness_sec": 600,
            "critical": True,
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "fail"

    def test_uninstalled_swing_artifact_is_terminally_disabled(self, tmp_path):
        artifact = {
            "id": "swing_live_dry_run_status",
            "path_template": str(tmp_path / "missing.json"),
            "max_staleness_sec": 600,
            "critical": True,
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
            patch(
                "src.engine.error_detectors.artifact_freshness.load_installed_crontab",
                return_value="10 20 * * 1-5 runner # THRESHOLD_CYCLE_POSTCLOSE\n",
            ),
        ):
            result = ArtifactFreshnessDetector().check()

        assert result.severity == "pass"
        assert (
            result.details["swing_live_dry_run_status_status"]
            == "disabled_not_installed"
        )

    def test_parent_disabled_swing_artifact_is_terminally_disabled(self, tmp_path):
        artifact = {
            "id": "swing_lifecycle_audit_report",
            "path_template": str(tmp_path / "missing.md"),
            "max_staleness_sec": 600,
            "critical": True,
        }
        crontab = (
            "10 20 * * 1-5 THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE=false "
            "runner # THRESHOLD_CYCLE_POSTCLOSE\n"
        )
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
            patch(
                "src.engine.error_detectors.artifact_freshness.load_installed_crontab",
                return_value=crontab,
            ),
        ):
            result = ArtifactFreshnessDetector().check()

        assert result.severity == "pass"
        assert (
            result.details["swing_lifecycle_audit_report_status"]
            == "disabled_by_parent"
        )

    def test_default_disabled_codex_artifact_is_terminally_disabled(self, tmp_path):
        artifact = {
            "id": "codex_workorder_runner_report",
            "path_template": str(tmp_path / "missing.json"),
            "max_staleness_sec": 600,
            "critical": True,
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
            patch(
                "src.engine.error_detectors.artifact_freshness.load_installed_crontab",
                return_value=("10 20 * * 1-5 runner # POSTCLOSE_DONE_CONTROLLER\n"),
            ),
        ):
            result = ArtifactFreshnessDetector().check()

        assert result.severity == "pass"
        assert (
            result.details["codex_workorder_runner_report_status"]
            == "disabled_by_parent"
        )

    def test_default_disabled_codebase_performance_artifact_is_not_required(
        self, tmp_path
    ):
        artifact = {
            "id": "codebase_performance_workorder_report",
            "path_template": str(tmp_path / "missing.md"),
            "max_staleness_sec": 600,
            "critical": True,
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
            patch(
                "src.engine.error_detectors.artifact_freshness.load_installed_crontab",
                return_value=("10 20 * * 1-5 runner # THRESHOLD_CYCLE_POSTCLOSE\n"),
            ),
        ):
            result = ArtifactFreshnessDetector().check()

        assert result.severity == "pass"
        assert (
            result.details["codebase_performance_workorder_report_status"]
            == "disabled_by_parent"
        )

    def test_explicitly_enabled_codebase_performance_artifact_remains_required(
        self, tmp_path
    ):
        artifact = {
            "id": "codebase_performance_workorder_report",
            "path_template": str(tmp_path / "missing.md"),
            "max_staleness_sec": 600,
            "critical": True,
        }
        crontab = (
            "10 20 * * 1-5 "
            "THRESHOLD_CYCLE_RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT=true "
            "runner # THRESHOLD_CYCLE_POSTCLOSE\n"
        )
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
            patch(
                "src.engine.error_detectors.artifact_freshness.load_installed_crontab",
                return_value=crontab,
            ),
        ):
            result = ArtifactFreshnessDetector().check()

        assert result.severity == "fail"
        assert result.details["codebase_performance_workorder_report_status"] == "fail"

    def test_step_scoped_skip_marker_is_terminal_success(self, monkeypatch, tmp_path):
        import src.engine.error_detectors.artifact_freshness as af

        today = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "threshold_cycle_postclose_cron.log").write_text(
            "[SKIP] threshold-cycle postclose "
            f"target_date={today} step=codebase_performance_workorder "
            "reason=fresh_outputs_no_trigger\n",
            encoding="utf-8",
        )
        artifact = {
            "id": "codebase_performance_workorder_report",
            "path_template": "data/report/missing.md",
            "max_staleness_sec": 600,
            "critical": True,
        }
        monkeypatch.setattr(af, "PROJECT_ROOT", tmp_path)
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
            patch(
                "src.engine.error_detectors.artifact_freshness.load_installed_crontab",
                return_value=None,
            ),
            patch("src.engine.error_detectors.artifact_freshness._holding_profit_exit_semantics",
                  return_value={"findings": []}),
            patch("src.engine.error_detectors.artifact_freshness._machine_result_semantics",
                  return_value={"findings": []}),
            patch("src.engine.error_detectors.artifact_freshness._auxiliary_result_semantics",
                  return_value={"findings": []}),
            patch("src.engine.error_detectors.artifact_freshness._initial_quantity_semantics",
                  return_value={"findings": []}),
        ):
            result = ArtifactFreshnessDetector().check()

        assert result.severity == "pass"
        assert (
            result.details["codebase_performance_workorder_report_status"]
            == "pass_terminal_skip"
        )

    def test_unrelated_step_skip_does_not_close_missing_artifact(
        self, monkeypatch, tmp_path
    ):
        import src.engine.error_detectors.artifact_freshness as af

        today = datetime.now().strftime("%Y-%m-%d")
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "threshold_cycle_postclose_cron.log").write_text(
            "[SKIP] threshold-cycle postclose "
            f"target_date={today} step=some_other_report reason=disabled\n",
            encoding="utf-8",
        )
        artifact = {
            "id": "codebase_performance_workorder_report",
            "path_template": "data/report/missing.md",
            "max_staleness_sec": 600,
            "critical": True,
        }
        monkeypatch.setattr(af, "PROJECT_ROOT", tmp_path)
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
            patch(
                "src.engine.error_detectors.artifact_freshness.load_installed_crontab",
                return_value=None,
            ),
        ):
            result = ArtifactFreshnessDetector().check()

        assert result.severity == "fail"
        assert result.details["codebase_performance_workorder_report_status"] == "fail"

    def test_invalid_critical_json_fails(self, tmp_path):
        artifact_path = tmp_path / "invalid.json"
        artifact_path.write_text("{bad json", encoding="utf-8")
        artifact = {
            "id": "test_invalid_json",
            "path_template": str(artifact_path),
            "max_staleness_sec": 600,
            "critical": True,
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "fail"
            assert result.details["test_invalid_json_status"] == "fail"

    def test_critical_json_status_not_ok_fails(self, tmp_path):
        artifact_path = tmp_path / "status.json"
        artifact_path.write_text('{"status":"running"}', encoding="utf-8")
        artifact = {
            "id": "test_status",
            "path_template": str(artifact_path),
            "max_staleness_sec": 600,
            "critical": True,
            "json_status_field": "status",
            "json_ok_values": ["succeeded"],
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "fail"
            assert result.details["test_status_status"] == "fail"

    def test_window_not_yet_due(self):
        artifact = {
            "id": "test_future",
            "path_template": "/nonexistent/path/file.json",
            "max_staleness_sec": 600,
            "critical": True,
            "window_start": (23, 59),
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            detail_key = "test_future_status"
            assert detail_key in result.details
            assert result.details[detail_key] == "not_yet_due"

    def test_window_startup_grace_suppresses_missing_critical_file(self):
        now = datetime.now()
        artifact = {
            "id": "test_startup_grace",
            "path_template": "/nonexistent/path/file.json",
            "max_staleness_sec": 600,
            "critical": True,
            "window_start": (now.hour, now.minute),
            "window_end": (23, 59),
            "window_grace_sec": 7200,
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "pass"
            assert result.details.get("test_startup_grace_status") == "startup_grace"

    def test_window_startup_grace_suppresses_stale_critical_file(self, tmp_path):
        now = datetime.now()
        artifact_path = tmp_path / "stale.jsonl"
        artifact_path.write_text("old event\n", encoding="utf-8")
        stale_mtime = time.time() - 900
        os.utime(artifact_path, (stale_mtime, stale_mtime))
        artifact = {
            "id": "test_startup_stale_grace",
            "path_template": str(artifact_path),
            "max_staleness_sec": 600,
            "critical": True,
            "window_start": (now.hour, now.minute),
            "window_end": (23, 59),
            "window_grace_sec": 7200,
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "pass"
            assert (
                result.details.get("test_startup_stale_grace_status") == "startup_grace"
            )
            assert (
                result.details.get("test_startup_stale_grace_startup_stale_suppressed")
                is True
            )

    def test_missing_critical_artifact_warns_when_upstream_cron_in_progress(
        self, tmp_path
    ):
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        cron_log = tmp_path / "postclose.log"
        cron_log.write_text(
            f"[START] threshold-cycle postclose target_date={today}\n", encoding="utf-8"
        )
        artifact = {
            "id": "runtime_approval_summary_report",
            "path_template": str(tmp_path / "missing_threshold_ev.json"),
            "max_staleness_sec": 600,
            "critical": True,
            "window_start": (now.hour, now.minute),
            "window_end": (23, 59),
            "suppress_missing_while_cron_in_progress": {
                "id": "threshold_cycle_postclose",
                "log": str(cron_log),
            },
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "warning"
            assert result.details.get("runtime_approval_summary_report_status") == "warning"
            assert (
                result.details.get("runtime_approval_summary_report_upstream_status")
                == "in_progress"
            )

    def test_missing_critical_artifact_warns_when_upstream_process_in_progress(
        self, tmp_path
    ):
        now = datetime.now()
        artifact = {
            "id": "runtime_approval_summary_report",
            "path_template": str(tmp_path / "missing_threshold_ev.json"),
            "max_staleness_sec": 600,
            "critical": True,
            "window_start": (now.hour, now.minute),
            "window_end": (23, 59),
            "suppress_missing_while_cron_in_progress": {
                "id": "threshold_cycle_postclose",
                "log": str(tmp_path / "missing_postclose.log"),
                "process_patterns": ["deploy/run_threshold_cycle_postclose.sh"],
            },
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
            patch(
                "src.engine.error_detectors.artifact_freshness."
                "ArtifactFreshnessDetector._has_matching_live_process",
                return_value=True,
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "warning"
            assert result.details.get("runtime_approval_summary_report_status") == "warning"
            assert (
                result.details.get("runtime_approval_summary_report_upstream_status")
                == "in_progress"
            )

    def test_postclose_done_controller_report_uses_controller_cron_for_in_progress_suppression(
        self, tmp_path
    ):
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        controller_log = tmp_path / "postclose_done_controller_cron.log"
        controller_log.write_text(
            f"[DONE] postclose_done_controller target_date=2000-01-01 finished_at={today}T00:27:44+0900\n"
            f"[START] postclose_done_controller target_date={today} started_at={today}T20:40:01+0900\n",
            encoding="utf-8",
        )
        artifact = {
            "id": "postclose_done_controller_report",
            "path_template": str(tmp_path / "postclose_done_controller_missing.json"),
            "max_staleness_sec": 3600,
            "critical": True,
            "window_start": (now.hour, now.minute),
            "window_end": (23, 59),
            "suppress_missing_while_cron_in_progress": {
                "id": "postclose_done_controller",
                "log": str(controller_log),
            },
            "allow_missing_after_window_while_cron_in_progress": True,
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "warning"
            assert (
                result.details.get("postclose_done_controller_report_status")
                == "warning"
            )
            assert (
                result.details.get("postclose_done_controller_report_upstream_status")
                == "in_progress"
            )

    @pytest.mark.parametrize("previous", ["DONE", "FAIL"])
    def test_upstream_latest_run_survives_rotation_and_verbose_output(
        self, tmp_path, previous
    ):
        day = "2026-09-08"
        log = tmp_path / "controller.log"
        log.with_suffix(".log.1").write_text(
            f"[{previous}] controller target_date={day}\n"
            f"[START] controller target_date={day}\n",
            encoding="utf-8",
        )
        log.write_text(
            '{"quoted": "[DONE] controller target_date=2026-09-08"}\n'
            + "payload detail\n" * 300,
            encoding="utf-8",
        )
        config = {"log": str(log)}
        assert ArtifactFreshnessDetector._is_upstream_cron_in_progress(config, day)
        with log.open("a", encoding="utf-8") as stream:
            stream.write(f"[FAIL] controller target_date={day}\n")
        assert not ArtifactFreshnessDetector._is_upstream_cron_in_progress(config, day)

    def test_other_date_start_does_not_suppress_missing_artifact(self, tmp_path):
        log = tmp_path / "controller.log"
        log.write_text(
            "[START] controller target_date=2026-09-07 started_at=2026-09-08T00:01:00\n",
            encoding="utf-8",
        )
        assert not ArtifactFreshnessDetector._is_upstream_cron_in_progress(
            {"log": str(log)}, "2026-09-08"
        )

    def test_missing_critical_artifact_warns_after_window_when_upstream_cron_still_in_progress(
        self, tmp_path
    ):
        today = datetime.now().strftime("%Y-%m-%d")
        cron_log = tmp_path / "postclose.log"
        cron_log.write_text(
            f"[START] threshold-cycle postclose target_date={today}\n", encoding="utf-8"
        )
        artifact = {
            "id": "runtime_approval_summary_report",
            "path_template": str(tmp_path / "missing_threshold_ev.json"),
            "max_staleness_sec": 600,
            "critical": True,
            "window_start": (0, 0),
            "window_end": (0, 1),
            "allow_missing_after_window_while_cron_in_progress": True,
            "suppress_missing_while_cron_in_progress": {
                "id": "threshold_cycle_postclose",
                "log": str(cron_log),
            },
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "warning"
            assert result.details.get("runtime_approval_summary_report_status") == "warning"
            assert (
                result.details.get("runtime_approval_summary_report_upstream_status")
                == "in_progress_after_window"
            )

    def test_non_trading_day_skips(self):
        artifact = {
            "id": "test_skip",
            "path_template": "/nonexistent/path/file.json",
            "max_staleness_sec": 600,
            "critical": True,
            "trading_day_only": True,
        }
        with (
            patch(_TRADING_MOCK, return_value=False),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "pass"
            assert result.details.get("test_skip_status") == "skip_non_trading_day"

    def test_past_window_end_exists_passes(self, tmp_path):
        log_file = tmp_path / "past_window.log"
        log_file.write_text("content", encoding="utf-8")
        artifact = {
            "id": "test_past_window",
            "path_template": str(log_file),
            "max_staleness_sec": 600,
            "critical": True,
            "window_start": (0, 0),
            "window_end": (0, 1),
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.details.get("test_past_window_status") == "pass_after_window"

    def test_window_end_boundary_existing_artifact_passes_after_window(self, tmp_path):
        log_file = tmp_path / "window_end_boundary.log"
        log_file.write_text("content", encoding="utf-8")
        stale_ts = time.time() - 901
        os.utime(log_file, (stale_ts, stale_ts))
        now = datetime.now()
        artifact = {
            "id": "test_window_end_boundary",
            "path_template": str(log_file),
            "max_staleness_sec": 900,
            "critical": True,
            "window_start": (0, 0),
            "window_end": (now.hour, now.minute),
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "pass"
            assert (
                result.details.get("test_window_end_boundary_status")
                == "pass_after_window"
            )

    def test_one_shot_artifact_exists_passes_even_when_stale_inside_window(
        self, tmp_path
    ):
        report_file = tmp_path / "threshold_cycle_ev.json"
        report_file.write_text("{}", encoding="utf-8")
        stale_ts = time.time() - 7200
        os.utime(report_file, (stale_ts, stale_ts))
        now = datetime.now()
        artifact = {
            "id": "runtime_approval_summary_report",
            "path_template": str(report_file),
            "max_staleness_sec": 1800,
            "critical": True,
            "one_shot": True,
            "window_start": (now.hour, now.minute),
            "window_end": (23, 59),
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "pass"
            assert (
                result.details.get("runtime_approval_summary_report_status")
                == "pass_one_shot"
            )
            assert result.details.get("runtime_approval_summary_report_age_sec", 0) > 1800

    def test_threshold_postclose_status_succeeded_is_one_shot_completion(
        self, tmp_path
    ):
        status_file = tmp_path / "threshold_cycle_postclose.status.json"
        status_file.write_text(
            '{"status":"succeeded","target_date":"2026-07-02"}', encoding="utf-8"
        )
        stale_ts = time.time() - 7200
        os.utime(status_file, (stale_ts, stale_ts))
        now = datetime.now()
        artifact = {
            "id": "threshold_postclose_status",
            "path_template": str(status_file),
            "max_staleness_sec": 3600,
            "critical": True,
            "one_shot": True,
            "window_start": (now.hour, now.minute),
            "window_end": (23, 59),
            "json_status_field": "status",
            "json_ok_values": ["succeeded"],
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "pass"
            assert (
                result.details.get("threshold_postclose_status_content_status")
                == "succeeded"
            )
            assert (
                result.details.get("threshold_postclose_status_status")
                == "pass_one_shot"
            )
            assert result.details.get("threshold_postclose_status_age_sec", 0) > 3600

    def test_daily_recommendations_csv_content_date_suppresses_mtime_stale_inside_window(
        self, tmp_path
    ):
        reco_file = tmp_path / "daily_recommendations_v2.csv"
        content_date = (datetime.now() - timedelta(days=1)).date().isoformat()
        reco_file.write_text(
            "date,code,name,generated_at\n"
            f"{content_date},005930,삼성전자,{datetime.now().isoformat()}\n",
            encoding="utf-8",
        )
        stale_ts = time.time() - 7200
        os.utime(reco_file, (stale_ts, stale_ts))
        now = datetime.now()
        artifact = {
            "id": "daily_recommendations_csv",
            "path_template": str(reco_file),
            "max_staleness_sec": 3600,
            "critical": False,
            "window_start": (now.hour, now.minute),
            "window_end": (23, 59),
            "content_freshness": {
                "format": "csv",
                "date_field": "date",
                "max_age_days": 7,
                "min_rows": 1,
            },
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "pass"
            assert (
                result.details.get("daily_recommendations_csv_status")
                == "pass_content_date"
            )
            assert (
                result.details.get("daily_recommendations_csv_content_status") == "pass"
            )
            assert result.details.get("daily_recommendations_csv_content_age_days") == 1

    def test_daily_recommendations_diag_content_date_suppresses_mtime_stale_inside_window(
        self, tmp_path
    ):
        diag_file = tmp_path / "daily_recommendations_v2_diagnostics.json"
        content_date = (datetime.now() - timedelta(days=1)).date().isoformat()
        diag_file.write_text(
            f'{{"latest_date": "{content_date}", "selected_count": 3}}',
            encoding="utf-8",
        )
        stale_ts = time.time() - 7200
        os.utime(diag_file, (stale_ts, stale_ts))
        now = datetime.now()
        artifact = {
            "id": "daily_recommendations_diag",
            "path_template": str(diag_file),
            "max_staleness_sec": 3600,
            "critical": False,
            "window_start": (now.hour, now.minute),
            "window_end": (23, 59),
            "content_freshness": {
                "format": "json",
                "date_field": "latest_date",
                "max_age_days": 7,
                "min_count_field": "selected_count",
                "min_count": 1,
            },
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "pass"
            assert (
                result.details.get("daily_recommendations_diag_status")
                == "pass_content_date"
            )
            assert (
                result.details.get("daily_recommendations_diag_content_status")
                == "pass"
            )
            assert result.details.get("daily_recommendations_diag_selected_count") == 3

    def test_daily_recommendations_diag_content_date_stale_warns_inside_window(
        self, tmp_path
    ):
        diag_file = tmp_path / "daily_recommendations_v2_diagnostics.json"
        content_date = (datetime.now() - timedelta(days=9)).date().isoformat()
        diag_file.write_text(
            f'{{"latest_date": "{content_date}", "selected_count": 3}}',
            encoding="utf-8",
        )
        stale_ts = time.time() - 7200
        os.utime(diag_file, (stale_ts, stale_ts))
        now = datetime.now()
        artifact = {
            "id": "daily_recommendations_diag",
            "path_template": str(diag_file),
            "max_staleness_sec": 3600,
            "critical": False,
            "window_start": (now.hour, now.minute),
            "window_end": (23, 59),
            "content_freshness": {
                "format": "json",
                "date_field": "latest_date",
                "max_age_days": 7,
                "min_count_field": "selected_count",
                "min_count": 1,
            },
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "warning"
            assert result.details.get("daily_recommendations_diag_status") == "warning"
            assert (
                result.details.get("daily_recommendations_diag_content_status")
                == "stale_date"
            )

    def test_past_window_end_missing_fails(self):
        artifact = {
            "id": "test_past_window_missing",
            "path_template": "/nonexistent/after_window_file.json",
            "max_staleness_sec": 600,
            "critical": True,
            "window_start": (0, 0),
            "window_end": (0, 1),
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "fail"

    def test_json_status_value_is_validated(self, tmp_path):
        status_file = tmp_path / "status.json"
        status_file.write_text('{"status": "failed"}', encoding="utf-8")
        artifact = {
            "id": "test_status_json",
            "path_template": str(status_file),
            "max_staleness_sec": 600,
            "critical": False,
            "json_status_field": "status",
            "json_ok_values": ["completed"],
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "warning"
            assert result.details["test_status_json_content_status"] == "failed"

    def test_json_status_ok_passes(self, tmp_path):
        status_file = tmp_path / "status.json"
        status_file.write_text('{"status": "completed"}', encoding="utf-8")
        artifact = {
            "id": "test_status_json",
            "path_template": str(status_file),
            "max_staleness_sec": 600,
            "critical": False,
            "json_status_field": "status",
            "json_ok_values": ["completed"],
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "pass"
            assert result.details["test_status_json_content_status"] == "completed"

    def test_swing_automation_artifacts_are_registered_with_status_guards(self):
        registry = {str(item["id"]): item for item in ARTIFACT_REGISTRY}

        assert registry["swing_live_dry_run_status"]["json_status_field"] == "status"
        assert "succeeded" in registry["swing_live_dry_run_status"]["json_ok_values"]
        assert registry["swing_live_dry_run_status"]["window_start"] == (20, 15)
        assert registry["swing_lifecycle_audit_report"]["window_start"] == (20, 10)
        assert registry["swing_runtime_approval_report"]["window_start"] == (20, 10)
        assert registry["codebase_performance_workorder_report"]["window_start"] == (
            20,
            10,
        )
        assert registry["codebase_performance_workorder_report"]["window_end"] == (
            21,
            40,
        )
        assert (
            registry["swing_daily_simulation_status"]["json_status_field"] == "status"
        )
        assert registry["swing_daily_simulation_status"]["one_shot"] is True
        assert (
            "swing_daily_simulation_{date}.json"
            in registry["swing_daily_simulation_report"]["path_template"]
        )
        assert registry["swing_daily_simulation_report"]["one_shot"] is True
        assert (
            "swing_pattern_lab_automation_{date}.json"
            in registry["swing_pattern_lab_automation_report"]["path_template"]
        )
        assert (
            "current.json" in registry["swing_model_registry_current"]["path_template"]
        )
        assert registry["pipeline_events"]["window_grace_sec"] == 300
        assert registry["threshold_events"]["critical"] is False
        assert registry["threshold_events"]["window_grace_sec"] == 300
        assert "partitioned_compact" in registry["threshold_events"]
        assert registry["runtime_approval_summary_report"]["one_shot"] is True

    def test_partitioned_threshold_events_checkpoint_passes_when_legacy_file_missing(
        self, tmp_path
    ):
        today = datetime.now().strftime("%Y-%m-%d")
        checkpoint = tmp_path / "checkpoints" / f"{today}.json"
        part = (
            tmp_path
            / f"date={today}"
            / "family=soft_stop_whipsaw_confirmation"
            / "part-000001.jsonl"
        )
        temp_part = part.with_name(f"{part.name}.gz.tmp")
        checkpoint.parent.mkdir(parents=True)
        part.parent.mkdir(parents=True)
        checkpoint.write_text(
            '{"completed": true, "status": "completed", "written_count": 1}',
            encoding="utf-8",
        )
        part.write_text('{"stage":"soft_stop_micro_grace"}\n', encoding="utf-8")
        temp_part.write_bytes(b"incomplete gzip")
        artifact = {
            "id": "threshold_events",
            "path_template": str(tmp_path / f"threshold_events_{today}.jsonl"),
            "max_staleness_sec": 600,
            "critical": False,
            "partitioned_compact": {
                "checkpoint_template": str(checkpoint),
                "partition_glob_template": str(
                    tmp_path / f"date={today}" / "family=*" / "part-*.jsonl*"
                ),
            },
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "pass"
            assert (
                result.details["threshold_events_status"]
                == "pass_partitioned_checkpoint"
            )
            assert result.details["threshold_events_legacy_path_missing"] is True
            assert result.details["threshold_events_partitioned_completed"] is True
            assert result.details["threshold_events_partitioned_part_count"] == 1

    def test_partitioned_threshold_events_incomplete_checkpoint_warns(self, tmp_path):
        today = datetime.now().strftime("%Y-%m-%d")
        checkpoint = tmp_path / "checkpoints" / f"{today}.json"
        part = (
            tmp_path
            / f"date={today}"
            / "family=soft_stop_whipsaw_confirmation"
            / "part-000001.jsonl"
        )
        checkpoint.parent.mkdir(parents=True)
        part.parent.mkdir(parents=True)
        checkpoint.write_text(
            '{"completed": false, "status": "paused_by_availability_guard", "paused_reason": "cpu_busy_pct>=95"}',
            encoding="utf-8",
        )
        part.write_text('{"stage":"soft_stop_micro_grace"}\n', encoding="utf-8")
        artifact = {
            "id": "threshold_events",
            "path_template": str(tmp_path / f"threshold_events_{today}.jsonl"),
            "max_staleness_sec": 600,
            "critical": False,
            "partitioned_compact": {
                "checkpoint_template": str(checkpoint),
                "partition_glob_template": str(
                    tmp_path / f"date={today}" / "family=*" / "part-*.jsonl"
                ),
            },
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "warning"
            assert result.details["threshold_events_status"] == "warning"
            assert result.details["threshold_events_partitioned_completed"] is False
            assert (
                result.details["threshold_events_partitioned_paused_reason"]
                == "cpu_busy_pct>=95"
            )


def test_historical_bootstrap_uses_prepared_day_without_early_preopen(tmp_path, monkeypatch):
    import src.engine.error_detectors.artifact_freshness as mod
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 9, 20, 15, 0)
    monkeypatch.setattr(mod, 'datetime', Clock)
    monkeypatch.setattr(mod, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(mod, 'ARTIFACT_REGISTRY', [row for row in ARTIFACT_REGISTRY if row['id']=='runtime_policy_bootstrap'])
    monkeypatch.setattr(mod, 'load_installed_crontab', lambda: '')
    monkeypatch.setenv('POSTCLOSE_PREPARED_EFFECTIVE_DATE', '2026-09-21')
    detector = mod.ArtifactFreshnessDetector(dry_run=True)
    detector.postclose_source_date = '2026-09-17'
    result = detector.check()
    assert result.details['runtime_policy_bootstrap_status'] == 'future_due'
    assert not list(tmp_path.rglob('*.json'))
    monkeypatch.setenv('POSTCLOSE_PREPARED_EFFECTIVE_DATE', '2026-09-18')
    result = detector.check()
    assert result.severity == 'fail'
    monkeypatch.delenv('POSTCLOSE_PREPARED_EFFECTIVE_DATE')
    assert detector.check().severity == 'fail'


def test_submission_monitor_does_not_require_artifacts_before_installation(tmp_path, monkeypatch):
    import src.engine.error_detectors.artifact_freshness as mod
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 9, 21, 10, 0)
    monkeypatch.setattr(mod, 'datetime', Clock)
    monkeypatch.setattr(mod, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(mod, 'ARTIFACT_REGISTRY', [r for r in ARTIFACT_REGISTRY if r['id']=='submission_bottleneck_monitor'])
    monkeypatch.setattr(mod, 'load_installed_crontab', lambda: '')
    detector = mod.ArtifactFreshnessDetector(dry_run=True)
    detector.postclose_source_date = '2026-09-17'
    assert detector.check().details['submission_bottleneck_monitor_status'] == 'not_required_before_introduction'
    detector.postclose_source_date = '2026-09-21'
    assert detector.check().severity == 'fail'  # future normal producer must exist
