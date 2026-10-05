from copy import deepcopy
from datetime import datetime
import json

import pytest

from src.engine.scalping import entry_admission_acceptance as V
from src.engine.scalping import entry_admission_analysis as H
from src.engine.scalping import entry_admission_recipe as A
from src.engine.scalping import entry_strategy_policy as S
from src.engine.scalping import mechanistic_entry_runtime_policy as M
from src.engine.scalping import ai_action_outcome_calibration as C


def observations(days=('2026-09-29', '2026-10-06')):
    rows = []
    for day in days:
        # Select 40% of the baseline, drop a winning baseline observation, and
        # improve enough in both splits. No fabricated native IDs are needed.
        for i in range(100):
            win = i < 39 or i == 40
            rows.append(dict(trace=f'{day}:{i}', day=day, symbol=f'{i+1:06}',
                ts=f'{day}T09:01:00+09:00', group='non_samsung',
                raw_sha256='a' * 64, outcome_request_code=f'{i+1:06}_AL',
                source_bundle_sha256='b' * 64, scope=['KRX', 'KRX_REGULAR'],
                source_lane='original_capture', native_provenance=None,
                parent_action='ENTER_NOW', candidate_action='ENTER_NOW' if i < 40 else 'RECHECK',
                path=dict(status='target' if win else 'stop', net_pct=.1 if win else -1., delay_sec=60)))
    return rows


def evaluate(rows, consumed=None):
    return V.evaluate({'observations': rows}, target_date=max(r['day'] for r in rows), consumed_dates=consumed or [])


def test_selection_without_coverage_or_winner_retention_veto():
    result = evaluate(observations())
    assert result['candidate_selected'] and result['fresh_validation'] == 'passed'
    assert result['selection_coverage'] == {'train': .4, 'holdout': .4}
    assert result['success_retention_diagnostics']['train']['excluded_wins'] == 1
    assert result['candidate']['train']['native_selected_count'] == 0


def test_discovery_not_forward_and_metrics_survive_nonselection():
    result = evaluate(observations(('2026-09-29', '2026-10-02')))
    assert result['candidate_computed'] and result['candidate_train_qualified']
    assert not result['candidate_validation_evaluated'] and not result['candidate_selected']
    assert result['fresh_validation'] == 'not_observed'
    assert result['candidate']['train']['selected_observation_count'] == 80
    assert result['candidate']['train']['win_rate_pct'] == 97.5


def test_candidate_empty_day_is_not_a_missing_source_day():
    rows = observations(('2026-09-29', '2026-09-30', '2026-10-06'))
    for row in rows:
        if row['day'] == '2026-09-30':
            row['candidate_action'] = 'RECHECK'
    result = evaluate(rows)
    assert result['candidate_selected']
    assert result['train_dates'] == ['2026-09-29', '2026-09-30']
    assert result['candidate']['train']['selected_source_dates'] == ['2026-09-29']
    assert result['source_date_census']['2026-09-30']['observation_count'] == 100


def test_repeated_observations_do_not_inflate_support():
    rows = observations()
    rows.extend({**r, 'trace': r['trace'] + ':retry', 'ts': r['ts'].replace('09:01', '09:02')} for r in deepcopy(rows))
    result = evaluate(rows)
    assert result['candidate']['holdout']['boundary_cluster_count'] == 40


def test_baseline_unknown_and_train_failure_do_not_consume_holdout():
    rows = observations()
    for row in rows:
        if row['day'] == '2026-09-29':
            row['path'] = dict(status='timeout', net_pct=None, delay_sec=None)
    result = evaluate(rows)
    assert result['candidate_computed'] and not result['candidate_train_qualified']
    assert not result['candidate_validation_evaluated']
    assert result['baseline']['train']['win_rate_pct'] is None
    assert result['selected_holdout_manifest_sha256'] is None


def test_consumed_latest_date_cannot_make_an_older_day_holdout():
    result = evaluate(observations(('2026-09-29', '2026-10-06', '2026-10-07')), ['2026-10-07'])
    assert result['holdout_dates'] == [] and not result['candidate_selected']


def test_winner_retention_is_an_identity_intersection():
    rows = observations()
    old = [r for r in rows if r['path']['status'] == 'target'][:17]
    new = [{**old[0], 'trace': 'new-winner'}]
    diagnostic = V._retention(old, new)
    assert (diagnostic['retained_wins'],diagnostic['new_wins'],diagnostic['excluded_wins']) == (0,1,17)


