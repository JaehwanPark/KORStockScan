"""Forward postclose regression; all fixtures are offline, with no orders/provider."""

from copy import deepcopy
from datetime import datetime, timedelta
import pytest

from src.engine.scalping import postclose_entry_validation as validation
from src.engine.scalping import entry_strategy_policy as strategy
from src.engine.scalping import ai_action_outcome_calibration as calibration
from src.engine.scalping import compact_auxiliary_paired_replay as compact


def machine_rows(count=20, day='2026-10-02'):
    from src.tests.test_entry_strategy_policy import machine_cost_row
    start = datetime.fromisoformat(day + 'T09:00:00+09:00')
    rows = []
    for i in range(count):
        row = machine_cost_row()
        row.update(source_date=day, decision_trace_id=f'{day}:attempt-{i}',
                   scanner_promotion_id=f'promotion-{i}', decision_ts=(start+timedelta(minutes=i*15)).isoformat())
        row['comparison']['entry_cost_contract']['source_date'] = day
        rows.append(row)
    return rows


def test_chronology_keeps_retries_and_purges_entire_overlapping_opportunity():
    rows = machine_rows(10)
    # One late retry crosses the validation boundary; do not keep its early arm.
    retry = deepcopy(rows[1])
    retry.update(decision_trace_id='retry', decision_ts=rows[7]['decision_ts'])
    train, held, proof = validation.chronological_split(rows + [retry])
    assert len(held) == 3
    assert all(r['scanner_promotion_id'] != 'promotion-1' for r in train)
    assert len(proof['purged_opportunity_ids']) == 1
    assert validation.split_manifest_valid(proof, [r['scanner_promotion_id'] for r in train], [r['scanner_promotion_id'] for r in held])
    assert validation.chronological_split(rows + [rows[0]]) == validation.chronological_split(rows)


def test_new_identity_requires_lineage_and_separates_venue():
    row = machine_rows(1)[0]
    other = {**row, 'effective_venue': 'NXT'}
    assert validation.opportunity_identity(row) != validation.opportunity_identity(other)
    with pytest.raises(ValueError, match='lineage_missing'):
        validation.opportunity_identity({**row, 'scanner_promotion_id': None})


def test_machine_recovery_uses_episode_union_and_fractional_outcomes():
    rows = machine_rows(2)
    rows[1]['scanner_promotion_id'] = rows[0]['scanner_promotion_id']
    rows[1]['entry_quality_path'].update(first_hit='exact_stop_first')
    rows[0]['comparison']['conservative_execution_cost_pct'] = str(rows[0]['comparison']['conservative_execution_cost_pct'])
    result = calibration._machine_admission_metrics(rows, ['ENTER_NOW'] * 2, recovery=True)
    recovered = result['recovery_metrics']
    assert recovered['selected_opportunity_count'] == 1
    assert recovered['win_rate_pct'] == 50
    assert recovered['successful_opportunity_weight'] == .5
    assert result['transition_opportunity_counts']['nonentry_success_recovered'] == 1
    assert result['transition_opportunity_counts']['nonentry_failure_recovered'] == 1


def test_machine_later_parent_enter_is_observed_even_without_price_or_cost_outcome():
    rows = machine_rows(2)
    rows[1]['scanner_promotion_id'] = rows[0]['scanner_promotion_id']
    rows[1]['comparison']['incumbent_machine_action'] = 'ENTER_NOW'
    rows[1]['entry_quality_contract_valid'] = False
    result = calibration._machine_admission_metrics(rows, ['ENTER_NOW']*2, recovery=True)
    assert result['recovery_diagnostics']['later_parent_enter_observed_opportunity_count'] == 1
    assert result['recovery_diagnostics']['parent_enter_not_observed_opportunity_count'] == 0
    assert result['recovery_diagnostics']['terminal_nonentry_proven'] is False
    assert result['comparable_attempt_count'] == 1


