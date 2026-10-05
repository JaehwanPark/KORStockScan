from copy import deepcopy
from datetime import datetime
import json

import pytest

from src.engine.scalping import entry_observation_recipe_policy as R
from src.engine.scalping import ai_action_outcome_calibration as C


def observation(trace='a', symbol='000660', ts='2026-09-29T09:00:00+09:00',
                status='target', parent='ENTER_NOW', candidate='ENTER_NOW'):
    return dict(trace=trace, symbol=symbol, day=ts[:10], ts=ts,
        parent_action=parent, candidate_action=candidate, raw_sha256='a' * 64,
        native_provenance=None, source_lane='machine_observation_counterfactual_no_provider',
        path=dict(status=status, delay_sec=60 if status in {'target', 'stop'} else None,
            net_pct=.1 if status == 'target' else -1 if status == 'stop' else None))


def test_repeated_observations_do_not_inflate_cluster_support():
    rows = [observation(str(i)) for i in range(100)] + [observation('loss', '000001', status='stop')]
    result = R.metrics(rows)
    assert result['selected_observation_count'] == 101
    assert result['boundary_cluster_count'] == 2
    assert result['win_rate_pct'] == 50
    assert result['observation_weighted_win_rate_pct'] > 99


def test_missing_first_entry_keeps_occupancy_and_does_not_pick_later_winner():
    rows = [observation(status='first_partial_bar_ambiguous'),
        observation('later', ts='2026-09-29T09:10:00+09:00')]
    result = R.replay(rows, 'candidate_action')
    assert [r['trace'] for r in result] == ['a']
    assert R.metrics(result)['win_rate_pct'] is None


def test_unresolved_parent_not_treated_as_zero_winrate():
    rows = [observation(status='timeout', candidate='RECHECK'),
        observation('b', '000002', parent='RECHECK')]
    result = R.compare(rows)
    assert result['candidate']['win_rate_pct'] == 100
    assert not result['improves'] and result['reasons'] == ['baseline_boundary_unresolved']


def test_success_can_be_removed_while_better_candidate_is_selected():
    rows = [observation('old-win', '000001', candidate='RECHECK')]
    rows += [observation(str(i), f'{i+2:06}', status='stop', candidate='RECHECK') for i in range(8)]
    rows += [observation('new' + str(i), f'{i+20:06}', parent='RECHECK') for i in range(8)]
    result = R.compare(rows)
    assert result['improves']
    assert 'old-win' not in result['candidate']['selected_ids']


def test_thinning_is_blind_to_actions_and_outcomes():
    rows = [observation('a'), observation('b', ts='2026-09-29T09:01:00+09:00'),
        observation('c', ts='2026-09-29T09:10:00+09:00')]
    altered = deepcopy(rows)
    for row in altered:
        row['candidate_action'] = 'BLOCK'
        row['path']['status'] = 'stop'
    assert [r['trace'] for r in R.thin(rows)] == [r['trace'] for r in R.thin(altered)] == ['a', 'c']


def test_comparison_cannot_reselect_failed_training_candidate():
    train = [observation('t', status='stop', parent='RECHECK')]
    held = [observation('h', ts='2026-10-02T09:00:00+09:00', parent='RECHECK')]
    result = R._selection(train + held, boundary='2026-09-30', recipe={'id': 'fixed'})
    assert result['later_comparison']['improves']
    assert result['selected_on_train'] is None and result['selected_observation_recipe'] is None


def cost_path():
    row = dict(decision_trace_id='a', source_date='2026-09-29', stock_code='000660',
        decision_ts='2026-09-29T09:00:30+09:00', machine_action='RECHECK',
        setup_evidence=dict(strategy_raw_input=dict(quote=dict(best_ask=100))),
        comparison=dict(entry_cost_contract=dict(schema='entry_round_trip_cost_v1',
            source_date='2026-09-29', effective_venue='KRX', session_bucket='KRX_REGULAR',
            basis='source_bound_estimate', source_sha256='a' * 64,
            components_pct=dict(buy_fee=.015, sell_fee=.015, sell_tax=.2, slippage=.07))))
    outcome = dict(trace='a', day=row['source_date'], symbol='000660', ts=row['decision_ts'],
        tags=dict(venue='KRX', session='KRX_REGULAR'), action='RECHECK',
        features=dict(entry_cost_pct=.3), capture_valid=True, reference_type='executable_ask',
        reference_price=100, paths={'60m':dict(status='late_target_first', delay_sec=90,
            requested_seconds=3600, requested_end='2026-09-29T10:00:30+09:00', gaps=[])})
    return row, outcome