def test_already_adopted_recipe_can_be_carried_again():
    from src.tests.test_entry_strategy_policy import policy
    parent = A.candidate_policy(policy())
    rows = observations()
    for row in rows:
        row['parent_action'] = row['candidate_action']
    result = V.apply(dict(target_date='2026-10-06',consumed_holdout_dates=[]), {'observations':rows},parent)
    assert result['disposition'] == 'incumbent_carried'
    assert result['candidate_policy'] is None and result['candidate_computed']


@pytest.mark.parametrize('change', [dict(raw_sha256=None), dict(scope=['NXT', 'NXT']),
    dict(ts='2026-09-30T09:01:00+09:00'), dict(symbol='005930'),
    dict(path=dict(status='target', net_pct=float('nan'), delay_sec=60))])
def test_invalid_source_rejected(change):
    rows = observations()
    rows[0].update(change)
    with pytest.raises(ValueError):
        evaluate(rows)


def test_generator_publisher_loader_share_selection(tmp_path):
    bootstrap = tmp_path / 'bootstrap.json'
    C._atomic_write_json(bootstrap, C._with_artifact_content_sha256(dict(schema=C.SCHEMA,
        target_date='2026-09-11', clean_tuning_baseline_date='2026-06-05',
        mechanistic_entry_refinement=dict(policy_candidate=None, promotion_pass=False),
        mechanistic_flow_groups=dict(source_population=dict(accepted_unique_trace_count=15)))))
    previous = M.publish(bootstrap, data_root=tmp_path, bootstrap=True,
        now=datetime(2026, 9, 13, 20, tzinfo=M.KST))
    previous['machine_policy'] = S.seed(previous['machine_policy'], ('KRX', 'KRX_REGULAR'))
    previous['machine_policy']['entry_situation_veto'] = C._winrate_veto_payload(68.75)
    previous['bundle_sha256'] = S.digest({k:v for k,v in previous.items() if k != 'bundle_sha256'})
    for path in [M.root(tmp_path) / 'policy_2026-09-14.json',
                 M.root(tmp_path) / 'generations' / f"{previous['bundle_sha256']}.json"]:
        M._atomic_write_json(path, previous)
    parent = M.for_cohort(previous, ('KRX', 'KRX_REGULAR'))['machine_policy']
    analysis = H.build_report([], parent=parent, target_date='2026-10-06', data_root=tmp_path)
    analysis['observations'] = observations()
    analysis['artifact_content_sha256'] = S.digest({k:v for k,v in analysis.items() if k != 'artifact_content_sha256'})
    report = C.build_winrate_policy_report([], source_receipt=dict(target_date='2026-10-06',
        machine_threshold_tuning_input_allowed=True), target_date='2026-10-06', data_root=tmp_path,
        publication_day='2026-10-06', admission_recipe_id=A.RECIPE_ID, admission_analysis=analysis)
    assert V.validate_source(report, require_files=True)['candidate_selected']
    current_before = M._load_current(tmp_path, '2026-10-06')
    source = tmp_path / 'report.json'
    M._atomic_write_json(source, report)
    staged = M.stage_winrate_policy(source, data_root=tmp_path,
        now=datetime(2026, 10, 6, 20, tzinfo=M.KST))
    assert staged['status'] == 'staged'
    loaded = M.load(data_root=tmp_path, target_date='2026-10-07')
    assert M.for_cohort(loaded, ('KRX', 'KRX_REGULAR'))['machine_policy'] == A.candidate_policy(parent)
    assert M._load_current(tmp_path, '2026-10-06') == current_before
    receipts = list((M.root(tmp_path) / 'winrate_holdouts').glob('*.json'))
    receipt = json.loads(receipts[0].read_text())
    assert receipt['evaluation_unit'] == V.UNIT and receipt['selected_boundary_cluster_count'] == 40
    for field, value in [('candidate_selected', False), ('candidate_computed', 1),
                         ('holdout_dates', ['2026-10-02']), ('acceptance_contract', 'unknown')]:
        bad = deepcopy(report)
        bad[field] = value
        with pytest.raises(ValueError):
            V.validate_source(bad)