def test_new_machine_same_day_selection_and_holdout_seed_invariance(monkeypatch):
    from src.tests.test_entry_strategy_policy import one_research_candidate
    from src.engine.scalping.entry_setup_evidence import MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1
    one_research_candidate(monkeypatch)
    rows = machine_rows()
    kwargs = dict(parent=MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1, scope=('KRX', 'KRX_REGULAR'),
                  source_contract={}, machine_policy_only=True)
    result = calibration.build_main_strategy_refinement(rows, **kwargs)
    assert result['selection_basis'] == strategy.RECOVERY_SELECTION_VERSION
    assert result['promotion_pass'], result['promotion_errors']
    assert result['candidate']['evidence']['train']['replay_coverage']['exact_setup_cache_hits'] > 0
    changed = deepcopy(rows)
    for row in changed[14:]:
        row['entry_quality_path']['first_hit'] = 'exact_stop_first'
    second = calibration.build_main_strategy_refinement(changed, **kwargs)
    assert result['train_search_sha256'] == second['train_search_sha256']
    assert result['search_domain'] == second['search_domain']
    assert result['candidate']['policy_sha256'] == second['candidate']['policy_sha256']
    assert second['promotion_pass'] is False
    revised_training = deepcopy(rows)
    revised_training[0]['entry_quality_path']['gross_net_target_pct'] += .01
    revised = calibration.build_main_strategy_refinement(revised_training, previous=result, **kwargs)
    assert revised['candidate']['policy_sha256'] == result['candidate']['policy_sha256']
    assert 'strategy_frozen_training_source_mismatch' in revised['promotion_errors']
    assert 'frozen_selection_training_source_changed' in revised['promotion_errors']


def test_new_machine_recovery_rank_precedes_veto_without_using_ev():
    base = {'selection_score_version': strategy.RECOVERY_SELECTION_VERSION,
            'win_rate_pct': 80., 'selected_opportunity_count': 100,
            'recovery_metrics': {'win_rate_pct': 90., 'selected_opportunity_count': 10,
                                 'successful_opportunity_weight': 9.}}
    assert strategy.machine_admission_rank(base) == strategy.machine_admission_rank({**base, 'selected_path_ev_pct': -100})
    many = deepcopy(base)
    many['recovery_metrics'].update(selected_opportunity_count=20, successful_opportunity_weight=18.)
    assert strategy.machine_admission_rank(many) > strategy.machine_admission_rank(base)


def test_new_machine_calculation_date_cannot_fall_back_to_old_ranking_when_today_source_missing(monkeypatch):
    from src.tests.test_entry_strategy_policy import one_research_candidate
    from src.engine.scalping.entry_setup_evidence import MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1
    one_research_candidate(monkeypatch)
    result = calibration.build_main_strategy_refinement(machine_rows(day='2026-10-01'),
        parent=MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1, scope=('KRX','KRX_REGULAR'),
        source_contract={'natural_machine_source_receipt': {'target_date':'2026-10-02'}},
        machine_policy_only=True)
    assert result['selection_basis'] == strategy.RECOVERY_SELECTION_VERSION
    assert not result['promotion_pass']


def test_independent_joint_slots_relax_two_simultaneous_blockers_without_anchor():
    from src.engine.scalping.entry_setup_evidence import MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1
    parent = strategy.seed(MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1, ('KRX','KRX_REGULAR'))
    profile = strategy.default_profile(parent)
    names = ['overextension_runup_pct', 'overextension_vwap_bp']
    domains = {k: [v] for k,v in profile.items()}
    for k in names:
        domains[k] = sorted(set(domains[k] + list(strategy.REGISTRY[k][1])))
    candidates = list(strategy.joint_candidates(parent, ('KRX','KRX_REGULAR'), domains=domains,
        local_first=True, priority_coordinates=names, admission_expansion=True, recovery_anchor=lambda: None))
    assert len(candidates) == 96
    joint = [p for p, progress in candidates if progress['allocated_group'] == 'independent_joint']
    assert any(all(strategy.default_profile(p)[name] > profile[name] for name in names) for p in joint)