@pytest.mark.parametrize('damage,reason',[
    ('identity', 'horizon_identity_mismatch'), ('cost', 'cost_missing_or_mismatched'),
    ('ask', 'entry_reference_mismatch'), ('partial', 'first_partial_bar_ambiguous'),
    ('gap', 'price_gap_before_hit'), ('clock', 'horizon_hit_clock_invalid'),
    ('horizon', 'horizon_contract_invalid')])
def test_path_bindings_fail_closed(damage, reason):
    row, outcome = cost_path()
    if damage == 'identity': outcome['symbol'] = '005930'
    elif damage == 'cost': outcome['features']['entry_cost_pct'] = .1
    elif damage == 'ask': outcome['reference_price'] = 99
    elif damage == 'partial': outcome['paths']['60m']['delay_sec'] = 30
    elif damage == 'gap': outcome['paths']['60m']['gaps'] = [dict(to_ts=datetime.fromisoformat(row['decision_ts']).timestamp()+60)]
    elif damage == 'clock': outcome['paths']['60m']['delay_sec'] = 4000
    elif damage == 'horizon': outcome['paths']['60m']['requested_seconds'] = 600
    result = R._path(row, outcome)
    assert result == dict(status=reason, net_pct=None, delay_sec=None)


def test_valid_hit_before_later_gap_still_counts_and_cost_is_not_zero():
    row, outcome = cost_path()
    path = outcome['paths']['60m']
    path['gaps'] = [dict(to_ts=datetime.fromisoformat(row['decision_ts']).timestamp()+600)]
    assert R._path(row, outcome)['net_pct'] == .1
    path['status'] = 'stop_first'
    assert R._path(row, outcome)['net_pct'] == pytest.approx(-1)


def test_source_accepts_missing_promotion_but_rejects_future_capture(monkeypatch):
    row, _ = cost_path()
    raw = row['setup_evidence']['strategy_raw_input']
    raw.update(stock_code='000660', effective_venue='KRX', session_bucket='krx_regular',
        entry_machine_input_as_of=datetime.fromisoformat(row['decision_ts']).timestamp())
    row['setup_evidence']['strategy_raw_sha256'] = R.S.digest(raw)
    row['evaluation_attempt_id'] = 'probe-exact-attempt'
    monkeypatch.setattr(C, '_machine_source_contract_valid', lambda r: True)
    assert R._source_error(row, through='2026-10-02') is None
    raw['entry_machine_input_as_of'] += 1
    row['setup_evidence']['strategy_raw_sha256'] = R.S.digest(raw)
    assert R._source_error(row, through='2026-10-02') == 'observation_capture_cutoff_invalid'


def test_expression_is_scope_parent_kernel_and_authority_bound():
    value = R.expression('samsung', {})
    assert not R.validate_expression(value, {})
    for key, replacement in [('recipe_id', 'other'), ('parent_sha256', 'f'*64),
            ('allowed_runtime_apply', True), ('kernel_sha256', '0'*64)]:
        modified = {**value, key: replacement}
        assert R.validate_expression(modified, {})


def test_actual_generator_dispatch_is_isolated_and_never_loads_live(monkeypatch):
    from src.engine.scalping import mechanistic_entry_runtime_policy as live
    monkeypatch.setattr(live, 'load_effective', lambda **kw: pytest.fail('live loader called'))
    monkeypatch.setattr(R, 'build_report', lambda req, **kw: {'seen': req, **kw})
    result = C.build_machine_policy_report([], source_receipt={}, target_date='2026-10-02',
        observation_recipe_request={'frozen': True})
    assert result == dict(seen={'frozen':True}, target_date='2026-10-02')
    with pytest.raises(ValueError, match='must_be_isolated'):
        C.build_machine_policy_report([], source_receipt={}, target_date='2026-10-02',
            observation_recipe_request={}, write_checkpoints=True)


