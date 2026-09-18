def test_modern_machine_link_refresh_is_exact_date_and_reaches_summary_consumers(tmp_path):
    import json
    import hashlib
    from src.engine.scalping.microstructure_reaction_context import (
        refresh_machine_evaluation_link, microstructure_summary_contract, MACHINE_EVALUATION_SCHEMA,
    )
    source = tmp_path / 'ai_decision_action_outcome_calibration_2026-09-17.json'
    source.write_text(json.dumps({
        'schema': 'ai_decision_action_outcome_calibration_v2',
        'target_date': '2026-09-17', 'runtime_effect': False, 'allowed_runtime_apply': False,
        'hierarchical_entry_quality': {'machine_decision_case_table': {'microstructure_evaluation': {
            'schema': MACHINE_EVALUATION_SCHEMA, 'case_count': 206,
            'cost_adjusted_outcome_count': 205, 'partitions': [],
            'actual_completed_ev_pct': None, 'runtime_effect': False, 'allowed_runtime_apply': False,
        }}},
    }))
    report = refresh_machine_evaluation_link(source, report_root=tmp_path / 'report')
    linked = microstructure_summary_contract(report['summary'])['machine_primary_auxiliary_evaluation']
    assert linked['case_count'] == 206
    forged = {**report['summary']['machine_primary_auxiliary_evaluation'], 'case_count': 999}
    assert microstructure_summary_contract({'machine_primary_auxiliary_evaluation': forged})['machine_primary_auxiliary_evaluation']['status'] == 'source_gap_machine_evaluation_parent_hash_mismatch'
    assert linked['source_target_date'] == '2026-09-17'
    assert linked['source_report_sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert report['runtime_effect'] is report['allowed_runtime_apply'] is False
    path = tmp_path / 'report/microstructure_reaction_context/microstructure_reaction_context_2026-09-17.json'
    path.write_text(json.dumps({'date': '2026-09-16'}))
    import pytest
    with pytest.raises(ValueError, match='target_date_mismatch'):
        refresh_machine_evaluation_link(source, report_root=tmp_path / 'report')


def test_machine_evaluation_summary_does_not_reuse_stale_or_absent_parent(tmp_path):
    import hashlib
    from src.engine.scalping.microstructure_reaction_context import microstructure_summary_contract
    missing = microstructure_summary_contract({})['machine_primary_auxiliary_evaluation']
    assert missing['status'] == 'source_gap_exact_date_machine_evaluation_not_generated'
    source = tmp_path / 'parent.json'
    source.write_text('before')
    summary = {'machine_primary_auxiliary_evaluation': {
        'source_report_path': str(source), 'source_report_sha256': hashlib.sha256(b'before').hexdigest(),
        'case_count': 20, 'machine_tuning_input_allowed': True, 'auxiliary_tuning_input_allowed': True,
    }}
    source.write_text('after')
    linked = microstructure_summary_contract(summary)['machine_primary_auxiliary_evaluation']
    assert linked['status'] == 'source_gap_machine_evaluation_parent_hash_mismatch'
    assert linked['machine_tuning_input_allowed'] is linked['auxiliary_tuning_input_allowed'] is False
    assert linked['case_count'] == 20


def test_machine_parent_access_time_change_is_not_a_new_source_generation(tmp_path):
    import os
    import hashlib
    from src.engine.scalping.microstructure_reaction_context import microstructure_summary_contract
    import json
    path = tmp_path / 'ai_decision_action_outcome_calibration_2026-09-17.json'
    evaluation = {'status': 'evaluable_descriptive_counterfactual'}
    path.write_text(json.dumps({'schema': 'ai_decision_action_outcome_calibration_v2', 'runtime_effect': False, 'allowed_runtime_apply': False, 'target_date': '2026-09-17', 'hierarchical_entry_quality': {'machine_decision_case_table': {'microstructure_evaluation': evaluation}}}))
    os.utime(path, ns=(1, path.stat().st_mtime_ns))
    result = microstructure_summary_contract({'machine_primary_auxiliary_evaluation': {
        'status': 'evaluable_descriptive_counterfactual', 'source_report_path': str(path),
        'source_target_date': '2026-09-17',
        'source_report_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    }})['machine_primary_auxiliary_evaluation']
    assert result['status'] == 'evaluable_descriptive_counterfactual'


def test_modern_only_handoff_preserves_legacy_and_rejects_stale_consumers(tmp_path):
    import hashlib
    import json
    from src.engine.scalping.microstructure_reaction_context import (
        MACHINE_EVALUATION_SCHEMA, refresh_machine_evaluation_link, microstructure_summary_contract,
    )
    from src.engine.verify_threshold_cycle_postclose_chain import _microstructure_diagnostic_handoff_status

    source = tmp_path / 'ai_decision_action_outcome_calibration_2026-09-17.json'
    source.write_text(json.dumps({
        'schema': 'ai_decision_action_outcome_calibration_v2', 'target_date': '2026-09-17',
        'runtime_effect': False, 'allowed_runtime_apply': False,
        'hierarchical_entry_quality': {'machine_decision_case_table': {'microstructure_evaluation': {
            'schema': MACHINE_EVALUATION_SCHEMA, 'status': 'source_gap_full_cost_outcomes_missing',
            'case_count': 0, 'cost_adjusted_outcome_count': 0, 'partitions': [],
            'runtime_effect': False, 'allowed_runtime_apply': False,
        }}},
    }))
    path = tmp_path / 'report/microstructure_reaction_context/microstructure_reaction_context_2026-09-17.json'
    path.parent.mkdir(parents=True)
    legacy = json.dumps({'date': '2026-09-17', 'generated_at': 'old-as-of',
                         'summary': {'row_count': 9000}, 'code_improvement_orders': [{'order_id': 'retired_adm'}]}).encode()
    path.write_bytes(legacy)
    report = refresh_machine_evaluation_link(source, report_root=tmp_path / 'report')
    assert report['legacy_study_status'] == 'retired'
    assert report['warnings'] == []
    assert 'row_count' not in report['summary']
    assert list(path.parent.glob('*.legacy.*.json'))[0].read_bytes() == legacy
    summary = microstructure_summary_contract(report['summary'])
    assert summary['row_count'] is None
    assert summary['clean_baseline_cumulative_opportunity_exploration']['status'] == 'retired'
    ev = {'microstructure_reaction_context': summary}
    daily = {'calibration_source_bundle': {'source_metrics': {'microstructure_reaction_context': summary}}}
    check = _microstructure_diagnostic_handoff_status(report, ev, ev, {}, daily)
    assert check['status'] == 'pass'  # Cost gap is reported, not a fabricated no-edge or handoff failure.
    stale = {'microstructure_reaction_context': {**summary, 'machine_primary_auxiliary_evaluation': {}}}
    check = _microstructure_diagnostic_handoff_status(report, stale, ev, {}, daily)
    assert 'ev_modern_evaluation_stale_or_missing' in check['issues']
    source.write_text(source.read_text() + '\n')
    check = _microstructure_diagnostic_handoff_status(report, ev, ev, {}, daily)
    assert 'modern_parent_hash_mismatch' in check['issues']
    assert report['summary']['machine_primary_auxiliary_evaluation']['source_report_sha256'] != hashlib.sha256(source.read_bytes()).hexdigest()


def test_retired_raw_job_cannot_be_reenabled_by_environment():
    from pathlib import Path
    import ast
    script = Path('deploy/run_threshold_cycle_postclose.sh').read_text()
    assert 'RUN_MICROSTRUCTURE_REACTION_CONTEXT' not in script
    assert '-m src.engine.scalping.microstructure_reaction_context --date' not in script
    tree = ast.parse(Path('src/engine/scalping/microstructure_reaction_context.py').read_text())
    names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert 'build_microstructure_reaction_context_report' not in names
    assert 'backfill_clean_baseline_opportunity_rollups' not in names
    assert script.index('daily_machine_evaluation_handoff') > script.index('--require-policy-publication')


def test_daily_refresh_changes_only_modern_handoff_without_policy_replay(tmp_path, monkeypatch):
    import json
    from src.engine import daily_threshold_cycle_report as daily
    from src.engine.scalping.microstructure_reaction_context import MACHINE_EVALUATION_SCHEMA, refresh_machine_evaluation_link
    parent = tmp_path / 'ai_decision_action_outcome_calibration_2026-09-17.json'
    parent.write_text(json.dumps({
        'schema': 'ai_decision_action_outcome_calibration_v2', 'target_date': '2026-09-17',
        'runtime_effect': False, 'allowed_runtime_apply': False,
        'hierarchical_entry_quality': {'machine_decision_case_table': {'microstructure_evaluation': {
            'schema': MACHINE_EVALUATION_SCHEMA, 'partitions': [],
            'runtime_effect': False, 'allowed_runtime_apply': False,
        }}},
    }))
    refresh_machine_evaluation_link(parent, report_root=tmp_path)
    path = tmp_path / 'threshold_cycle_2026-09-17.json'
    original = {'date': '2026-09-17', 'summary': {'real_pnl': None},
                'apply_candidate_list': [{'family': 'existing_owner', 'hash': 'frozen'}],
                'calibration_source_bundle': {'source_metrics': {'other_owner': {'valid': True}}}}
    original['meta'] = {'pipeline_load': {'2026-09-17': {'event_family_projection': ['holding_flow_ofi_smoothing', 'scale_in_counterfactual', 'statistical_action_weight']}}}
    path.write_text(json.dumps(original))
    monkeypatch.setattr(daily, 'REPORT_DIR', tmp_path)
    daily.refresh_machine_evaluation_only('2026-09-17')
    actual = json.loads(path.read_text())
    assert actual['meta'] == original['meta']
    assert actual['summary'] == original['summary']
    assert actual['apply_candidate_list'] == original['apply_candidate_list']
    assert actual['calibration_source_bundle']['source_metrics']['other_owner'] == {'valid': True}
    assert actual['calibration_source_bundle']['source_metrics']['microstructure_reaction_context']['legacy_study_status'] == 'retired'


def test_machine_parent_authority_and_report_metric_contract(tmp_path):
    import json
    import hashlib
    import pytest
    from src.engine.scalping.microstructure_reaction_context import (
        MACHINE_EVALUATION_SCHEMA, refresh_machine_evaluation_link, microstructure_summary_contract,
    )
    parent = tmp_path / 'ai_decision_action_outcome_calibration_2026-09-17.json'
    body = {'schema': 'ai_decision_action_outcome_calibration_v2', 'target_date': '2026-09-17',
            'runtime_effect': False, 'allowed_runtime_apply': False,
            'hierarchical_entry_quality': {'machine_decision_case_table': {'microstructure_evaluation': {
                'schema': MACHINE_EVALUATION_SCHEMA, 'partitions': [], 'case_count': 0,
                'runtime_effect': False, 'allowed_runtime_apply': False}}}}
    parent.write_text(json.dumps(body))
    report = refresh_machine_evaluation_link(parent, report_root=tmp_path)
    for key in ('metric_role', 'decision_authority', 'window_policy', 'sample_floor',
                'primary_decision_metric', 'source_quality_gate', 'forbidden_uses'):
        assert report[key]
    linked = dict(report['summary']['machine_primary_auxiliary_evaluation'])
    body['allowed_runtime_apply'] = True
    parent.write_text(json.dumps(body))
    linked['source_report_sha256'] = hashlib.sha256(parent.read_bytes()).hexdigest()
    assert microstructure_summary_contract({'machine_primary_auxiliary_evaluation': linked})['machine_primary_auxiliary_evaluation']['status'] == 'source_gap_machine_evaluation_parent_hash_mismatch'
    body['allowed_runtime_apply'] = False
    parent.write_text(json.dumps(body))
    path = tmp_path / 'microstructure_reaction_context/microstructure_reaction_context_2026-09-17.json'
    report['allowed_runtime_apply'] = True
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match='diagnostic_authority_invalid'):
        refresh_machine_evaluation_link(parent, report_root=tmp_path)