def auxiliary_rows(day, *, loss_support=1, count=10):
    from src.tests.test_entry_setup_evidence import _machine_screen_case
    from src.engine.ai_prompt_contracts import ENTRY_MACHINE_AUXILIARY_COMPACT_CONTRACT_PROMPT_VERSION
    rows = []
    start = datetime.fromisoformat(day + 'T09:00:00+09:00')
    for i in range(count):
        setup, response = _machine_screen_case('PASS')
        win = i % 2 == 0
        desired = len(response['supporting_fact_ids']) + 1 if win else loss_support
        if desired > len(response['supporting_fact_ids']):
            response['supporting_fact_ids'].append(next(
                fact for fact in setup['positive_facts'] if fact not in response['supporting_fact_ids']))
        contract = {'schema': 'entry_round_trip_cost_v1', 'source_date': day,
                    'effective_venue': 'KRX', 'session_bucket': 'KRX_REGULAR',
                    'basis': 'source_bound_estimate', 'source_sha256': 'a'*64,
                    'components_pct': {'buy_fee': .01, 'sell_fee': .01, 'sell_tax': .05, 'slippage': .03}}
        rows.append({'source_date': day, 'stock_code': f'{i:06d}',
            'scanner_promotion_id': f'promotion-{i}', 'evaluation_key': f'{day}:trace-{i}',
            'decision_ts': (start + timedelta(minutes=i*15)).isoformat(),
            'effective_venue': 'KRX', 'session_bucket': 'KRX_REGULAR', 'machine_policy': {},
            'incumbent_prompt_version': ENTRY_MACHINE_AUXILIARY_COMPACT_CONTRACT_PROMPT_VERSION,
            'incumbent_verdict': 'PASS', 'input': {'entry_setup_evidence_v1': setup},
            'raw_response': response, 'parent_auxiliary_soft_policy': None,
            'natural_contract_evidence': {'semantic_validation_status': 'pass', 'decision_quality_contract_status': 'pass'},
            'source_label_identity_reasons': [],
            'ai_stage_path': {'schema': 'auxiliary_fixed_path_10m_v1',
                'first_hit': 'target_first' if win else 'adverse_first', 'target_pct': .3,
                'adverse_pct': -.7, 'end_return_pct': 0, 'sample_count': 10,
                'conservative_execution_cost_pct': .1, 'label_report_sha256': 'b'*64,
                'label_source_quality_status': 'pass', 'observed_venue': 'KRX',
                'observed_session_bucket': 'KRX_REGULAR', 'cost_scope': 'full_round_trip_source_bound',
                'entry_cost_contract': contract, 'entry_cost_contract_sha256': compact.digest(contract)}})
    return rows


def test_auxiliary_new_stage_preserves_good_pass_and_requires_exact_full_cost():
    rows = auxiliary_rows('2026-10-01') + auxiliary_rows('2026-10-02')
    projection = compact.sealed({'schema': 'compact_auxiliary_frozen_projection_v1',
                               'target_date': '2026-10-02', 'source_tuning_allowed': True, 'rows': rows})
    scope = compact.evaluate_auxiliary_stage(projection)['scope_results']['KRX|KRX_REGULAR']
    assert scope['status'] == 'candidate_selected', scope
    assert scope['selected']['successful_pass_changed_count'] == 0
    assert scope['selection_rank_version'] == 'train_top1_frozen_paired_net_ev_holdout_gate_v4'
    assert len(scope['candidates']) <= 33
    assert len(scope['prompt_variant_manifest']) == 2
    assert scope['completed_candidate_count'] < len(scope['candidates'])
    broken = deepcopy(rows)
    for row in broken:
        row['ai_stage_path']['cost_scope'] = 'counterfactual_friction_no_broker_fees'
    projection = compact.sealed({**projection, 'rows': broken})
    scope = compact.evaluate_auxiliary_stage(projection)['scope_results']['KRX|KRX_REGULAR']
    assert scope['status'] == 'incumbent_carry'
    assert 'stage_full_cost_contract_missing' in scope['holdout_errors']