def test_file_manifest_and_duplicate_rows_are_checked(tmp_path):
    paths = []
    for role in ('capture', 'horizon', 'samsung_receipt'):
        path = tmp_path / (role + '.json')
        path.write_text('[]')
        paths.append(dict(role=role, path=str(path), sha256=R.file_sha(path)))
    R._verify_files(paths)
    path.write_text('[1]')
    with pytest.raises(ValueError, match='file_changed'):
        R._verify_files(paths)
    indexed, conflicts = R._index([dict(trace='x'), dict(trace='x'), dict(trace='valid')], 'trace')
    assert indexed == {'valid': {'trace': 'valid'}} and conflicts == {'x'}


def test_live_policy_validator_rejects_observation_expression():
    from src.engine.scalping.entry_setup_evidence import validate_mechanistic_entry_threshold_policy
    assert validate_mechanistic_entry_threshold_policy(R.expression('non_samsung', {}))


def test_probe_request_reaches_generator_selection_without_native_ids(monkeypatch, tmp_path):
    from src.engine.scalping import entry_setup_evidence as E
    from src.engine.scalping import entry_pullback_buy_flow_research as P
    captures, outcomes = [], []
    for day in ('2026-09-29', '2026-10-02'):
        row, outcome = cost_path()
        row.update(source_date=day, decision_trace_id=day, decision_ts=day+'T09:00:30+09:00',
            effective_venue='KRX', session_bucket='KRX_REGULAR')
        row['setup_evidence']['strategy_raw_sha256'] = 'a'*64
        row['comparison']['entry_cost_contract']['source_date'] = day
        outcome.update(trace=day, day=day, ts=row['decision_ts'])
        outcome['paths']['60m']['requested_end'] = day+'T10:00:30+09:00'
        captures.append(row)
        outcomes.append(outcome)
    files = []
    for role, content in [('capture', captures), ('horizon', outcomes), ('samsung_receipt', [])]:
        path = tmp_path / (role+'.json')
        path.write_text(json.dumps({'rows': content} if role == 'capture' else content))
        files.append(dict(role=role, path=str(path), sha256=R.file_sha(path)))
    monkeypatch.setattr(E, 'validate_mechanistic_entry_threshold_policy', lambda p: [])
    monkeypatch.setattr(R, '_source_error', lambda *a, **kw: None)
    monkeypatch.setattr(P, 'evaluate', lambda *a, **kw:dict(parent_action='RECHECK',
        proposed_action='ENTER_NOW', condition_match=True))
    request = dict(schema=R.REQUEST, target_date='2026-10-02', training_through_date='2026-09-30',
        evaluation_unit=R.UNIT, pristine_holdout=False, parent_policy={}, parent_sha256=R.S.digest({}),
        files=files, expressions={g:R.expression(g, {}) for g in R.GROUPS})
    result = C.build_machine_policy_report([], source_receipt={}, target_date='2026-10-02',
        observation_recipe_request=request)
    assert result['parent_replay_count'] == 2 and not result['exclusions']
    assert result['selections']['non_samsung']['observational_candidate_supported']
    assert all(r['native_provenance'] is None for r in result['observations'])
    assert result['policy_by_scope'] == {} and result['promotion_pass'] is False
    capture_file = next(f for f in files if f['role'] == 'capture')
    from pathlib import Path
    Path(capture_file['path']).write_text(json.dumps({'rows': captures + [captures[0]]}))
    capture_file['sha256'] = R.file_sha(capture_file['path'])
    localized = R.build_report(request, target_date='2026-10-02')
    assert localized['parent_replay_count'] == 1
    assert localized['exclusion_counts'] == {'capture_identity_conflict': 1}
    assert localized['observations'][0]['day'] == '2026-10-02'
    request['expressions']['samsung'] = request['expressions']['non_samsung']
    with pytest.raises(ValueError, match='expression_invalid'):
        R.build_report(request, target_date='2026-10-02')


def test_runtime_activation_rejects_report_before_creating_runtime_directory(tmp_path):
    from src.engine.scalping import mechanistic_entry_runtime_policy as live
    path = tmp_path / 'report.json'
    report = dict(schema=R.REPORT, **R.AUTHORITY, policy_by_scope={})
    report['artifact_content_sha256'] = R.S.digest(report)
    path.write_text(json.dumps(report))
    data = tmp_path / 'isolated-data'
    with pytest.raises(ValueError, match='activation_source_invalid'):
        live.activate_strategy_report(path, data_root=data)
    assert not data.exists()
