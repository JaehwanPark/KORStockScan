from __future__ import annotations


def test_main_stop_alert_uses_current_preopen_owner_after_transfer():
    from src.engine.error_detectors.artifact_freshness import _project_semantic_owner
    alert = dict(stage='main_stop_confirmation', owner='main_stop_confirmation', target_date='2026-10-14')
    _project_semantic_owner(alert, {'DirectFamilyPreopenPolicyHandoff'}, '2026-10-14')
    assert alert['owner'] == 'DirectFamilyPreopenPolicyHandoff'
    assert alert['owner_status'] == 'current_open'
    assert alert['historical_owner'] == 'main_stop_confirmation'


def test_historical_family_kernel_uses_exact_original_bytes_after_code_change(tmp_path):
    from src.engine.monitoring import family_policy_semantics as native
    import hashlib
    producer=tmp_path/'producer.py'; original=b'original producer\n'
    producer.write_bytes(original); sha=hashlib.sha256(original).hexdigest()
    archived=native.preserve_kernel(tmp_path/'data', original, sha)
    producer.write_bytes(b'retired sibling changed\n')
    assert native.verify_kernel(tmp_path/'data',producer,sha)=='retained_original_bytes'
    assert archived.read_bytes()==original
    archived.chmod(0o644);archived.write_bytes(b'corrupt\n')
    import pytest
    with pytest.raises(ValueError,match='archived_kernel_invalid'):
        native.verify_kernel(tmp_path/'data',producer,sha)


def test_family_kernel_never_manufactures_missing_original(tmp_path):
    from src.engine.monitoring import family_policy_semantics as native
    import pytest
    with pytest.raises(ValueError,match='original_kernel_missing'):
        native.verify_kernel(tmp_path/'data',tmp_path/'missing.py','a'*64)
    with pytest.raises(ValueError,match='kernel_content_invalid'):
        native.preserve_kernel(tmp_path/'data',b'current code','a'*64)



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
    _auxiliary_scope_contract,
    _postclose_handoff_semantics,
    _semantic_stage_binding,
    _semantic_alerts,
)
from src.engine.scalping.micro_reversion.symbol_master import SymbolLookupStatus

_TRADING_MOCK = "src.engine.error_detectors.artifact_freshness.is_krx_trading_day"


@pytest.mark.parametrize("owner", ["machine", "auxiliary", "handoff"])
def test_semantic_generation_race_is_unobservable_not_corruption(tmp_path, monkeypatch, owner):
    day = "2026-10-02"
    paths = {
        "machine": "data/report/postclose_stage_terminal/2026-10-02/legacy_machine_report.json",
        "auxiliary": "data/report/postclose_stage_terminal/2026-10-02/main_auxiliary_policy.json",
        "handoff": "data/report/postclose_stage_terminal/2026-10-02/summary_handoff.json",
    }
    path = tmp_path / paths[owner]
    path.parent.mkdir(parents=True)
    path.write_text("{}")
    def replaced_generation(*args, **kwargs):
        raise ValueError("semantic_generation_changed_during_read")
    monkeypatch.setattr("src.engine.error_detectors.artifact_freshness._semantic_object", replaced_generation)
    if owner == "handoff":
        result = _postclose_handoff_semantics(tmp_path, day, datetime(2026, 10, 2, tzinfo=ZoneInfo("Asia/Seoul")))
    else:
        result = {"machine": _machine_result_semantics, "auxiliary": _auxiliary_result_semantics}[owner](tmp_path, day)
    assert result["status"] == "unobservable"
    assert result["findings"] == []
    assert result["reason"] == "semantic_generation_changed_during_read"
    assert _semantic_alerts(owner, result, day) == []


@pytest.mark.parametrize('component,stage', [
    ('machine', 'main_machine_policy'), ('auxiliary', 'main_auxiliary_policy')])
def test_missing_reversal_execution_is_not_report_hash_corruption(tmp_path, component, stage):
    from src.engine.scalping import continuous_reversal_postclose as reports
    from src.engine.scalping import continuous_reversal_operating_postclose as operating
    from src.engine.error_detectors import artifact_freshness as detector
    day = '2026-10-13'
    path = tmp_path / 'data/report/continuous_reversal' / day / (component + '.json')
    path.parent.mkdir(parents=True)
    value = reports.seal(dict(schema=operating.SCHEMA, source_date=day, status='completed'))
    path.write_text(json.dumps(value))
    result = detector._continuous_reversal_result_semantics(tmp_path, day, component)
    reason = 'continuous_reversal_execution_not_completed:main_machine_policy'
    assert result['findings'] == [reason]
    alerts = _semantic_alerts(stage, result, day)
    assert [a['reason'] for a in alerts] == [reason]
    assert alerts[0]['artifact'] == str(path)
    assert alerts[0]['generation'] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_auxiliary_v4_frozen_same_day_contract_and_cost_isolation():
    from src.engine.scalping import compact_auxiliary_paired_replay as paired
    day, scope = "2026-10-02", "KRX|KRX_REGULAR"
    train = [[day, f"{i:06}", "KRX", "KRX_REGULAR", f"promotion-{i}"] for i in range(5)]
    held = [[day, f"{i:06}", "KRX", "KRX_REGULAR", f"promotion-{i}"] for i in range(5, 8)]
    manifest = {"version": "chronological_opportunity_purge_v1", "basis": "same_day_70_30_opportunities",
        "train_opportunity_ids": train, "holdout_opportunity_ids": held,
        "purged_opportunity_ids": [], "train_observation_end": day + "T10:00:00+09:00",
        "holdout_start": day + "T10:01:00+09:00"}
    candidate = {"policy": {"soft": "candidate"}, "prompt_version": "risk_v2",
                 "evaluation_status": "evaluated"}
    candidate["policy_sha256"] = paired.digest(candidate["policy"])
    value = {"selection_rank_version": "train_top1_frozen_paired_net_ev_holdout_gate_v4",
        "status": "candidate_selected", "split_manifest": manifest, "selected": candidate,
        "frozen_train_choice": candidate, "full_cost_candidate_population_count": 8,
        "candidates": [candidate], "completed_candidate_count": 1,
        "holdout_selection_candidate_count": 1,
        "cost_incomplete_diagnostic_count": 2, "current_machine_policy_sha256": "a" * 64,
        "parent_prompt_versions": ["parent"], "parent_soft_policy_sha256s": ["b" * 64],
        "train_population_sha256": "c" * 64,
        "metric_authority": "full_cost_fixed_checkpoint_cf_not_owner_portfolio"}
    receipt = paired.sealed({"schema": "auxiliary_train_selection_v1", "target_date": day,
        "scopes": {scope: {**candidate, "machine_policy_sha256": "a" * 64,
            "parent_prompt_version": "parent", "parent_soft_sha256": "b" * 64,
            "train_population_sha256": "c" * 64, "split_manifest": manifest}}})
    report = {"auxiliary_train_selection": receipt}
    assert _auxiliary_scope_contract(value, report, day, scope) == []
    value["selected"] = {**candidate, "prompt_version": "runner-up"}
    assert "auxiliary_selected_without_frozen_full_cost_evidence" in _auxiliary_scope_contract(value, report, day, scope)
    value["selected"] = candidate
    value["full_cost_candidate_population_count"] = 0
    assert "auxiliary_selected_without_frozen_full_cost_evidence" in _auxiliary_scope_contract(value, report, day, scope)
    value["status"] = "incumbent_carry"
    assert _auxiliary_scope_contract(value, report, day, scope) == []
    manifest["holdout_start"] = manifest["train_observation_end"]
    assert "auxiliary_chronological_split_invalid" in _auxiliary_scope_contract(value, report, day, scope)


@pytest.mark.parametrize('origin,generation,expected', [
    ('MAIN_FIXED_WATCH', 'generation-1', True),
    ('SCANNER', 'generation-1', False),
    ('MAIN_FIXED_WATCH', 'unknown', False),
])
def test_auxiliary_split_validates_full_fixed_watch_identity(origin, generation, expected):
    from src.engine.scalping import compact_auxiliary_paired_replay as paired
    manifest = {'version': 'chronological_opportunity_purge_v1',
        'train_opportunity_ids': [['2026-09-30', '000660', 'KRX', 'KRX_REGULAR', 'promotion-1']],
        'holdout_opportunity_ids': [['2026-10-02', '005930', 'KRX', 'KRX_REGULAR',
                                    origin, 'admission-1', generation]],
        'purged_opportunity_ids': [], 'train_observation_end': '2026-09-30T10:10:00+09:00',
        'holdout_start': '2026-10-02T09:00:00+09:00'}
    value = {'status': 'incumbent_carry', 'selection_rank_version': paired.STAGE_SELECTION_VERSION,
        'split_manifest': manifest, 'full_cost_candidate_population_count': 0,
        'cost_incomplete_diagnostic_count': 2, 'metric_authority': 'full_cost_fixed_checkpoint_cf_not_owner_portfolio',
        'candidates': [], 'completed_candidate_count': 0, 'holdout_selection_candidate_count': 0}
    errors = _auxiliary_scope_contract(value, {}, '2026-10-02', 'KRX|KRX_REGULAR')
    assert ('auxiliary_chronological_split_invalid' not in errors) is expected