def test_cumulative_projection_keeps_first_day_beyond_four_days_and_streams_hash(tmp_path):
    root = tmp_path / 'report/ai_entry_setup_paired_replay_batch'
    root.mkdir(parents=True)
    for ordinal in range(6):
        day = (datetime(2026,9,29) + timedelta(days=ordinal)).date().isoformat()
        value = compact.sealed({'schema': 'compact_auxiliary_frozen_projection_v1',
            'source_projection_contract': compact.SOURCE_PROJECTION_CONTRACT,
            'target_date': day, 'source_tuning_allowed': True, 'rows': auxiliary_rows(day, count=2)})
        compact.write(root / f'compact_auxiliary_paired_economic_{day}.source.json', value)
    combined = compact.auxiliary_population_projection(value, root)
    assert len(combined['history_projection_sha256s']) == 5
    assert '2026-09-29' in combined['history_projection_sha256s']
    assert isinstance(combined['rows'], validation.FrozenRows)
    assert compact.digest(combined) == compact.digest({**combined, 'rows': list(combined['rows'])})
    assert compact.valid(combined)
    replay = compact.auxiliary_population_projection(value, root, history_hashes=combined['history_projection_sha256s'])
    assert combined['artifact_content_sha256'] == replay['artifact_content_sha256']


def test_machine_projection_large_cache_preserves_hash_rows_and_reuse(tmp_path):
    import json
    path = tmp_path / 'projection.json'
    kernels = {'code.py': 'a' * 64}
    value = compact.sealed({'contract': {'kernels': kernels},
                            'rows': [{'evidence': 'x' * (65 * 1024 * 1024), 'cost': None}],
                            'census': {'captured': 1}})
    calibration._write_machine_projection(path, value)
    compressed = path.with_suffix('.json.gz')
    assert compressed.stat().st_size < 64 * 1024 * 1024
    read = calibration._read_machine_projection(path, kernels=kernels)
    assert read == value
    assert read['artifact_content_sha256'] == compact.digest({k:v for k,v in value.items() if k != 'artifact_content_sha256'})
    assert calibration._read_machine_projection(path, kernels={'code.py': 'b' * 64}) == {}


def test_machine_projection_cache_invalid_inputs_do_not_create_rows(tmp_path, monkeypatch):
    import json
    path = tmp_path / 'projection.json'
    kernels = {'code.py': 'a' * 64}
    for payload in ([], {'contract': []}, {'contract': {'kernels': kernels}, 'rows': [{'cost': 1}]}):
        path.write_text(json.dumps(payload))
        assert calibration._read_machine_projection(path, kernels=kernels) == {}
    value = compact.sealed({'contract': {'kernels': kernels}, 'rows': [{'evidence': 'x' * 4096}]})
    calibration._write_machine_projection(path, value)
    monkeypatch.setattr(calibration, 'MACHINE_PROJECTION_MAX_BYTES', 1024)
    assert calibration._read_machine_projection(path, kernels=kernels) == {}


def test_disk_backed_machine_rows_preserve_sequence_and_content_hash():
    rows = machine_rows(3)
    frozen = validation.FrozenRows()
    frozen.extend(rows)
    assert frozen == rows and rows == frozen
    assert frozen[-1] == rows[-1] and frozen[1:] == rows[1:]
    assert compact.digest({'rows': frozen, 'census': {'captured': 3}}) == compact.digest({'rows': rows, 'census': {'captured': 3}})
    assert calibration._machine_admission_metrics(frozen, ['ENTER_NOW'] * 3, recovery=True) == calibration._machine_admission_metrics(rows, ['ENTER_NOW'] * 3, recovery=True)
    assert calibration.build_machine_decision_case_table(frozen) == calibration.build_machine_decision_case_table(rows)


def test_machine_daily_projection_reuses_raw_and_invalidates_changed_date(tmp_path, monkeypatch):
    directory = tmp_path / 'ai_decision_payloads'
    directory.mkdir()
    for day in ('2026-10-01', '2026-10-02'):
        (directory / f'ai_decision_payloads_{day}.jsonl').write_text('{}\n')
    calls = []
    def raw_loader(root, *, target_date, **kwargs):
        calls.append(target_date)
        return machine_rows(1, target_date), {'captured': 1, 'microstructure_capture_population': {
            'verified_capture_count': 1, 'unique_verified_capture_count': 1,
            'duplicate_capture_collapsed_count': 0, 'partitions': [{'capture_count': 1}]}}
    monkeypatch.setattr(calibration, '_load_machine_observation_rows_uncached', raw_loader)
    rows, census = calibration.load_machine_observation_rows(tmp_path, target_date='2026-10-02')
    assert calls == ['2026-10-01', '2026-10-02']
    assert census['microstructure_capture_population']['unique_verified_capture_count'] == 2
    again, reuse = calibration.load_machine_observation_rows(tmp_path, target_date='2026-10-02')
    assert again == rows and len(calls) == 2
    assert all(r['cache_reused'] and not r['raw_reloaded'] for r in reuse['frozen_projection_receipts'])
    (directory / 'ai_decision_payloads_2026-10-02.jsonl').write_text('{"new":true}\n')
    calibration.load_machine_observation_rows(tmp_path, target_date='2026-10-02')
    assert calls == ['2026-10-01', '2026-10-02', '2026-10-02']
    # The normal after-close caller supplies a fetcher. It must still reuse
    # history and never pass today's date-bound fetcher to an earlier date.
    def fetch_loader(root, *, target_date, completed_price_fetcher, **kwargs):
        assert target_date == '2026-10-02' and completed_price_fetcher is not None
        return raw_loader(root, target_date=target_date)
    monkeypatch.setattr(calibration, '_load_machine_observation_rows_uncached', fetch_loader)
    calibration.load_machine_observation_rows(tmp_path, target_date='2026-10-02',
        completed_price_fetcher=lambda *args: None,
        completed_price_as_of=datetime.fromisoformat('2026-10-02T20:05:00+09:00'))
    assert calls[-1] == '2026-10-02' and len(calls) == 4


def test_auxiliary_top_train_choice_cannot_be_replaced_by_holdout_runner_up(monkeypatch):
    from src.engine.scalping import entry_setup_evidence as owner
    rows = auxiliary_rows('2026-10-01') + auxiliary_rows('2026-10-02')
    from src.tests.test_entry_setup_evidence import _machine_screen_case
    for row in rows:
        if row['stock_code'] == '000009':
            setup, response = _machine_screen_case('VETO')
            row.update(incumbent_verdict='VETO', raw_response=response,
                       input={'entry_setup_evidence_v1': setup})
    tags = {id(row['input']['entry_setup_evidence_v1']): (row['source_date'], int(row['stock_code'])) for row in rows}
    original = owner._evaluate_auxiliary_policy_validated
    def replay(response, setup, policy, errors):
        result = original(response, setup, policy, errors)
        if isinstance(policy, dict) and policy.get('schema') == 'auxiliary_soft_policy_v1':
            axis = policy['veto_min_independent_evidence_count']
            day, i = tags[id(setup)]
            train = day == '2026-10-01'
            # Best train axis blocks every loss, but loses a held success.
            # Runner-up blocks fewer train losses and succeeds on holdout.
            blocked = ((i % 2 == 1 if train else i == 0) if axis == 2
                       else i in (1,3) if axis == 3 else False)
            result = {**result, 'effective_verdict': 'CAUTION' if blocked else 'PASS', 'validation_errors': []}
        return result
    monkeypatch.setattr(owner, '_evaluate_auxiliary_policy_validated', replay)
    projection = compact.sealed({'schema': 'compact_auxiliary_frozen_projection_v1',
        'target_date': '2026-10-02', 'source_tuning_allowed': True, 'rows': rows})
    scope = compact.evaluate_auxiliary_stage(projection)['scope_results']['KRX|KRX_REGULAR']
    assert scope['frozen_train_choice']['policy']['veto_min_independent_evidence_count'] == 2
    assert any(t['policy'] and t['policy'].get('veto_min_independent_evidence_count') == 3
               and t['holdout_paired_delta_ev_pct'] > 0 and t['successful_pass_changed_count'] == 0
               for t in scope['candidates'])
    assert scope['status'] == 'incumbent_carry'
    assert scope['holdout_errors'] == ['frozen_train_candidate_holdout_failed']