@pytest.mark.parametrize('status,promotion,candidate,runtime_effect,apply,expected', [
    ('source_gap', False, None, False, False, True),
    ('hold_candidate', False, None, False, False, True),
    ('hold_candidate', False, {'version': 'held-diagnostic'}, False, False, True),
    ('hold_candidate', False, {'version': 'held-diagnostic'}, True, False, False),
    ('hold_candidate', False, {'version': 'held-diagnostic'}, False, True, False),
    ('hold_candidate', False, {'version': 'held-diagnostic'}, None, False, False),
    ('hold_candidate', False, {'version': 'held-diagnostic'}, False, None, False),
    ('source_gap', True, None, False, False, False),
    ('selected_machine_policy', False, {'version': 'old-candidate'}, False, False, False),
])
def test_machine_diagnostic_hold_does_not_require_current_promotion_version(
    tmp_path, monkeypatch, status, promotion, candidate, runtime_effect, apply, expected,
):
    from src.engine.scalping import entry_strategy_policy as strategy
    monkeypatch.setattr('src.engine.error_detectors.artifact_freshness._semantic_stage_binding',
                        lambda *args, **kwargs: {'status': 'succeeded'})
    day, scope = '2026-10-02', 'NXT|NXT_REGULAR'
    report = {'target_date': day, 'machine_full_evaluation': {'scope_evaluations': {
        scope: {'full_population_count': 0, 'current_structure_eligible_count': 0,
                'paired_comparable_count': None, 'row_exclusion_reason_counts': {}}}},
        'strategy_refinements_by_scope': {scope: {'status': status, 'promotion_pass': promotion,
            'candidate': candidate, 'selection_basis': strategy.MACHINE_SELECTION_VERSION,
            'runtime_effect': runtime_effect, 'allowed_runtime_apply': apply}}}
    report['artifact_content_sha256'] = hashlib.sha256(json.dumps(report,
        ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    path = tmp_path / 'data/report/ai_decision_action_outcome_calibration' / f'ai_decision_action_outcome_calibration_{day}.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(report))
    result = _machine_result_semantics(tmp_path, day)
    assert ('machine_selection_version_invalid' not in result['findings']) is expected


def test_semantic_stage_rejects_terminal_generation_mismatch(tmp_path):
    day, stage = "2026-10-02", "legacy_machine_report"
    path = tmp_path / "data/report/postclose_stage_terminal" / day / f"{stage}.json"
    path.parent.mkdir(parents=True)
    terminal = {"schema": "postclose_stage_terminal_v3", "source_date": day, "stage_id": stage,
                "status": "succeeded", "exit_code": 0, "sources": {"report": {"sha256": "a" * 64}}}
    terminal["receipt_sha256"] = hashlib.sha256(json.dumps(terminal, ensure_ascii=True,
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    path.write_text(json.dumps(terminal))
    assert _semantic_stage_binding(tmp_path, day, stage, artifact="report", artifact_sha="a" * 64)["status"] == "succeeded"
    with pytest.raises(ValueError, match="generation_mismatch"):
        _semantic_stage_binding(tmp_path, day, stage, artifact="report", artifact_sha="b" * 64)
    with pytest.raises(ValueError, match="source_path_invalid"):
        _semantic_stage_binding(tmp_path, day, stage, artifact="report", artifact_sha="a" * 64,
                                artifact_path=tmp_path / "wrong.json")
    terminal.update(status="failed", exit_code=2)
    terminal.pop("receipt_sha256")
    terminal["receipt_sha256"] = hashlib.sha256(json.dumps(terminal, ensure_ascii=True,
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    path.write_text(json.dumps(terminal))
    assert _machine_result_semantics(tmp_path, day)["findings"] == ["machine_execution_failed"]


def test_auxiliary_v4_diagnostic_only_population_is_not_a_candidate(tmp_path):
    from src.engine.scalping import compact_auxiliary_paired_replay as paired
    day = "2026-10-02"
    scope = {"status": "incumbent_carry", "eligible_count": 2, "selected": {},
        "selection_rank_version": "train_top1_frozen_paired_net_ev_holdout_gate_v4",
        "full_cost_candidate_population_count": 0, "cost_incomplete_diagnostic_count": 2,
        "metric_authority": "full_cost_fixed_checkpoint_cf_not_owner_portfolio",
        "split_manifest": {"train_opportunity_ids": [], "holdout_opportunity_ids": [], "purged_opportunity_ids": []},
        "candidates": [], "completed_candidate_count": 0, "holdout_selection_candidate_count": 0}
    stage = paired.sealed({"schema": "auxiliary_ai_stage_evaluation_v1", "source_date": day,
        "source_projection_sha256": "a" * 64, "source_manifest_sha256": "b" * 64,
        "source_tuning_allowed": True, "screened_total": 2, "eligible_count": 2, "excluded_count": 0,
        "eligible_keys": ["one", "two"], "candidate_population_keys": [],
        "scope_results": {"KRX|KRX_REGULAR": scope}, "runtime_effect": False, "actual_order_submitted": False})
    report = paired.sealed({"schema": paired.SCHEMA, "target_date": day,
        "source_projection_sha256": "a" * 64, "source_manifest_sha256": "b" * 64,
        "runtime_effect": False, "auxiliary_stage": stage})
    path = tmp_path / "data/report/ai_entry_setup_paired_replay_batch" / f"compact_auxiliary_paired_economic_{day}.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(report))
    result = _auxiliary_result_semantics(tmp_path, day)
    assert result["findings"] == ["auxiliary_independent_holdout_missing"]
    assert result["scopes"]["KRX|KRX_REGULAR"]["full_cost_count"] == 0
    assert _semantic_alerts("main_auxiliary_policy", result, day) == []
    # Producer candidate keys are the pre-purge full-cost cohort, not the
    # smaller train/holdout population retained after chronological purging.
    scope.update(eligible_count=8, full_cost_candidate_population_count=10)
    stage = paired.sealed({k:v for k,v in stage.items() if k != "artifact_content_sha256"} | {
        "screened_total": 12, "eligible_count": 12,
        "eligible_keys": [f"key-{i}" for i in range(12)],
        "candidate_population_keys": [f"key-{i}" for i in range(10)],
        "scope_results": {"KRX|KRX_REGULAR": scope}})
    report = paired.sealed({k:v for k,v in report.items() if k != "artifact_content_sha256"} | {"auxiliary_stage": stage})
    path.write_text(json.dumps(report))
    assert "auxiliary_candidate_population_invalid" not in _auxiliary_result_semantics(tmp_path, day)["findings"]


def test_semantic_alert_denominator_does_not_mix_current_economics_and_cumulative_cf():
    result = {"status": "source_gap", "eligible_count": 10, "screened_total": 44,
        "economic_screened_total": 6, "paired_comparable_count": 0,
        "outcome_label_source_gap_count": 6, "source_lineage_counts": {"writer_trace_plan_joined": 0},
        "findings": ["auxiliary_primary_economics_source_blocked", "auxiliary_outcome_label_source_gap",
                     "auxiliary_exact_plan_lineage_missing"]}
    alerts = _semantic_alerts("main_auxiliary_policy", result, "2026-09-30")
    assert all(a["total"] == 6 and a["eligible"] == 0 for a in alerts)


def test_prepared_semantics_does_not_claim_future_pid_or_ignore_stale_release(tmp_path, monkeypatch):
    from src.engine.automation import next_preopen_readiness as readiness
    target = "2026-10-02"
    index = tmp_path / "data/runtime/policy_bootstrap/prepared" / target / "latest.json"
    index.parent.mkdir(parents=True)
    index.write_text('{}')
    monkeypatch.setattr(readiness, "verify_prepared", lambda _, **kw: {"status": "fail", "findings": ["prepared_source_or_release_changed"]})
    result = _postclose_handoff_semantics(tmp_path, "2026-10-01", datetime(2026, 10, 1, 22))
    assert result["findings"] == ["next_preopen_prepared_contract_invalid"]
    assert result["consumption"] == "not_observed"


def test_current_morning_source_does_not_relabel_previous_prepared_failure(tmp_path, monkeypatch):
    from src.engine.automation import next_preopen_readiness as readiness
    index=tmp_path/'data/runtime/policy_bootstrap/prepared/2026-10-12/latest.json'
    index.parent.mkdir(parents=True);index.write_text('{}')
    monkeypatch.setattr(readiness,'verify_prepared',lambda *a,**k:pytest.fail('wrong source owns prepared check'))
    result=_postclose_handoff_semantics(tmp_path,'2026-10-12',datetime.fromisoformat('2026-10-12T07:10:00+09:00'))
    assert result['findings']==[] and result['prepared']['reason']=='source_not_before_target'


@pytest.mark.parametrize('damage', [None, 'handoff', 'other_generation'])
def test_postclose_observer_uses_consumed_snapshot_and_rechecks_other_sources(tmp_path, monkeypatch, damage):
    from src.engine.automation import intraday_release_handoff as handoff
    from src.engine.automation import postclose_done_controller as controller
    import src.engine.error_detectors.artifact_freshness as detector
    day = '2026-10-06'
    path = tmp_path/f'data/report/postclose_done_controller/postclose_done_controller_{day}.json'
    path.parent.mkdir(parents=True); path.write_text(json.dumps(dict(date=day, status='done')))
    snapshot = tmp_path/'historical-checklist.md'; snapshot.write_text('original generation')
    monkeypatch.setattr(detector, '_semantic_stage_binding', lambda *a, **kw: {'status': 'off'})
    calls = []
    def verify(path, source_date, **kwargs):
        assert source_date == day and kwargs['generation_only'] is True
        calls.append(kwargs)
        if not kwargs.get('checklist_snapshot'):
            return ['strict_checklist_generation_stale', 'strict_generation_changed_during_recheck']
        assert kwargs['checklist_snapshot'] == snapshot
        return ['strict_stage_generation_stale:main'] if damage == 'other_generation' else []
    monkeypatch.setattr(controller, 'done_terminal_receipt_issues', verify)
    def historical(project, source_date, **kwargs):
        assert project == tmp_path and source_date == day
        if damage == 'handoff': raise ValueError('intraday_observer_current_pid_not_bound')
        return dict(path=str(snapshot), basis='consumed_intraday_preserved_historical_generation', runtime_effect=False)
    monkeypatch.setattr(handoff, 'historical_checklist_for_observer', historical)
    result = _postclose_handoff_semantics(tmp_path, day, datetime(2026, 10, 7, 13, tzinfo=ZoneInfo('Asia/Seoul')))
    if damage is None:
        assert result['status'] == 'done' and result['findings'] == []
        assert len(calls) == 2 and result['historical_generation_validation']['runtime_effect'] is False
    else:
        assert result['findings'] == ['postclose_handoff_generation_invalid']
        if damage == 'other_generation':
            assert result['closure_errors'] == ['strict_stage_generation_stale:main']


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
        monkeypatch.setattr(mod, name, lambda *_, **__: {"status": "not_assessed",
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


@pytest.mark.parametrize("clock,overdue", [
    ((8, 4, 59), False), ((8, 5, 17), False), ((8, 10, 0), False),
    ((8, 10, 1), True), ((9, 0, 0), True),
])
def test_holding_first_publication_race_has_bounded_missing_receipt_grace(tmp_path, clock, overdue):
    registry = next(a for a in ARTIFACT_REGISTRY if a["id"] == "holding_exit_sentinel_premarket_report")
    assert registry["window_grace_sec"] == 300
    now = datetime(2026, 10, 15, *clock, tzinfo=ZoneInfo("Asia/Seoul"))
    result = _holding_profit_exit_semantics(tmp_path, "2026-10-15", now=now)
    assert result["expected_overdue"] is overdue
    assert result["findings"] == (["holding_semantic_receipt_missing_after_due"] if overdue else [])
    assert result["native_validated"] is False
    assert result["observation_complete"] is False


@pytest.mark.parametrize("artifact", ["markdown_only", "invalid_json", "wrong_date"])
def test_holding_first_publication_grace_never_hides_existing_invalid_receipt(tmp_path, artifact):
    path = tmp_path / "data/report/holding_exit_sentinel/holding_exit_sentinel_2026-10-15.json"
    path.parent.mkdir(parents=True)
    if artifact == "markdown_only":
        path.with_suffix(".md").write_text("# published\n")
    elif artifact == "invalid_json":
        path.write_text("{invalid")
    else:
        path.write_text(json.dumps({"target_date": "2026-10-14"}))
    now = datetime(2026, 10, 15, 8, 5, 17, tzinfo=ZoneInfo("Asia/Seoul"))
    result = _holding_profit_exit_semantics(tmp_path, "2026-10-15", now=now)
    assert result["status"] == "source_invalid"
    assert result["findings"]


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
    terminal = {"schema": "postclose_stage_terminal_v3",
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
    @pytest.fixture(autouse=True)
    def isolated_runtime_root(self, tmp_path, monkeypatch):
        # Registry fixtures must not consume the operator's live postclose data.
        monkeypatch.setattr("src.engine.error_detectors.artifact_freshness.PROJECT_ROOT", tmp_path)
        monkeypatch.setattr("src.engine.error_detectors.artifact_freshness._initial_quantity_semantics",
                            lambda *a, **k: {"status": "not_assessed", "findings": []})

        # These tests own individual artifact registry contracts. Independent
        # startup semantics have dedicated exact-receipt tests below.
        monkeypatch.setattr("src.engine.error_detectors.artifact_freshness._completed_semantic_source",
            lambda *a, **k: dict(findings=[], source_date=None, prepared_source_date=None, target_date="2026-10-06"))

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
        fixed_now = datetime(2026, 9, 10, 9, 0)
        today = fixed_now.strftime("%Y-%m-%d")
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
            patch("src.engine.error_detectors.artifact_freshness.datetime", wraps=datetime) as clock,
            patch("src.engine.error_detectors.artifact_freshness.time.time", return_value=fixed_now.timestamp()),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            clock.now.return_value = fixed_now
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
        fixed_now = datetime(2026, 9, 10, 9, 0)
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
            patch("src.engine.error_detectors.artifact_freshness.datetime", wraps=datetime) as clock,
            patch("src.engine.error_detectors.artifact_freshness.time.time", return_value=fixed_now.timestamp()),
            patch(
                "src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY",
                [artifact],
            ),
        ):
            clock.now.return_value = fixed_now
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


@pytest.mark.parametrize('unknown', [False, True])
def test_cancel_wait_detector_valid_carry_never_replays_or_alerts(tmp_path, monkeypatch, unknown):
    from src.tests.test_entry_cancel_wait_tuning import _reconciliation_fixture
    from src.engine.automation import entry_cancel_wait_tuning as cancel
    from src.engine.error_detectors.artifact_freshness import _entry_cancel_wait_result_semantics
    _reconciliation_fixture(tmp_path, monkeypatch, unknown_history=unknown)
    monkeypatch.setattr(cancel, 'build_report', lambda *_a: pytest.fail('read-only monitor replayed producer'))
    result = _entry_cancel_wait_result_semantics(tmp_path, '2026-10-02')
    assert result['status'] == 'incumbent_carry'
    assert result['findings'] == []
    assert result['daily_zero_is_verified'] is True
    assert result['historical_state'] == ('source_gap' if unknown else 'verified_empty')
    assert _semantic_alerts('entry_cancel_wait_tuning', result, '2026-10-02') == []


def test_cancel_wait_detector_false_zero_is_actionable_and_bound(tmp_path, monkeypatch):
    from src.tests.test_entry_cancel_wait_tuning import _reconciliation_fixture, _reseal_reconciliation
    from src.engine.automation import entry_cancel_wait_tuning as cancel
    from src.engine.error_detectors.artifact_freshness import _entry_cancel_wait_result_semantics
    report, policy, path, pp = _reconciliation_fixture(tmp_path, monkeypatch, unknown_history=True)
    report['historical_reconciliation']['zero_is_verified'] = True
    report['submission_census']['unresolved_prior_custody_count'] = 0
    _reseal_reconciliation(report)
    policy['report_proof_sha256'] = report['proof_sha256']
    policy['sha256'] = cancel._digest({k:v for k,v in policy.items() if k != 'sha256'})
    path.write_text(json.dumps(report)); pp.write_text(json.dumps(policy))
    result = _entry_cancel_wait_result_semantics(tmp_path, '2026-10-02')
    assert result['status'] == 'source_invalid'
    assert 'cancel_wait_false_historical_zero' in result['findings']
    alerts = _semantic_alerts('entry_cancel_wait_tuning', result, '2026-10-02')
    assert any(a['reason'] == 'cancel_wait_false_historical_zero' for a in alerts)
    assert all(a['owner'] == 'EntryCancelWaitSourceReconciliation1002' for a in alerts)


def test_cancel_wait_legacy_future_and_read_race_do_not_alert(tmp_path, monkeypatch):
    from src.engine.error_detectors import artifact_freshness as detector
    now = datetime(2026, 10, 2, 19, tzinfo=ZoneInfo('Asia/Seoul'))
    assert detector._entry_cancel_wait_result_semantics(tmp_path, '2026-10-02', now)['status'] == 'not_yet_due'
    path = tmp_path/'data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-02.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'date':'2026-10-02','economic_schema':'legacy'}))
    assert detector._entry_cancel_wait_result_semantics(tmp_path, '2026-10-02', now)['status'] == 'not_evaluated_legacy'
    monkeypatch.setattr(detector, '_semantic_object', lambda *_a, **_k: (_ for _ in ()).throw(ValueError('semantic_generation_changed_during_read')))
    result = detector._entry_cancel_wait_result_semantics(tmp_path, '2026-10-02', now)
    assert result['status'] == 'unobservable'
    assert detector._semantic_alerts('entry_cancel_wait_tuning', result, '2026-10-02') == []


def test_cancel_wait_native_success_without_artifact_is_not_empty(tmp_path):
    from src.engine.error_detectors.artifact_freshness import _entry_cancel_wait_result_semantics
    log = tmp_path/'logs/threshold_cycle_postclose_cron.log'
    log.parent.mkdir(parents=True)
    log.write_text('[PERF] '+json.dumps(dict(schema='postclose_command_metrics_v1', target_date='2026-10-02',
        producer_module='src.engine.automation.entry_cancel_wait_tuning', run_id='r1', code_commit='a'*40,
        measurement_complete=True, exit_code=0))+'\n')
    result = _entry_cancel_wait_result_semantics(tmp_path, '2026-10-02')
    assert result['findings'] == ['cancel_wait_completed_report_missing']


def test_cancel_wait_run_keeps_original_source_date_after_midnight(tmp_path, monkeypatch):
    from src.tests.test_entry_cancel_wait_tuning import _reconciliation_fixture
    from src.engine.error_detectors import artifact_freshness as detector
    _reconciliation_fixture(tmp_path,monkeypatch,unknown_history=True)
    status = tmp_path/'data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_2026-10-02.status.json'
    status.parent.mkdir(parents=True)
    status.write_text(json.dumps(dict(target_date='2026-10-02',status='running',run_id='native-1002')))
    original = detector._cancel_wait_monitor_source_date(tmp_path,'2026-10-03')
    assert original == '2026-10-02'
    result = detector._entry_cancel_wait_result_semantics(tmp_path,original,
        datetime(2026,10,3,0,30,tzinfo=ZoneInfo('Asia/Seoul')))
    assert result['source_date'] == '2026-10-02'
    assert result['historical_state'] == 'source_gap'
    assert result['unresolved_prior_custody_count'] is None


@pytest.mark.parametrize('status', ['producers_completed', 'succeeded', 'failed'])
def test_cancel_wait_finished_run_keeps_source_date_and_new_run_takes_precedence(tmp_path, status):
    from src.engine.error_detectors import artifact_freshness as detector
    directory = tmp_path/'data/report/threshold_cycle_postclose_status'
    directory.mkdir(parents=True)
    (directory/'threshold_cycle_postclose_2026-10-02.status.json').write_text(json.dumps(
        dict(target_date='2026-10-02', status=status, run_id='native-1002')))
    assert detector._cancel_wait_monitor_source_date(tmp_path, '2026-10-03') == '2026-10-02'
    (directory/'threshold_cycle_postclose_2026-10-03.status.json').write_text(json.dumps(
        dict(target_date='2026-10-03', status='running', run_id='native-1003')))
    assert detector._cancel_wait_monitor_source_date(tmp_path, '2026-10-03') == '2026-10-03'


def _cancel_wait_consumer_fixture(tmp_path, monkeypatch, status='succeeded'):
    from src.tests.test_entry_cancel_wait_tuning import _reconciliation_fixture
    from src.engine.automation import entry_cancel_wait_tuning as cancel
    from src.engine.automation.postclose_summary_handoff import source_receipt, checklist_marker
    report, policy, rp, pp = _reconciliation_fixture(tmp_path, monkeypatch)
    view = cancel.handoff_view(report, policy, pp)
    receipt = source_receipt({'entry_cancel_wait_tuning':rp, 'entry_cancel_wait_policy':pp}, '2026-10-02')
    paths = {
        'summary':tmp_path/'data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json',
        'tower':tmp_path/'data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-10-02.json',
        'checklist':tmp_path/'docs/checklists/2026-10-06-stage2-todo-checklist.md',
        'native':tmp_path/'data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_2026-10-02.status.json',
    }
    for path in paths.values(): path.parent.mkdir(parents=True, exist_ok=True)
    paths['summary'].write_text(json.dumps(dict(date='2026-10-02', sources={'entry_cancel_wait':dict(
        sha256=receipt['sources']['entry_cancel_wait_tuning']['sha256'],
        economic_evidence={'cancel_wait_reconciliation':view['reconciliation']})})))
    receipt = source_receipt({'entry_cancel_wait_tuning':rp, 'entry_cancel_wait_policy':pp,
        'runtime_approval_summary':paths['summary']}, '2026-10-02')
    paths['tower'].write_text(json.dumps(dict(date='2026-10-02', entry_cancel_wait_economic_tuning=view,
        source_generation_contract=receipt)))
    paths['checklist'].write_text(checklist_marker(receipt)+'\n'+cancel.checklist_handoff(view))
    paths['native'].write_text(json.dumps(dict(target_date='2026-10-02',status=status,run_id='native-1002')))
    return paths


@pytest.mark.parametrize('stage,mutation', [(stage, mutation)
    for stage in ('summary', 'tower', 'checklist') for mutation in ('missing', 'stale', 'wrong_date', 'malformed')]
    + [('checklist', 'duplicate'), ('summary', 'changed_bytes')])
def test_cancel_wait_finished_consumers_cannot_remain_pending(tmp_path, monkeypatch, stage, mutation):
    from src.engine.error_detectors import artifact_freshness as detector
    paths = _cancel_wait_consumer_fixture(tmp_path, monkeypatch)
    path = paths[stage]
    if mutation == 'missing':
        path.unlink()
    elif mutation == 'malformed':
        path.write_text('<!-- POSTCLOSE_SUMMARY_SOURCES {invalid} -->' if stage == 'checklist' else '{invalid}')
    elif mutation == 'changed_bytes':
        path.write_text(path.read_text()+'\n')
    elif stage == 'checklist':
        text = path.read_text()
        text = (text.replace('entry_cancel_wait_handoff_sha256:', 'stale_handoff_sha256:') if mutation == 'stale'
                else text.replace('"source_date": "2026-10-02"', '"source_date": "2026-10-01"') if mutation == 'wrong_date'
                else text+'\n<!-- entry_cancel_wait_handoff:start -->\n<!-- entry_cancel_wait_handoff:end -->')
        path.write_text(text)
    else:
        value = json.loads(path.read_text())
        if mutation == 'wrong_date': value['date'] = '2026-10-01'
        elif stage == 'summary':
            value['sources']['entry_cancel_wait']['sha256'] = 'a'*64
        else:
            value['source_generation_contract']['sources']['entry_cancel_wait_tuning']['sha256'] = 'a'*64
        path.write_text(json.dumps(value))
    result = detector._entry_cancel_wait_result_semantics(tmp_path, '2026-10-02')
    assert result['status'] == 'source_invalid'
    assert 'cancel_wait_consumer_projection_invalid' in result['findings']


def test_cancel_wait_running_consumers_are_pending_then_verified(tmp_path, monkeypatch):
    from src.engine.error_detectors import artifact_freshness as detector
    paths = _cancel_wait_consumer_fixture(tmp_path, monkeypatch, status='running')
    text = paths['checklist'].read_text()
    paths['checklist'].unlink()
    result = detector._entry_cancel_wait_result_semantics(tmp_path, '2026-10-02')
    assert result['findings'] == []
    assert result['consumers']['status'] == 'pending'
    paths['checklist'].write_text(text)
    result = detector._entry_cancel_wait_result_semantics(tmp_path, '2026-10-02')
    assert result['findings'] == []
    assert result['consumers']['status'] == 'verified'


@pytest.mark.parametrize('stage', ['summary', 'tower', 'checklist', 'native', 'report', 'registry', 'removed', 'malformed_during_read'])
def test_cancel_wait_generation_change_during_consumer_read_is_unobservable(tmp_path, monkeypatch, stage):
    from src.engine.error_detectors import artifact_freshness as detector
    from src.tests.test_entry_cancel_wait_tuning import _append_registry_event
    paths = _cancel_wait_consumer_fixture(tmp_path,monkeypatch)
    paths['report'] = tmp_path/'data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-02.json'
    paths['registry'] = tmp_path/'data/runtime/order_owner_registry.jsonl'
    original_reader = detector._semantic_object
    mutated = False
    def reader(path, **kwargs):
        nonlocal mutated
        if path == paths['summary'] and not kwargs.get('hash_only') and not mutated and stage in {'removed', 'malformed_during_read'}:
            mutated = True
            if stage == 'removed': path.unlink()
            else: path.write_text('{invalid}')
        value = original_reader(path, **kwargs)
        if path == paths['summary'] and not kwargs.get('hash_only') and not mutated:
            mutated = True
            if stage == 'registry':
                _append_registry_event(paths['registry'], owner_type='main_scalping', day='2026-10-01')
            else:
                changed = paths[stage]
                changed.write_text(changed.read_text()+'\n')
        return value
    monkeypatch.setattr(detector,'_semantic_object',reader)
    result = detector._entry_cancel_wait_result_semantics(tmp_path,'2026-10-02')
    assert mutated
    assert result['status'] == 'unobservable'
    assert result['findings'] == []
    assert detector._semantic_alerts('entry_cancel_wait_tuning', result, '2026-10-02') == []


def test_cancel_wait_consumer_error_preserves_known_reuse_finding(tmp_path, monkeypatch):
    from src.engine.error_detectors import artifact_freshness as detector
    paths = _cancel_wait_consumer_fixture(tmp_path, monkeypatch)
    report = tmp_path/'data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-02.json'
    report.with_suffix('.reuse-contract.json').write_text(json.dumps({'artifact_sha256':'invalid'}))
    paths['summary'].write_text('{invalid}')
    result = detector._entry_cancel_wait_result_semantics(tmp_path,'2026-10-02')
    assert result['status'] == 'source_invalid'
    assert set(result['findings']) == {'cancel_wait_reuse_generation_invalid', 'cancel_wait_consumer_projection_invalid'}


@pytest.mark.parametrize("defect", [None, "enum", "generation", "cutoff", "missing"])
def test_holding_semantics_v2_pending_submit_is_valid_and_malformed_contract_rejected(tmp_path, defect):
    from src.tests.test_holding_exit_sentinel import _semantic_flow
    from src.engine.scalping.holding_profit_exit_semantics import audit_profit_exit_flow
    event, mechanical, rows, lineage, at = _semantic_flow()
    rows.append(event(2, "exit_signal", lineage))
    semantics = audit_profit_exit_flow(rows, target_date="2026-10-09", load_votes=lambda _: [],
                                      mechanical_policy_receipt=mechanical, consumed_pid=42)
    report = {"target_date": "2026-10-09", "as_of": semantics["as_of"],
              "source_generation": semantics["source_generation"], "profit_exit_semantics": semantics}
    if defect == "enum": semantics["lifecycle"][0]["lifecycle_state"] = "silent_success"
    if defect == "generation": report["source_generation"] = "b" * 64
    if defect == "cutoff": semantics["as_of"] = "2026-10-10T10:00:00+09:00"
    if defect == "missing": semantics.pop("economics_status")
    path = tmp_path / "data/report/holding_exit_sentinel/holding_exit_sentinel_2026-10-09.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(report))
    result = _holding_profit_exit_semantics(tmp_path, "2026-10-09")
    if defect:
        assert result["status"] == "source_invalid"
    else:
        assert result["status"] == "pending_submit"
        assert result["findings"] == []
        assert result["lifecycle_verified"] is True
        assert result["lifecycle_counts"] == {"pending_submit": 1}


def test_cancel_wait_semantics_accepts_attested_shared_data_mount(tmp_path, monkeypatch):
    from src.engine.error_detectors import artifact_freshness as mod
    workspace=tmp_path/'workspace';workspace.mkdir()
    _cancel_wait_consumer_fixture(workspace,monkeypatch)
    release=tmp_path/'release';release.mkdir()
    (release/'data').symlink_to(workspace/'data',target_is_directory=True)
    (release/'docs').symlink_to(workspace/'docs',target_is_directory=True)
    result=mod._entry_cancel_wait_result_semantics(release,'2026-10-02')
    assert result['findings']==[]
    assert result['runtime_effect'] is False


def test_main_stop_semantics_uses_physical_data_without_changing_code_root(tmp_path, monkeypatch):
    from src.engine.error_detectors import artifact_freshness as mod
    from src.engine.automation import main_stop_postclose as stop
    data=tmp_path/'workspace/data';data.mkdir(parents=True)
    release=tmp_path/'release';release.mkdir();(release/'data').symlink_to(data,target_is_directory=True)
    path=stop.committed_path(data,'2026-10-12');path.parent.mkdir(parents=True);path.write_text('{}')
    seen=[]
    def read(root,day):
        seen.append(root)
        assert root==data.resolve()
        return {'target_date':'2026-10-13','policy_sha256':'a'*64,'cells':{'c':{'status':'incumbent_carry'}}},{},{'generation':'b'*64},path.parent
    monkeypatch.setattr(stop,'read_committed',read)
    monkeypatch.setattr(stop,'runtime_consumption',lambda root,bundle:{'actual_pid_consumed':False,'findings':[]})
    result=mod._main_stop_semantics(release,'2026-10-12',now=datetime(2026,10,13,tzinfo=ZoneInfo('Asia/Seoul')))
    assert seen==[data.resolve()]
    assert result['status']=='published_policy' and result['findings']==[]
    assert result['actual_pid_consumed'] is False


def test_generation_detector_preserves_release_code_root_and_canonical_data(tmp_path, monkeypatch):
    from src.engine.error_detectors import artifact_freshness as mod
    from src.engine.monitoring import policy_generation_contract as generation
    data=tmp_path/'workspace/data';data.mkdir(parents=True)
    release=tmp_path/'release';release.mkdir();(release/'data').symlink_to(data,target_is_directory=True)
    class Clock(datetime):
        @classmethod
        def now(cls,tz=None):return cls(2026,10,13,6,25,tzinfo=ZoneInfo('Asia/Seoul'))
    monkeypatch.setattr(mod,'datetime',Clock)
    monkeypatch.setattr(mod,'PROJECT_ROOT',release)
    monkeypatch.setattr(mod,'ARTIFACT_REGISTRY',[])
    monkeypatch.setattr(mod,'is_krx_trading_day',lambda *_:True)
    monkeypatch.setattr(mod,'load_installed_crontab',lambda:'')
    seen=[]
    def observe(root,day,*,data_root=None):
        seen.append((root,data_root));return []
    monkeypatch.setattr(generation,'observations',observe)
    mod.ArtifactFreshnessDetector(dry_run=True).check()
    assert seen and all(root==release and actual==data.resolve() for root,actual in seen)


def _startup_observer_fixture(tmp_path, monkeypatch):
    import src.engine.error_detectors.artifact_freshness as mod
    now = datetime.fromisoformat("2026-10-14T14:42:00+09:00")
    root = tmp_path.resolve(); data = root / "data"; data.mkdir()
    release = root / "release"; release.mkdir()
    day = "2026-10-14"; commit = "b" * 40
    report_path = data / "report/buy_funnel_sentinel" / f"submission_bottleneck_monitor_{day}.json"
    report_path.parent.mkdir(parents=True)
    report = dict(schema="submission_bottleneck_monitor_v1", date=day,
        as_of=f"{day}T14:34:40+09:00", run_id="d" * 32,
        execution_status="completed", semantic_status="partial", notification_status="idle",
        status="unobservable", blocker="prior_real_source_gap")
    report_path.write_text(json.dumps(report))
    old_epoch = datetime.fromisoformat(f"{day}T14:34:45+09:00").timestamp()
    os.utime(report_path, (old_epoch, old_epoch))
    identity = dict(pid=42, start_ticks="123", cwd=str(release / "src"))
    monkeypatch.setattr(mod, "_observer_live_identity", lambda pid: dict(identity))
    transition_path = data / "runtime/release_transitions" / day / commit / "status.json"
    transition_path.parent.mkdir(parents=True)
    transition = dict(schema="ordered_intraday_deployment_v1", authority="APPROVED_ORDERED_INTRADAY_DEPLOY_AND_RESTART",
        target_date=day, candidate_commit=commit, candidate_root=str(release), policy_effect="unchanged",
        phase="complete", status="pass", updated_at=f"{day}T14:37:18+09:00", successor_identity=identity,
        predecessor_observer=dict(schema="startup_observer_predecessor_v1", status="captured", path=str(report_path),
            sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(), mtime_ns=report_path.stat().st_mtime_ns,
            **{key: report[key] for key in ("date", "as_of", "run_id", "execution_status", "semantic_status")}))
    transition_path.write_text(json.dumps(transition))
    selection_path = data / "runtime/runtime_release_selection.json"
    selection = dict(schema="runtime_release_selection_v1", git_commit=commit, release_root=str(release),
        selected_at_kst=f"{day}T14:35:38+09:00", deployment_transition=str(transition_path),
        approval_scope="ordered_intraday_deploy_and_restart", approved_by="user", actual_pid_consumed=True,
        actual_pid_receipt=dict(schema="runtime_release_pid_receipt_v1", git_commit=commit,
            release_root=str(release), pid=42, start_ticks='123', process_cwd=str(release / "src")))
    selection_path.write_text(json.dumps(selection))
    return mod, root, now, report_path, report, transition_path, transition, selection_path, selection


def test_exact_captured_old_observer_is_bounded_pending_without_new_pass(tmp_path, monkeypatch):
    mod, root, now, report_path, report, *_ = _startup_observer_fixture(tmp_path, monkeypatch)
    before = report_path.read_bytes()
    pending = mod._submission_observer_transition_pending(root, report_path, now, max_staleness_sec=600)
    assert pending["status"] == "pending_first_current_observer"
    assert pending["deadline"] == "2026-10-14T14:43:00+09:00"
    assert pending["prior_semantic_status"] == "partial"
    assert pending["prior_blocker"] == "prior_real_source_gap"
    assert pending["current_observation_verified"] is False
    assert pending["runtime_effect"] is False and pending["allowed_runtime_apply"] is False
    assert report_path.read_bytes() == before
    assert mod._submission_observer_transition_pending(root, report_path,
        datetime.fromisoformat("2026-10-14T14:43:01+09:00"), max_staleness_sec=600) is None


@pytest.mark.parametrize("change", ["capture_absent", "capture_sha", "capture_path", "capture_mtime", "capture_clock",
    "capture_partial_lost", "transition_failed", "transition_starting", "transition_wrong_root", "selection_wrong_commit",
    "selection_unapproved", "selection_pid_missing", "receipt_start_changed", "pid_changed", "stale", "failed", "malformed", "new_current", "replaced_same_bytes"])
def test_pending_never_suppresses_unproven_failed_stale_or_current_report(tmp_path, monkeypatch, change):
    fixture = _startup_observer_fixture(tmp_path, monkeypatch)
    mod, root, now, path, report, tp, transition, sp, selection = fixture
    if change == "capture_absent": transition.pop("predecessor_observer")
    elif change == "capture_sha": transition["predecessor_observer"]["sha256"] = "0" * 64
    elif change == "capture_path": transition["predecessor_observer"]["path"] = str(path.with_name("latest.json"))
    elif change == "capture_mtime": transition["predecessor_observer"]["mtime_ns"] += 1
    elif change == "capture_clock": transition["predecessor_observer"]["as_of"] = "wrong"
    elif change == "capture_partial_lost": transition["predecessor_observer"]["semantic_status"] = "validated"
    elif change == "transition_failed": transition.update(status="fail", phase="failed")
    elif change == "transition_starting": transition["phase"] = "starting"
    elif change == "transition_wrong_root": transition["candidate_root"] = str(root / "wrong")
    elif change == "selection_wrong_commit": selection["git_commit"] = "c" * 40
    elif change == "selection_unapproved": selection["approval_scope"] = "unknown"
    elif change == "selection_pid_missing": selection["actual_pid_consumed"] = False
    elif change == 'receipt_start_changed': selection['actual_pid_receipt']['start_ticks']='999'
    elif change == "pid_changed": monkeypatch.setattr(mod, "_observer_live_identity", lambda pid: {"pid": 99})
    elif change == "stale": os.utime(path, (datetime.fromisoformat(transition['updated_at']).timestamp() - 601,) * 2)
    elif change == "failed": report["execution_status"] = "failed"
    elif change == "malformed": path.write_text("{bad")
    elif change == "new_current": report["as_of"] = "2026-10-14T14:41:19+09:00"
    elif change == "replaced_same_bytes": path.write_bytes(path.read_bytes())
    tp.write_text(json.dumps(transition)); sp.write_text(json.dumps(selection))
    if change in {"failed", "new_current"}: path.write_text(json.dumps(report))
    assert mod._submission_observer_transition_pending(root, path, now, max_staleness_sec=600) is None


def test_current_partial_keeps_original_failure_and_generation_loss_cannot_pass(tmp_path, monkeypatch):
    fixture = _current_observer_fixture(tmp_path, monkeypatch)
    mod, root, now, path, report, *_ = fixture
    monkeypatch.setattr(mod, "PROJECT_ROOT", root)
    artifact = dict(id="submission_bottleneck_monitor", json_status_field="notification_status",
                    json_ok_values=["idle", "sent", "cooldown"])
    assert "semantic coverage partial" in mod.ArtifactFreshnessDetector._validate_json_status(artifact, path, {})
    report["semantic_status"] = "validated"; report.pop('observer_generation'); path.write_text(json.dumps(report))
    assert "observer_generation_missing" in mod.ArtifactFreshnessDetector._validate_json_status(artifact, path, {})


def _current_observer_fixture(tmp_path, monkeypatch):
    from src.engine.monitoring import submission_bottleneck_monitor as monitor
    fixture = _startup_observer_fixture(tmp_path, monkeypatch)
    mod, root, now, path, report, _, _, selector_path, selection = fixture
    monkeypatch.setattr(mod, 'PROJECT_ROOT', root)
    code_path = Path(selection['release_root']) / 'src/engine/monitoring/submission_bottleneck_monitor.py'
    code_path.parent.mkdir(parents=True); code_path.write_bytes(b'reviewed immutable observer\n')
    code = dict(release_root=selection['release_root'], git_commit=selection['git_commit'],
                observer_code_sha256=hashlib.sha256(code_path.read_bytes()).hexdigest())
    monkeypatch.setattr(monitor, '_observer_code_identity', lambda: dict(code))
    selection['actual_pid_receipt']['start_ticks']='123'
    selector_path.write_text(json.dumps(selection))
    report.update(as_of=(now-timedelta(seconds=30)).isoformat(), blocker='missing_stale_or_noncurrent_sentinel_evidence',
                  source_as_of='2026-10-14T08:00:00+09:00',
                  source_gap_semantics=dict(status='unobservable',sources=dict(probe=dict(status='complete', recent_count=0))),
                  machine_semantics=dict(status='unobservable'), entry_execution_tuning_semantics=dict(status='observed'))
    original = monitor._observer_generation_snapshot(root, run_id=report['run_id'], target_date=report['date'],
        started_at=datetime.fromisoformat(report['as_of']))
    report['observer_generation'] = monitor._finish_observer_generation(original, root, completed_at=now-timedelta(seconds=20))
    path.write_text(json.dumps(report)); os.utime(path, ((now-timedelta(seconds=20)).timestamp(),)*2)
    return fixture


def _isolate_submission_artifact_check(mod, root, now, monkeypatch):
    from src.engine.monitoring import policy_generation_contract
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None): return now if tz else now.replace(tzinfo=None)
    monkeypatch.setattr(mod, 'datetime', Clock)
    monkeypatch.setattr(mod.time, 'time', lambda: now.timestamp())
    monkeypatch.setattr(mod, 'PROJECT_ROOT', root)
    monkeypatch.setattr(mod, 'ARTIFACT_REGISTRY', [r for r in ARTIFACT_REGISTRY if r['id']=='submission_bottleneck_monitor'])
    monkeypatch.setattr(mod, 'is_krx_trading_day', lambda *args: True)
    monkeypatch.setattr(mod, 'load_installed_crontab', lambda: '')
    for name in ('_entry_cancel_wait_result_semantics', '_holding_profit_exit_semantics', '_machine_result_semantics',
                 '_auxiliary_result_semantics', '_postclose_handoff_semantics', '_main_stop_semantics', '_samsung_forward_semantics',
                 '_initial_quantity_semantics'):
        monkeypatch.setattr(mod, name, lambda *args, **kwargs: dict(status='not_assessed',findings=[]))
    monkeypatch.setattr(mod, '_completed_semantic_source', lambda *args: dict(status='not_assessed',findings=[],target_date=None))
    monkeypatch.setattr(mod, '_current_semantic_owners', lambda *args: set())
    monkeypatch.setattr(policy_generation_contract, 'observations', lambda *args, **kwargs: [])
    monkeypatch.setattr(policy_generation_contract, 'retirement_dispositions', lambda *args, **kwargs: [])


@pytest.mark.parametrize('stale,wrong_generation', [(False,False),(True,False),(False,True),(True,True)])
def test_observer_dimensions_expose_freshness_generation_and_actual_source_gap(tmp_path, monkeypatch, stale, wrong_generation):
    mod, root, now, path, report, _, _, selector_path, selector = _current_observer_fixture(tmp_path, monkeypatch)
    if stale: os.utime(path, (now.timestamp()-1801,)*2)
    if wrong_generation: selector_path.write_text(json.dumps({**selector,'actual_pid_consumed':False}))
    _isolate_submission_artifact_check(mod, root, now, monkeypatch)
    result = mod.ArtifactFreshnessDetector(dry_run=True).check()
    dims = result.details['submission_bottleneck_monitor_observation_dimensions']
    assert result.severity == 'fail'
    assert dims['freshness']['status'] == ('stale' if stale else 'fresh')
    assert dims['freshness']['max_staleness_sec'] == 600
    assert dims['generation']['status'] == ('observer_generation_not_current' if wrong_generation else 'current')
    assert dims['semantic'] == 'partial' and dims['execution'] == 'completed'
    assert dims['source']['blocker'] == 'missing_stale_or_noncurrent_sentinel_evidence'
    assert dims['source']['inherited_source_as_of_is_upstream_clock'] is False
    assert 'upstream_age_sec' not in dims['source']
    assert dims['report']['byte_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert dims['report']['run_id'] == report['run_id']
    if stale:
        assert 'submission_bottleneck_monitor: stale (1801s > 600s)' in result.summary
    elif wrong_generation:
        assert 'observer_generation_not_current' in result.summary
    else:
        assert 'blocker=missing_stale_or_noncurrent_sentinel_evidence' in result.summary
        assert 'machine_semantics=unobservable' in result.summary


def test_observer_partial_legacy_generation_does_not_claim_current_proof(tmp_path, monkeypatch):
    mod, root, _, path, report, *_ = _startup_observer_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(mod, 'PROJECT_ROOT', root)
    report['date']='2026-10-13'; path.write_text(json.dumps(report))
    details={}
    mod.ArtifactFreshnessDetector._validate_json_status(dict(id='submission_bottleneck_monitor',json_status_field='notification_status'),path,details)
    generation=details['submission_bottleneck_monitor_observation_dimensions']['generation']
    assert generation == dict(status='legacy_generation_unverified',current_generation_verified=False)


def test_observer_partial_reason_distinguishes_scanner_cohort_main_and_actual_health_failure(tmp_path):
    from src.engine.error_detectors import artifact_freshness as mod
    payload=dict(evaluation_cohort='scanner_promotions',blocker='no_identified_scanner_machine_evaluation',
        identity_observation={'identified_event_count':0,'window_sec':600},
        fixed_watch_identity_observation={'identified_event_count':204,'window_policy':'current_45_minutes'},
        source_gap_semantics={'status':'gap_observed','sources':{'probe':
            {'status':'partial','window_covered':False,'first_read_at':'2026-10-14T18:31:39+09:00'}}})
    dimensions=mod._submission_observer_dimensions(payload,tmp_path/'report.json','a'*64)
    dimensions['observation_health']={'unmet_conditions':['source_window_not_complete:probe',
        'pending_or_withheld_auxiliary_pass_not_quiet']}
    reason=mod._submission_observer_partial_reason(dimensions)
    assert reason.startswith('health_unmet=source_window_not_complete:probe')
    assert 'evaluation_cohort=scanner_promotions' in reason
    assert 'scanner_identified_events=0' in reason and 'fixed_watch_identified_events=204' in reason
    assert dimensions['source']['cohorts']['fixed_watch_identity_observation']['window_policy']=='current_45_minutes'
    assert dimensions['source']['stages']['source_gap_semantics']['sources']['probe']['window_covered'] is False


def test_observer_snapshot_change_cannot_inherit_status_or_generation(tmp_path, monkeypatch):
    mod, _, _, path, _, *_ = _current_observer_fixture(tmp_path, monkeypatch)
    snapshot = mod._submission_observer_snapshot(path)
    path.write_bytes(path.read_bytes())
    result=mod.ArtifactFreshnessDetector._validate_json_status(
        dict(id='submission_bottleneck_monitor',json_status_field='notification_status'),path,{},observer_snapshot=snapshot)
    assert 'observer_report_changed_after_snapshot' in result
    snapshot=mod._submission_observer_snapshot(path)
    def changed(*args):
        path.unlink()
        return None
    monkeypatch.setattr(mod,'_submission_observer_generation_issue',changed)
    result=mod.ArtifactFreshnessDetector._validate_json_status(
        dict(id='submission_bottleneck_monitor',json_status_field='notification_status'),path,{},observer_snapshot=snapshot)
    assert 'observer_report_changed_after_snapshot' in result


def test_current_observer_diagnostics_reuse_one_bounded_report_snapshot(tmp_path, monkeypatch):
    mod,root,now,path,*_ = _current_observer_fixture(tmp_path,monkeypatch)
    _isolate_submission_artifact_check(mod,root,now,monkeypatch)
    original=mod._observer_small_object
    reads=[]
    def read(candidate,**kwargs):
        if Path(candidate)==path: reads.append(candidate)
        return original(candidate,**kwargs)
    monkeypatch.setattr(mod,'_observer_small_object',read)
    outcome=mod.ArtifactFreshnessDetector(dry_run=True).check()
    assert outcome.severity=='fail'
    assert len(reads)==1


def _quiet_current_observer_fixture(tmp_path, monkeypatch, *, payload_factory=None):
    from src.tests.test_submission_bottleneck_monitor import _observation_health_fixture
    from src.engine.monitoring import submission_bottleneck_monitor as monitor
    mod,root,_,path,report,tp,transition,sp,selection = _current_observer_fixture(tmp_path,monkeypatch)
    report.clear(); report.update((payload_factory or _observation_health_fixture)())
    lineage=report['machine_semantics'].get('reversal_provider_lineage')
    if lineage:
        pid,ticks=lineage['exact_pid_filter']
        selection['actual_pid_receipt'].update(pid=int(pid),start_ticks=ticks)
        sp.write_text(json.dumps(selection))
        monkeypatch.setattr(mod,'_observer_live_identity',lambda actual:dict(pid=actual,start_ticks=ticks,cwd=selection['actual_pid_receipt']['process_cwd']))
    now=datetime.fromisoformat(report['as_of'])+timedelta(seconds=20)
    def seal():
        original=monitor._observer_generation_snapshot(root,run_id=report['run_id'],target_date=report['date'],
            started_at=datetime.fromisoformat(report['as_of']))
        report['observer_generation']=monitor._finish_observer_generation(original,root,completed_at=now-timedelta(seconds=10))
        report['observation_health']=monitor.observation_health_projection(report)
        path.write_text(json.dumps(report));os.utime(path,(now.timestamp()-10,)*2)
    seal()
    _isolate_submission_artifact_check(mod,root,now,monkeypatch)
    return mod,root,now,path,report,sp,selection,seal


def test_exact_quiet_window_warns_without_pass_recovery_or_erasing_source_gaps(tmp_path,monkeypatch):
    from src.engine.error_detector import iter_daemon_alert_events
    from src.engine.error_detectors.base import DetectionResult
    mod,root,now,path,report,*_ = _quiet_current_observer_fixture(tmp_path,monkeypatch)
    before=path.read_bytes()
    result=mod.ArtifactFreshnessDetector(dry_run=True).check()
    assert result.severity=='warning' and 'observation pending' in result.summary
    assert result.details['submission_bottleneck_monitor_status']=='pending_no_applicable_observations'
    assert result.details['submission_bottleneck_monitor_observation_health_projection_match'] is True
    assert result.details['submission_bottleneck_monitor_current_observation_verified'] is False
    assert result.details['submission_bottleneck_monitor_semantic_status']=='partial'
    source=result.details['submission_bottleneck_monitor_observation_dimensions']['source']
    assert source['input_provenance']['snapshot_as_of']=='2026-10-14T15:35:12.585430+09:00'
    assert source['inherited_source_as_of']=='2026-10-14T15:15:18.387222+09:00'
    assert source['inherited_source_as_of_is_upstream_clock'] is False
    health=result.details['submission_bottleneck_monitor_observation_health']
    assert health['full_coverage_proven'] is False and health['runtime_effect'] is False
    assert path.read_bytes()==before and report['status']=='unobservable'
    assert report['entry_execution_tuning_semantics']['entry_split']['status']=='source_gap'
    assert report['entry_execution_tuning_semantics']['entry_split']['primary_operating_ev_pct'] is None
    state={}
    prior=DetectionResult(detector_id='artifact_freshness',category='artifact',severity='fail',summary='prior genuine failure')
    assert len(list(iter_daemon_alert_events([prior],state,target_date='2026-10-14')))==1
    assert list(iter_daemon_alert_events([result],state,target_date='2026-10-14'))==[]
    assert 'artifact_freshness' in state


@pytest.mark.parametrize('wrong_actor', [False, True])
def test_current_health_cohort_uses_selected_actor_without_rewriting_old_pid_history(tmp_path,monkeypatch,wrong_actor):
    import copy
    from src.engine.monitoring import submission_bottleneck_monitor as monitor
    mod,root,now,path,report,_,selection,seal=_quiet_current_observer_fixture(tmp_path,monkeypatch)
    receipt=selection['actual_pid_receipt']
    actor=[str(receipt['pid']),receipt['start_ticks']]
    original_machine=copy.deepcopy(report['machine_semantics'])
    for key in ('source_gap_semantics','machine_semantics'):
        view=copy.deepcopy(report[key])
        report[key]['current_health_cohort']=monitor._health_cohort(
            view, ['999999',actor[1]] if wrong_actor else actor,
            datetime.fromisoformat(report['as_of']),excluded=7)
    old_lineage=dict(exact_pid_filter=['111111','222222'],attempt_ledger=[dict(producer_pid='111111')])
    report['machine_semantics']['reversal_provider_lineage']=old_lineage
    seal()
    outcome=mod.ArtifactFreshnessDetector(dry_run=True).check()
    assert outcome.severity==('fail' if wrong_actor else 'warning')
    assert report['machine_semantics']['reversal_provider_lineage']==old_lineage
    assert report['machine_semantics']['current_health_cohort']['view']==original_machine
    if wrong_actor:
        assert 'current_health_actor_not_selected_pid' in outcome.details['submission_bottleneck_monitor_observation_health']['unmet_conditions']
    else:
        assert outcome.details['submission_bottleneck_monitor_status']=='pending_no_applicable_observations'
        assert outcome.details['submission_bottleneck_monitor_current_observation_verified'] is False


@pytest.mark.parametrize('healthy',[False,True])
def test_recorded_guard_and_healthy_fixed_nonentry_warn_without_fullpass_or_recovery(tmp_path,monkeypatch,healthy):
    from src.tests.test_submission_bottleneck_monitor import _recorded_guard_health_fixture
    from src.engine.error_detector import iter_daemon_alert_events
    from src.engine.error_detectors.base import DetectionResult
    mod,root,now,path,report,*_=_quiet_current_observer_fixture(tmp_path,monkeypatch,
        payload_factory=lambda:_recorded_guard_health_fixture(healthy=healthy))
    before=path.read_bytes()
    outcome=mod.ArtifactFreshnessDetector(dry_run=True).check()
    assert outcome.severity=='warning'
    assert outcome.details['submission_bottleneck_monitor_status']=='pending_bounded_observation'
    assert 'recorded_guard_or_cohort_pending' in outcome.summary
    assert outcome.details['submission_bottleneck_monitor_current_observation_verified'] is False
    assert outcome.details['submission_bottleneck_monitor_semantic_status']=='partial'
    assert report['status']=='unobservable' and path.read_bytes()==before
    assert report['entry_execution_tuning_semantics']['entry_split']['status']=='source_gap'
    assert report['entry_execution_tuning_semantics']['entry_split']['primary_operating_ev_pct'] is None
    machine=outcome.details['submission_bottleneck_monitor_observation_dimensions']['source']['stages']['machine_semantics']
    assert machine['source_invalid_count']==(0 if healthy else 2)
    state={};prior=DetectionResult(detector_id='artifact_freshness',category='artifact',severity='fail',summary='prior actual failure')
    assert len(list(iter_daemon_alert_events([prior],state,target_date='2026-10-14')))==1
    assert list(iter_daemon_alert_events([outcome],state,target_date='2026-10-14'))==[]
    assert 'artifact_freshness' in state


@pytest.mark.parametrize('damage',['unknown_diagnostic','actual_path_conflict','foreign_lineage'])
def test_recorded_guard_warning_never_hides_unknown_or_actual_conflict_or_foreign_pid(tmp_path,monkeypatch,damage):
    from src.tests.test_submission_bottleneck_monitor import _recorded_guard_health_fixture
    mod,root,now,path,report,_,_,seal=_quiet_current_observer_fixture(tmp_path,monkeypatch,payload_factory=_recorded_guard_health_fixture)
    if damage=='unknown_diagnostic':
        report['source_gap_semantics']['diagnostics']={'machine_probe:unknown_contract_error':2}
    elif damage=='actual_path_conflict':
        report['source_gap_semantics']['issues']={'machine_trace:path_auxiliary_feature_input_conflict':10}
    else:
        lineage=report['machine_semantics']['reversal_provider_lineage']
        lineage['exact_pid_filter'][0]='999999'
        for row in lineage['attempt_ledger']:row['producer_pid']='999999'
    seal()
    outcome=mod.ArtifactFreshnessDetector(dry_run=True).check()
    assert outcome.severity=='fail'
    assert outcome.details['submission_bottleneck_monitor_status']=='fail'
    if damage=='foreign_lineage':assert 'observer_current_main_lineage_mismatch' in outcome.summary
    elif damage=='actual_path_conflict':assert 'path_auxiliary_feature_input_conflict' in outcome.summary


@pytest.mark.parametrize('damage', ['missing_projection','mismatched_projection','source_gap','missing_reader','deferred',
    'stale_input','stale_report','future_report','wrong_generation','unattested_actor','dead_actor','reused_actor','malformed_actor'])
def test_quiet_warning_never_hides_real_failure_or_missing_current_actor(tmp_path,monkeypatch,damage):
    mod,root,now,path,report,sp,selection,seal = _quiet_current_observer_fixture(tmp_path,monkeypatch)
    if damage=='missing_projection': report.pop('observation_health')
    elif damage=='mismatched_projection': report['observation_health']['reason']='forged'
    elif damage=='source_gap': report['source_gap_semantics']['issues']['machine_probe:0B_missing']=1
    elif damage=='missing_reader': report['source_gap_semantics']['sources'].pop('trace')
    elif damage=='deferred': report['execution_status']='deferred'
    elif damage=='stale_input': report['input_provenance']['snapshot_age_seconds']=999
    elif damage in {'wrong_generation','unattested_actor'}:
        selection['actual_pid_consumed']=False;sp.write_text(json.dumps(selection))
        if damage=='unattested_actor': seal()
    elif damage=='dead_actor':
        def absent(pid): raise FileNotFoundError('dead test child')
        monkeypatch.setattr(mod,'_observer_live_identity',absent)
    elif damage=='reused_actor': monkeypatch.setattr(mod,'_observer_live_identity',lambda pid:dict(pid=pid,start_ticks='999',cwd=selection['actual_pid_receipt']['process_cwd']))
    elif damage=='malformed_actor':
        selection['actual_pid_receipt']['pid']='../../not-a-pid';sp.write_text(json.dumps(selection));seal()
        monkeypatch.setattr(mod,'_observer_live_identity',lambda *args:pytest.fail('malformed PID reached proc'))
    if damage in {'source_gap','missing_reader','deferred','stale_input'}: seal()
    else: path.write_text(json.dumps(report));os.utime(path,(now.timestamp()-10,)*2)
    if damage=='stale_report': os.utime(path,(now.timestamp()-601,)*2)
    elif damage=='future_report': os.utime(path,(now.timestamp()+0.05,)*2)
    outcome=mod.ArtifactFreshnessDetector(dry_run=True).check()
    assert outcome.severity=='fail'
    assert outcome.details['submission_bottleneck_monitor_status']=='fail'
    if damage in {'stale_report','future_report','wrong_generation'}:
        assert 'submission_bottleneck_monitor_observation_health' not in outcome.details


def test_exact_prior_fresh_at_completion_may_age_only_through_first_slot_budget(tmp_path, monkeypatch):
    mod,root,now,path,report,tp,transition,*_ = _startup_observer_fixture(tmp_path,monkeypatch)
    complete=datetime.fromisoformat(transition['updated_at'])
    mtime=complete.timestamp()-590
    report['as_of']=datetime.fromtimestamp(mtime-10,now.tzinfo).isoformat()
    path.write_text(json.dumps(report));os.utime(path,(mtime,mtime))
    transition['predecessor_observer'].update(mtime_ns=path.stat().st_mtime_ns,as_of=report['as_of'],
        sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    tp.write_text(json.dumps(transition))
    pending=mod._submission_observer_transition_pending(root,path,now,max_staleness_sec=600)
    assert pending['prior_stale_retained'] is True
    assert pending['age_at_completion_sec']==590
    assert pending['freshness_at_completion']=='fresh'
    assert pending['deadline']==pending['cron_deadline']=='2026-10-14T14:43:00+09:00'
    assert pending['current_observation_verified'] is False
    _isolate_submission_artifact_check(mod,root,now,monkeypatch)
    actual=mod.ArtifactFreshnessDetector(dry_run=True).check()
    assert actual.severity=='warning'
    assert actual.details['submission_bottleneck_monitor_status']=='pending_first_current_observer'
    assert actual.details['submission_bottleneck_monitor_transition']['prior_stale_retained'] is True
    assert mod._submission_observer_transition_pending(root,path,datetime.fromisoformat(pending['deadline'])+timedelta(microseconds=1),max_staleness_sec=600) is None
    os.utime(path,(complete.timestamp()-601,)*2);transition['predecessor_observer']['mtime_ns']=path.stat().st_mtime_ns
    tp.write_text(json.dumps(transition))
    assert mod._submission_observer_transition_pending(root,path,now,max_staleness_sec=600) is None


@pytest.mark.parametrize('change',['selector','report'])
def test_quiet_warning_rechecks_exact_generation_after_live_actor_read(tmp_path,monkeypatch,change):
    mod,root,now,path,report,sp,selection,_ = _quiet_current_observer_fixture(tmp_path,monkeypatch)
    def identity(pid):
        if change=='selector': sp.write_text(json.dumps({**selection,'actual_pid_consumed':False}))
        else: path.write_bytes(path.read_bytes())
        return dict(pid=pid,start_ticks='123',cwd=selection['actual_pid_receipt']['process_cwd'])
    monkeypatch.setattr(mod,'_observer_live_identity',identity)
    outcome=mod.ArtifactFreshnessDetector(dry_run=True).check()
    assert outcome.severity=='fail'
    first = outcome.details['submission_bottleneck_monitor_publication_recheck']['attempts'][0]
    assert ('observer_generation_changed_after_assessment' if change=='selector' else 'observer_report_changed_after_snapshot') in '; '.join(first['issues'])
    assert first['stable'] is False


@pytest.mark.parametrize('delta_sec',[-60,700,None])
def test_quiet_warning_rejects_future_or_stale_body_even_when_file_is_fresh(tmp_path,monkeypatch,delta_sec):
    from src.engine.monitoring import submission_bottleneck_monitor as monitor
    mod,root,now,path,report,*_ = _quiet_current_observer_fixture(tmp_path,monkeypatch)
    detector_now=now+timedelta(seconds=delta_sec or 0)
    if delta_sec is None:
        report['observer_generation']['completed_at']=(now+timedelta(seconds=30)).isoformat()
        report['observer_generation']['sha256']=monitor._observer_seal(report['observer_generation'])
        path.write_text(json.dumps(report))
    _isolate_submission_artifact_check(mod,root,detector_now,monkeypatch)
    os.utime(path,(detector_now.timestamp()-10,)*2)
    outcome=mod.ArtifactFreshnessDetector(dry_run=True).check()
    assert outcome.severity=='fail'
    assert 'observer_report_body_clock_not_current' in outcome.summary
    freshness=outcome.details['submission_bottleneck_monitor_observation_dimensions']['freshness']
    assert freshness['status']=='fresh'
    assert freshness['body_clock']['status']=='future_or_stale_or_unavailable'
    assert 'submission_bottleneck_monitor_observation_health' not in outcome.details


def test_pending_is_warning_and_cannot_clear_prior_daemon_failure(tmp_path, monkeypatch):
    from src.engine.error_detector import iter_daemon_alert_events
    from src.engine.error_detectors.base import DetectionResult
    from src.engine.monitoring import policy_generation_contract
    mod, root, now, path, report, *_ = _startup_observer_fixture(tmp_path, monkeypatch)
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None): return now if tz else now.replace(tzinfo=None)
    monkeypatch.setattr(mod, "datetime", Clock)
    monkeypatch.setattr(mod, "PROJECT_ROOT", root)
    monkeypatch.setattr(mod, "ARTIFACT_REGISTRY", [r for r in ARTIFACT_REGISTRY if r["id"] == "submission_bottleneck_monitor"])
    monkeypatch.setattr(mod, "is_krx_trading_day", lambda *args: True)
    monkeypatch.setattr(mod, "load_installed_crontab", lambda: "")
    for name in ("_entry_cancel_wait_result_semantics", "_holding_profit_exit_semantics", "_machine_result_semantics",
                 "_auxiliary_result_semantics", "_postclose_handoff_semantics", "_main_stop_semantics", "_samsung_forward_semantics",
                 "_initial_quantity_semantics"):
        monkeypatch.setattr(mod, name, lambda *args, **kwargs: {"status": "not_assessed", "findings": []})
    monkeypatch.setattr(mod, "_completed_semantic_source", lambda *args: {"status": "not_assessed", "findings": [], "target_date": None})
    monkeypatch.setattr(mod, "_current_semantic_owners", lambda *args: set())
    monkeypatch.setattr(policy_generation_contract, "observations", lambda *args, **kwargs: [])
    monkeypatch.setattr(policy_generation_contract, "retirement_dispositions", lambda *args, **kwargs: [])
    result = mod.ArtifactFreshnessDetector(dry_run=True).check()
    assert result.details["submission_bottleneck_monitor_status"] == "pending_first_current_observer"
    assert result.details["submission_bottleneck_monitor_current_observation_verified"] is False
    assert result.severity == "warning"
    assert "pending" in result.summary
    prior = DetectionResult(detector_id="artifact_freshness", category="artifact", severity="fail", summary="prior partial")
    state = {}
    assert len(list(iter_daemon_alert_events([prior], state, target_date="2026-10-14"))) == 1
    assert list(iter_daemon_alert_events([result], state, target_date="2026-10-14")) == []
    assert "artifact_freshness" in state


def test_current_observer_generation_requires_exact_selector_and_code(tmp_path, monkeypatch):
    from src.engine.monitoring import submission_bottleneck_monitor as monitor
    mod, root, now, path, report, tp, transition, sp, selection = _startup_observer_fixture(tmp_path, monkeypatch)
    code_path = Path(selection["release_root"]) / "src/engine/monitoring/submission_bottleneck_monitor.py"
    code_path.parent.mkdir(parents=True); code_path.write_bytes(b"reviewed immutable observer\n")
    code = dict(release_root=selection["release_root"], git_commit=selection["git_commit"],
                observer_code_sha256=hashlib.sha256(code_path.read_bytes()).hexdigest())
    monkeypatch.setattr(monitor, "_observer_code_identity", lambda: dict(code))
    started = datetime.fromisoformat("2026-10-14T14:41:00+09:00")
    original = monitor._observer_generation_snapshot(root, run_id=report["run_id"], target_date=report["date"], started_at=started)
    generation = monitor._finish_observer_generation(original, root, completed_at=started + timedelta(seconds=15))
    payload = {**report, "as_of": started.isoformat(), "semantic_status": "validated", "observer_generation": generation}
    assert mod._submission_observer_generation_issue(payload, root) is None
    generation["sha256"] = "0" * 64
    assert mod._submission_observer_generation_issue(payload, root) == "observer_generation_invalid"
    generation["sha256"] = monitor._observer_seal(generation)
    code_path.write_bytes(b"mutated observer\n")
    assert mod._submission_observer_generation_issue(payload, root) == "observer_generation_code_mismatch"
    sp.write_text(json.dumps({**selection, "actual_pid_consumed": False}))
    assert mod._submission_observer_generation_issue(payload, root) == "observer_generation_not_current"


@pytest.mark.parametrize('mutation', ['none', 'archive', 'seal', 'code', 'terminal', 'same_day', 'execution'])
def test_closed_postclose_observer_preserves_gaps_without_current_generation_claim(tmp_path, monkeypatch, mutation):
    mod, root, now, path, report, _, _, selector, selection = _current_observer_fixture(tmp_path, monkeypatch)
    archived = root/'data/runtime/postclose_recovery/2026-10-14/recovery/selection-before.json'
    archived.parent.mkdir(parents=True); archived.write_bytes(selector.read_bytes())
    selector.write_text(json.dumps({**selection,'actual_pid_consumed':False}))
    terminal = root/'data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_2026-10-14.status.json'
    terminal.parent.mkdir(parents=True); terminal.write_text(json.dumps(dict(target_date='2026-10-14',status='succeeded')))
    current = '2026-10-15'
    if mutation == 'archive': archived.write_text('{}')
    elif mutation == 'seal': report['observer_generation']['sha256']='0'*64
    elif mutation == 'code':
        (Path(selection['release_root'])/'src/engine/monitoring/submission_bottleneck_monitor.py').write_text('changed')
    elif mutation == 'terminal': terminal.write_text(json.dumps(dict(target_date='2026-10-14',status='failed')))
    elif mutation == 'same_day': current='2026-10-14'
    elif mutation == 'execution': report['execution_status']='deferred'
    assessment=mod._closed_submission_observer_evidence(report,root,'2026-10-14',current)
    if mutation != 'none':
        assert assessment is None
        assert mod._submission_observer_generation_issue(report,root) is not None
        return
    assert assessment['source_gap_preserved']==report['source_gap_semantics']
    assert assessment['semantic_status']=='partial'
    assert assessment['current_generation_verified'] is False
    assert assessment['current_observation_verified'] is False
    assert assessment['full_coverage_proven'] is False
    path.write_text(json.dumps(report))
    _isolate_submission_artifact_check(mod,root,now+timedelta(days=1),monkeypatch)
    detector=mod.ArtifactFreshnessDetector(dry_run=True)
    detector.postclose_source_date='2026-10-14'
    result=detector.check()
    assert result.severity=='warning'
    assert result.details['submission_bottleneck_monitor_status']=='historical_observation_only'
    assert result.details['submission_bottleneck_monitor_historical_evidence']==assessment


@pytest.mark.parametrize("which", ["report", "selector", "transition"])
def test_observer_pending_metadata_fifo_is_bounded_and_never_pending(tmp_path, monkeypatch, which):
    import multiprocessing
    fixture = _startup_observer_fixture(tmp_path, monkeypatch)
    mod, root, now, report, _, transition, _, selector, _ = fixture
    path = {"report": report, "selector": selector, "transition": transition}[which]
    path.unlink(); os.mkfifo(path)
    context = multiprocessing.get_context("fork"); queue = context.Queue()
    def attempt():
        queue.put(mod._submission_observer_transition_pending(root, report, now, max_staleness_sec=600))
    child = context.Process(target=attempt); child.start(); child.join(timeout=2)
    if child.is_alive():
        child.terminate(); child.join(timeout=2)
        pytest.fail("observer detector blocked on FIFO")
    assert queue.get(timeout=1) is None
    assert path.is_fifo()


@pytest.mark.parametrize("encoded", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1e999}', b'[]'])
def test_new_observer_metadata_reader_rejects_non_strict_json(tmp_path, encoded):
    import src.engine.error_detectors.artifact_freshness as mod
    path = tmp_path / "metadata.json"; path.write_bytes(encoded)
    with pytest.raises(ValueError): mod._observer_small_object(path)


def test_observer_pending_malformed_pid_cannot_reach_proc_path(tmp_path, monkeypatch):
    mod, root, now, report, _, tp, transition, sp, selection = _startup_observer_fixture(tmp_path, monkeypatch)
    selection["actual_pid_receipt"]["pid"] = "../../tmp/not-a-pid"
    transition["successor_identity"]["pid"] = "../../tmp/not-a-pid"
    sp.write_text(json.dumps(selection)); tp.write_text(json.dumps(transition))
    monkeypatch.setattr(mod, "_observer_live_identity", lambda *args: pytest.fail("malformed PID reached proc lookup"))
    assert mod._submission_observer_transition_pending(root, report, now, max_staleness_sec=600) is None


def test_actual_artifact_check_and_status_reader_do_not_open_fifo(tmp_path, monkeypatch):
    import multiprocessing
    fixture = _startup_observer_fixture(tmp_path, monkeypatch)
    mod, root, now, report, *_ = fixture
    report.unlink(); os.mkfifo(report)
    monkeypatch.setattr(mod, "PROJECT_ROOT", root)
    monkeypatch.setattr(mod, "ARTIFACT_REGISTRY", [r for r in ARTIFACT_REGISTRY if r["id"] == "submission_bottleneck_monitor"])
    monkeypatch.setattr(mod, "is_krx_trading_day", lambda *args: True)
    monkeypatch.setattr(mod, "load_installed_crontab", lambda: "")
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None): return now if tz else now.replace(tzinfo=None)
    monkeypatch.setattr(mod, "datetime", Clock)
    context = multiprocessing.get_context("fork"); queue = context.Queue()
    def attempt():
        status = mod.ArtifactFreshnessDetector._validate_json_status(
            dict(id="submission_bottleneck_monitor", json_status_field="notification_status"), report, {})
        outcome = mod.ArtifactFreshnessDetector(dry_run=True).check()
        queue.put((status, outcome.details["submission_bottleneck_monitor_status"]))
    child = context.Process(target=attempt); child.start(); child.join(timeout=2)
    if child.is_alive():
        child.terminate(); child.join(timeout=2)
        pytest.fail("artifact check blocked before safe observer reader")
    error, status = queue.get(timeout=1)
    assert "regular_file_required" in error and status == "fail"
    assert report.is_fifo()


@pytest.mark.parametrize('tamper', [None, 'birth_lower_bound_epoch', 'boot_epoch'])
def test_current_health_birth_requires_independent_kernel_attestation(tmp_path, monkeypatch, tamper):
    import copy
    from src.engine.monitoring import submission_bottleneck_monitor as monitor
    mod, root, now, path, report, _, selection, seal = _quiet_current_observer_fixture(tmp_path, monkeypatch)
    receipt = selection['actual_pid_receipt']
    actor = [str(receipt['pid']), receipt['start_ticks']]
    at = datetime.fromisoformat(report['as_of'])
    boot = int(at.timestamp()) - 3600
    hz = 100
    lower = boot + int(actor[1])/hz - 1.0
    native = dict(schema='submission_monitor_actor_birth_v1', status='verified', actor=actor,
        observed_at=at.isoformat(), boot_epoch=boot, clock_ticks_per_second=hz, start_ticks=int(actor[1]),
        birth_lower_bound_epoch=lower, birth_lower_bound_at=datetime.fromtimestamp(lower, monitor.KST).isoformat(),
        process_cwd=receipt['process_cwd'], runtime_effect=False, allowed_runtime_apply=False)
    declared = copy.deepcopy(native)
    if tamper is not None:
        declared[tamper] += 1
        # A forged proof is internally consistent, including its derived clock.
        # Only the separate live-kernel oracle can disprove its claimed boot.
        if tamper == 'boot_epoch':
            declared['birth_lower_bound_epoch'] += 1
        declared['birth_lower_bound_at'] = datetime.fromtimestamp(
            declared['birth_lower_bound_epoch'], monitor.KST).isoformat()
    calls = []
    def attest(generation, observed):
        calls.append((generation['selector_reported_pid_receipt'], observed))
        return copy.deepcopy(native)
    monkeypatch.setattr(monitor, '_attest_health_actor_birth', attest)
    seal()
    report['observer_generation']['actor_birth_proof'] = declared
    for key in ('source_gap_semantics', 'machine_semantics'):
        report[key]['current_health_cohort'] = dict(
            monitor._health_cohort(copy.deepcopy(report[key]), actor, at), actor_birth_proof=declared)
    report['observer_generation']['sha256'] = monitor._observer_seal(report['observer_generation'])
    report['observation_health'] = monitor.observation_health_projection(report)
    path.write_text(json.dumps(report)); os.utime(path, (now.timestamp()-10,)*2)
    outcome = mod.ArtifactFreshnessDetector(dry_run=True).check()
    if tamper is None:
        assert outcome.severity == 'warning'
        assert calls == [(receipt, at)]
        assert outcome.details['submission_bottleneck_monitor_current_observation_verified'] is False
    else:
        assert outcome.severity == 'fail'
        # A malformed proof can fail in the pure projection before the kernel
        # check; an internally valid changed boot must reach and fail the latter.
        if tamper == 'boot_epoch':
            assert calls == [(receipt, at)]
            assert 'observer_current_main_birth_unproven' in outcome.summary


@pytest.mark.parametrize('tamper', [None, 'source_issue', 'stale_input', 'wrong_actor'])
def test_active_observer_consumer_warns_only_for_current_intact_bounded_report(tmp_path, monkeypatch, tamper):
    import copy
    from src.tests.test_submission_bottleneck_monitor import _bounded_outcome_health_fixture, _health_birth_fixture
    from src.engine.monitoring import submission_bottleneck_monitor as monitor
    def payload():
        report, *_ = _bounded_outcome_health_fixture(partial=False, outcome='unknown_pass')
        report.update(status='observing', blocker=None, scopes={'KRX|krx_regular|bundle': {}})
        report['input_provenance']['row_count'] = 1
        return report
    mod, root, now, path, report, _, selection, seal = _quiet_current_observer_fixture(
        tmp_path, monkeypatch, payload_factory=payload)
    actor = [str(selection['actual_pid_receipt']['pid']), selection['actual_pid_receipt']['start_ticks']]
    at = monitor.stamp(report['as_of'])
    native, _ = _health_birth_fixture(at, actor)
    native['process_cwd'] = selection['actual_pid_receipt']['process_cwd']
    monkeypatch.setattr(monitor, '_attest_health_actor_birth', lambda generation, observed: copy.deepcopy(native))
    seal()
    report['observer_generation']['actor_birth_proof'] = copy.deepcopy(native)
    report['observer_generation']['sha256'] = monitor._observer_seal(report['observer_generation'])
    for name in ('source_gap_semantics', 'machine_semantics'):
        report[name]['current_health_cohort']['actor_birth_proof'] = copy.deepcopy(native)
    if tamper == 'source_issue':
        report['source_gap_semantics']['current_health_cohort']['view']['issues'] = {'native_contract_missing': 1}
    elif tamper == 'stale_input':
        report['input_provenance']['snapshot_as_of'] = (at-timedelta(seconds=421)).isoformat()
        report['input_provenance']['snapshot_age_seconds'] = 421
    elif tamper == 'wrong_actor':
        report['machine_semantics']['current_health_cohort']['actor'] = ['999', '999']
    report['observation_health'] = monitor.observation_health_projection(report)
    path.write_text(json.dumps(report)); os.utime(path, (now.timestamp()-10,)*2)
    before = path.read_bytes()
    outcome = mod.ArtifactFreshnessDetector(dry_run=True).check()
    assert outcome.severity == ('warning' if tamper is None else 'fail'), outcome.summary
    assert path.read_bytes() == before
    assert outcome.details['submission_bottleneck_monitor_observation_health_projection_match'] is True
    assert outcome.details.get('submission_bottleneck_monitor_current_observation_verified') is not True
    assert report['observation_health']['current_observation_verified'] is False
    if tamper is None:
        assert outcome.details['submission_bottleneck_monitor_observation_health']['status'] == 'warning_pending'
        assert report['status'] == 'observing' and report['semantic_status'] == 'partial'


def test_observer_reads_publication_after_slow_semantics_with_current_clock(tmp_path, monkeypatch):
    mod, root, now, path, report, _, _, seal = _quiet_current_observer_fixture(tmp_path, monkeypatch)
    path.write_text('{old incomplete report')
    reads = []
    original = mod._submission_observer_snapshot
    def snapshot(candidate):
        reads.append(candidate)
        return original(candidate)
    monkeypatch.setattr(mod, '_submission_observer_snapshot', snapshot)
    def slow_semantics(*args, **kwargs):
        assert reads == []
        seal()
        return dict(status='not_assessed', findings=[])
    monkeypatch.setattr(mod, '_initial_quantity_semantics', slow_semantics)
    outcome = mod.ArtifactFreshnessDetector(dry_run=True).check()
    assert outcome.severity == 'warning', outcome.summary
    assert reads == [path]
    boundary = outcome.details['submission_bottleneck_monitor_publication_recheck']
    assert boundary['stable'] and len(boundary['attempts']) == 1
    assert outcome.details['submission_bottleneck_monitor_run_id'] == report['run_id']


@pytest.mark.parametrize('replacement', ['valid', 'invalid_execution', 'invalid_projection', 'stale',
    'future', 'missing', 'symlink', 'oversize', 'wrong_selector', 'repeated_publication'])
def test_observer_final_recheck_never_inherits_replaced_verdict(tmp_path, monkeypatch, replacement):
    mod, root, now, path, report, selection_path, selection, seal = _quiet_current_observer_fixture(tmp_path, monkeypatch)
    report['execution_status'] = 'failed'
    seal()
    old_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    detector = mod.ArtifactFreshnessDetector
    original = detector._validate_json_status
    calls = []
    def validate(artifact, candidate, details, **kwargs):
        result = original(artifact, candidate, details, **kwargs)
        if artifact['id'] != 'submission_bottleneck_monitor':
            return result
        calls.append(report['run_id'])
        if len(calls) == 1 or replacement == 'repeated_publication':
            report.update(execution_status='completed', run_id=('b' if len(calls) == 1 else 'c') * 32)
            seal()
            if replacement == 'invalid_execution':
                report['execution_status'] = 'failed'; seal()
            elif replacement == 'invalid_projection':
                report['observation_health']['reason'] = 'forged'
                path.write_text(json.dumps(report)); os.utime(path, (now.timestamp()-10,)*2)
            elif replacement == 'stale':
                os.utime(path, (now.timestamp()-601,)*2)
            elif replacement == 'future':
                os.utime(path, (now.timestamp()+60,)*2)
            elif replacement == 'missing':
                path.unlink()
            elif replacement == 'symlink':
                copy = path.with_name('untrusted.json'); copy.write_bytes(path.read_bytes())
                path.unlink(); path.symlink_to(copy)
            elif replacement == 'oversize':
                path.write_bytes(b'x' * (8 * 1024 * 1024 + 1))
            elif replacement == 'wrong_selector':
                selection_path.write_text(json.dumps({**selection, 'actual_pid_consumed': False}))
        return result
    monkeypatch.setattr(detector, '_validate_json_status', staticmethod(validate))
    outcome = detector(dry_run=True).check()
    assert outcome.severity == ('warning' if replacement == 'valid' else 'fail'), outcome.summary
    boundary = outcome.details['submission_bottleneck_monitor_publication_recheck']
    assert len(boundary['attempts']) == 2
    assert boundary['attempts'][0]['stable'] is False
    assert boundary['attempts'][0]['issues']
    first = boundary['attempts'][0]['details']['submission_bottleneck_monitor_observation_dimensions']
    assert first['report']['byte_sha256'] == old_sha
    if replacement == 'repeated_publication':
        assert not boundary['stable']
        assert 'observer_inputs_changed_during_final_recheck' in outcome.summary
    else:
        assert boundary['stable']
    if replacement == 'valid':
        assert outcome.details['submission_bottleneck_monitor_run_id'] == 'b' * 32
        assert outcome.details['submission_bottleneck_monitor_current_observation_verified'] is False
        assert 'failed' not in outcome.summary
    assert len(calls) <= 2


def test_observer_recheck_preserves_other_artifact_failures(tmp_path, monkeypatch):
    mod, root, now, path, report, _, _, seal = _quiet_current_observer_fixture(tmp_path, monkeypatch)
    mod.ARTIFACT_REGISTRY.append(dict(id='other_required', path_template='missing.json', critical=True))
    original = mod.ArtifactFreshnessDetector._validate_json_status
    count = 0
    def validate(*args, **kwargs):
        nonlocal count
        result = original(*args, **kwargs)
        count += 1
        if count == 1:
            report['run_id'] = 'b' * 32; seal()
        return result
    monkeypatch.setattr(mod.ArtifactFreshnessDetector, '_validate_json_status', staticmethod(validate))
    result = mod.ArtifactFreshnessDetector(dry_run=True).check()
    assert result.severity == 'fail'
    assert result.details['other_required_status'] == 'fail'
    assert 'other_required: missing.json missing' in result.summary
    assert result.details['submission_bottleneck_monitor_status'] == 'pending_no_applicable_observations'


def test_observer_late_check_uses_elapsed_wall_clock(tmp_path, monkeypatch):
    mod, root, now, path, report, *_ = _quiet_current_observer_fixture(tmp_path, monkeypatch)
    def slow_semantics(*args, **kwargs):
        monkeypatch.setattr(mod.time, 'time', lambda: now.timestamp() + 650)
        return dict(status='not_assessed', findings=[])
    monkeypatch.setattr(mod, '_initial_quantity_semantics', slow_semantics)
    outcome = mod.ArtifactFreshnessDetector(dry_run=True).check()
    assert outcome.severity == 'fail'
    assert outcome.details['submission_bottleneck_monitor_age_sec'] == 660
    assert 'stale (660s > 600s)' in outcome.summary


def test_observer_final_check_rejects_kst_date_rollover(tmp_path, monkeypatch):
    mod, root, now, path, report, *_ = _quiet_current_observer_fixture(tmp_path, monkeypatch)
    class NextDay(datetime):
        @classmethod
        def now(cls, tz=None):
            current = now + timedelta(days=1)
            return current if tz else current.replace(tzinfo=None)
    def slow_semantics(*args, **kwargs):
        monkeypatch.setattr(mod, 'datetime', NextDay)
        return dict(status='not_assessed', findings=[])
    monkeypatch.setattr(mod, '_initial_quantity_semantics', slow_semantics)
    outcome = mod.ArtifactFreshnessDetector(dry_run=True).check()
    assert outcome.severity == 'fail'
    assert 'observer_check_crossed_kst_date_boundary' in outcome.summary
    assert outcome.details['submission_bottleneck_monitor_publication_recheck']['stable'] is False


def test_holding_native_source_gap_identity_reaches_alert_without_truncating_population(tmp_path):
    from src.tests.test_holding_exit_sentinel import _semantic_flow
    from src.tests.test_notify_error_detection_admin import _holding_gap_fixture
    from src.engine.scalping.holding_profit_exit_semantics import audit_profit_exit_flow
    from src.engine.error_detectors.artifact_freshness import _semantic_alert_candidates
    event, mechanical, rows, lineage, at = _semantic_flow()
    rows.append(event(2, 'exit_signal', lineage))
    semantics = audit_profit_exit_flow(rows, target_date='2026-10-09', load_votes=lambda _: [],
                                      mechanical_policy_receipt=mechanical, consumed_pid=42)
    gaps, alert, _, _ = _holding_gap_fixture()
    semantics.update(status='source_gap', semantic_status='source_gap', findings=[],
        policy_binding_gaps=[], runtime_consumption_gaps=[],
        **{k:gaps[k] for k in ('source_gaps','source_gap_details')})
    original=semantics['lifecycle'][0]
    original.update(position_key='record:42', signal_id='signal-1', buy_fill_identity='b'*64)
    path=tmp_path/'data/report/holding_exit_sentinel/holding_exit_sentinel_2026-10-09.json'
    path.parent.mkdir(parents=True)
    report=dict(target_date='2026-10-09',as_of=semantics['as_of'],source_generation=semantics['source_generation'],profit_exit_semantics=semantics)
    path.write_text(json.dumps(report))
    observed=_holding_profit_exit_semantics(tmp_path,'2026-10-09')
    assert observed['native_validated'] is True
    assert observed['source_gap_identity'] == alert['source_gap_identity']
    alerts=_semantic_alert_candidates('holding_profit_exit',observed,'2026-10-09')
    assert alerts[0]['source_gap_identity']==alert['source_gap_identity']
    assert alerts[0]['affected']==1
    # A missing detail disables stable deduplication, without clearing the warning.
    semantics['source_gap_details']=[]
    path.write_text(json.dumps(report))
    observed=_holding_profit_exit_semantics(tmp_path,'2026-10-09')
    assert observed['status']=='source_gap'
    assert observed['source_gap_identity'] is None
    # Broken generation still fails the native contract entirely.
    report['source_generation']='0'*64
    path.write_text(json.dumps(report))
    assert _holding_profit_exit_semantics(tmp_path,'2026-10-09')['status']=='source_invalid'


def test_native_component_comparison_is_independent_of_joint_handoff(tmp_path, monkeypatch):
    from src.engine.error_detectors import artifact_freshness as detector
    from src.engine.scalping import continuous_reversal_postclose as reports
    from src.engine.scalping import continuous_reversal_policy as policy
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    from src.engine.scalping import reversal_policy_status as status
    day = '2026-10-15'
    monkeypatch.setattr(detector, '_semantic_stage_binding', lambda *a, **k: {'status':'succeeded'})
    monkeypatch.setattr(policy, 'direct_handoff', lambda *a, **k: dict(effective_date='2026-10-16',
        selection_metric='native', comparison_complete=False, scope_pending=['aux-only']))
    monkeypatch.setattr(native, 'load', lambda **k: {'continuous_reversal':{'machine_cells':{},'auxiliary_cells':{}}})
    monkeypatch.setattr(status, 'current_view', lambda *a: {'status':'not_observed'})
    for component,complete in [('machine',True),('auxiliary',False)]:
        value=reports.seal(dict(schema=reports.SCHEMA, source_date=day, status='completed',
            comparison_complete=complete, adoption_basis='operator_designated_initial_cumulative',
            scope_pending=[] if complete else ['aux-only']))
        path=tmp_path/'data/report/continuous_reversal'/day/(component+'.json')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))
        bound=(tmp_path/'data/report/ai_decision_action_outcome_calibration'/f'winrate_policy_{day}.json'
            if component=='machine' else tmp_path/'data/report/ai_entry_setup_paired_replay_batch'/f'compact_auxiliary_paired_economic_{day}.json')
        bound.parent.mkdir(parents=True,exist_ok=True);bound.write_text(json.dumps(value))
        result=detector._continuous_reversal_result_semantics(tmp_path,day,component)
        assert result['component_comparison_complete'] is complete
        assert result['joint_comparison_complete'] is False
        assert result['scope_pending']==([] if complete else ['aux-only'])
        assert result['policy_states']['adoption_basis']=='operator_designated_initial_cumulative'
        assert result['bound_target_date']=='2026-10-16'
        assert result['runtime_effect'] is False


def test_optional_research_native_receipts_calendar_scope_and_generation(tmp_path,monkeypatch):
    from src.engine.error_detectors import artifact_freshness as detector
    from src.engine.automation import main_market_weakness_research as native
    from src.engine.scalping import continuous_reversal_postclose as reports
    base=native.namespace(tmp_path/'data');base.mkdir(parents=True)
    def put(name,value):
        p=base/name;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(reports.seal(dict(**value,runtime_effect=False,allowed_runtime_apply=False))))
    scope={'through_date':'2026-10-15','source_dates':['2026-10-15']}
    put('installation.json',dict(enabled=True,notify_enabled=True))
    put('night_summary.json',dict(latest_attempt=dict(source_date='2026-10-15',status='deferred',reason='regular_postclose_or_eod_active')))
    put('last_completed_computation.json',dict(source_date='2026-10-14',cumulative_generation='g'))
    put('cumulative/current.json',dict(generation='g',source_scope=scope,source_cursor_states=[],pending_source_dates=[],invalidated_source_dates=[]))
    monkeypatch.setattr(native,'verify_installed_calendar',lambda c:True)
    monkeypatch.setattr(native,'research_source_scope',lambda *a,**k:scope)
    monkeypatch.setattr(native,'source_cursor_states',lambda *a:[])
    now=datetime.fromisoformat('2026-10-16T16:00:00+09:00')
    result=detector._optional_weakness_semantics(tmp_path,now)
    assert result['status']=='verified' and result['execution_status']=='deferred'
    assert result['last_completed_computation']['source_date']=='2026-10-14'
    assert result['mandatory_preopen'] is False and result['runtime_effect'] is False
    monkeypatch.setattr(native,'verify_installed_calendar',lambda c:False)
    result=detector._optional_weakness_semantics(tmp_path,now)
    assert result['findings']==['optional_research_calendar_unverified']
    assert result['native_validated'] is False