def test_auxiliary_selection_survives_retry_and_blocks_corrected_train_source(tmp_path):
    rows = auxiliary_rows('2026-10-01') + auxiliary_rows('2026-10-02')
    projection = compact.sealed({'schema': 'compact_auxiliary_frozen_projection_v1',
        'target_date': '2026-10-02', 'source_tuning_allowed': True, 'rows': rows})
    stage = compact.evaluate_auxiliary_stage(projection)
    path = tmp_path / 'choice.json'
    choices = compact.freeze_auxiliary_selection(path, '2026-10-02', stage)
    assert choices
    scope = 'KRX|KRX_REGULAR'
    repeated = compact.evaluate_auxiliary_stage(projection, frozen_choices=choices)
    assert repeated['scope_results'][scope]['status'] == 'candidate_selected'
    assert compact.freeze_auxiliary_selection(path, '2026-10-02', repeated) == choices
    report = {'auxiliary_train_selection': compact.read(path)}
    assert compact.replay_auxiliary_stage(projection, report) == repeated
    changed = deepcopy(rows)
    changed[0]['ai_stage_path']['target_pct'] = .4
    changed_projection = compact.sealed({**projection, 'rows': changed})
    corrected = compact.evaluate_auxiliary_stage(changed_projection, frozen_choices=choices)
    assert corrected['scope_results'][scope]['status'] == 'incumbent_carry'
    assert 'frozen_selection_source_changed' in corrected['scope_results'][scope]['holdout_errors']
    assert compact.freeze_auxiliary_selection(path, '2026-10-02', corrected) == choices
    with pytest.raises(ValueError, match='selection_invalid'):
        compact.freeze_auxiliary_selection(path, '2026-10-03', corrected)
    path.write_text('{broken')
    with pytest.raises(ValueError, match='selection_invalid'):
        compact.freeze_auxiliary_selection(path, '2026-10-02', corrected)


def test_auxiliary_pass_only_does_not_tune_unobserved_veto_axis():
    rows = auxiliary_rows('2026-10-01') + auxiliary_rows('2026-10-02')
    projection = compact.sealed({'schema': 'compact_auxiliary_frozen_projection_v1',
        'target_date': '2026-10-02', 'source_tuning_allowed': True, 'rows': rows})
    stage = compact.evaluate_auxiliary_stage(projection)
    for trial in stage['scope_results']['KRX|KRX_REGULAR']['candidates']:
        policy = trial['policy']
        if not policy:
            continue
        profiles = ([policy['parent']] + [leaf['profile'] for leaf in policy['leaves']]
                    if policy['schema'] == 'auxiliary_soft_policy_v2' else [policy])
        assert all(p['veto_min_independent_evidence_count'] == 2 for p in profiles)


def test_auxiliary_cost_contract_checks_hash_date_and_sum():
    row = auxiliary_rows('2026-10-02', count=1)[0]
    assert compact.stage_full_cost_valid(row)
    for change in ('date', 'hash', 'sum'):
        invalid = deepcopy(row)
        path = invalid['ai_stage_path']
        if change == 'date':
            path['entry_cost_contract']['source_date'] = '2026-10-01'
            path['entry_cost_contract_sha256'] = compact.digest(path['entry_cost_contract'])
        elif change == 'hash':
            path['entry_cost_contract_sha256'] = '0'*64
        else:
            path['conservative_execution_cost_pct'] = 0
        assert not compact.stage_full_cost_valid(invalid)


def test_auxiliary_isolates_identifiable_missing_cost_without_blocking_valid_rows():
    rows = auxiliary_rows('2026-10-01') + auxiliary_rows('2026-10-02')
    rows[0]['ai_stage_path']['cost_scope'] = 'counterfactual_friction_no_broker_fees'
    projection = compact.sealed({'schema': 'compact_auxiliary_frozen_projection_v1',
        'target_date': '2026-10-02', 'source_tuning_allowed': True, 'rows': rows})
    scope = compact.evaluate_auxiliary_stage(projection)['scope_results']['KRX|KRX_REGULAR']
    assert scope['status'] == 'candidate_selected', scope
    assert scope['cost_incomplete_diagnostic_count'] == 1
    assert scope['full_cost_candidate_population_count'] == 19
    assert scope['selected']['eligible_count'] == 19


def test_auxiliary_publisher_defers_old_machine_parent_without_overwriting_machine(tmp_path, monkeypatch):
    from src.engine.scalping import mechanistic_entry_runtime_policy as policy
    from src.tests.test_mechanistic_entry_runtime_policy import initial
    from src.tests.test_entry_setup_paired_replay_batch import full_compact_proof
    parent = initial(tmp_path)
    future = deepcopy(parent)
    future.update(publication_date='2026-09-18', target_date='2026-09-21')
    future['machine_policy'] = strategy.seed(parent['machine_policy'], ('KRX', 'KRX_REGULAR'))
    future['bundle_sha256'] = policy.digest({k:v for k,v in future.items() if k != 'bundle_sha256'})
    policy.validate(future, target_date='2026-09-21')
    policy._atomic_write_json(policy.root(tmp_path) / 'policy_2026-09-21.json', future)
    projection = compact.sealed({'schema': 'compact_auxiliary_frozen_projection_v1',
                                'target_date': '2026-09-17', 'rows': []})
    compact.write(compact.report_path(tmp_path, '2026-09-17').with_suffix('.source.json'), projection)
    stage = compact.sealed({'schema': 'auxiliary_ai_stage_evaluation_v1',
        'source_date': '2026-09-17', 'source_projection_sha256': projection['artifact_content_sha256'],
        'source_manifest_sha256': 'd'*64, 'source_tuning_allowed': True, 'additional_provider_calls': 0,
        'scope_results': {'KRX|KRX_REGULAR': {
            'selection_rank_version': 'train_top1_frozen_paired_net_ev_holdout_gate_v4',
            'status': 'candidate_selected',
            'parent_prompt_versions': [parent['ai_policy']['prompt_version']],
            'parent_soft_policy_sha256s': [compact.digest(None)],
            'parent_machine_bundle_sha256s': [parent['bundle_sha256']],
            'selected': {'policy': {'schema': 'auxiliary_soft_policy_v1',
                         'veto_min_independent_evidence_count': 2, 'pass_min_positive_evidence_count': 3}}}}})
    source = full_compact_proof()
    source.update(candidate_improvement_proven=False, promotion_pass=False,
        candidate_selection=compact.sealed({'schema': compact.CANDIDATE_SELECTION_SCHEMA, 'status': 'insufficient_sample'}),
        promotion_scopes=[], machine_parent_bundle_sha256s=[parent['bundle_sha256']],
        source_projection_sha256=projection['artifact_content_sha256'], auxiliary_stage=stage)
    monkeypatch.setattr(compact, 'evaluate_auxiliary_stage', lambda _: stage)
    receipt = {'source_manifest_sha256': 'd'*64, 'target_date': '2026-09-17', 'tuning_input_allowed': True,
        'machine_terminal_tuning_gate': {'decision_counterfactual_tuning_input_allowed': True},
        'compact_auxiliary_policy_measurement': {'measurement_allowed': True}}
    published = policy.publish_compact_evaluation(compact.sealed(source), source_receipt=receipt,
        publication_day='2026-09-18', data_root=tmp_path,
        now=datetime.fromisoformat('2026-09-18T20:00:00+09:00'))
    assert published['machine_policy'] == future['machine_policy']
    assert published['ai_policy'] == parent['ai_policy']
    assert published['auxiliary_soft_deferred_scopes'] == {'KRX|KRX_REGULAR': 'new_machine_parent_requires_auxiliary_revalidation'}
    assert policy.load(data_root=tmp_path, target_date='2026-09-21') == published
