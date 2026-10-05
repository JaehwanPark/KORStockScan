"""Versioned postclose acceptance of the frozen non-Samsung admission recipe.

Source-bound observations use first signals and equal symbol/date clusters.
Native identities remain diagnostics; this module cannot create orders or IDs.
Both the producer and dated publisher recompute this same contract.
"""
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
import hashlib
import math
import re

from src.engine.scalping import entry_strategy_policy as S
from src.engine.scalping import entry_observation_recipe_policy as R
from src.engine.scalping import entry_first_signal_exit_research as F

CONTRACT = 'main_machine_observation_admission_acceptance_v1'
OBJECTIVE = 'winrate_observation_first_signal_without_retention_v1'
DISCOVERY_THROUGH = '2026-10-02'
UNIT = R.UNIT


def kernel_sha256():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _day(value):
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError('admission_acceptance_date_invalid')
    return value


def _rows(analysis, target_date):
    rows = []
    for row in analysis['observations']:
        if row.get('group') == 'samsung':
            continue
        if (row.get('group') != 'non_samsung' or row.get('symbol') == '005930'
            or not re.fullmatch(r'\d{6}', str(row.get('symbol') or ''))
            or not '2026-09-29' <= _day(row.get('day')) <= target_date
            or row.get('scope') != ['KRX', 'KRX_REGULAR']
            or any(row.get(k) not in {'BLOCK', 'RECHECK', 'ENTER_NOW'}
                   for k in ('parent_action', 'candidate_action'))
            or not re.fullmatch(r'[0-9a-f]{64}', str(row.get('raw_sha256') or ''))
            or not row.get('outcome_request_code') or not row.get('source_bundle_sha256')):
            raise ValueError('admission_acceptance_observation_invalid')
        stamp = F.epoch(row)
        path = row.get('path')
        if not isinstance(path, dict) or not isinstance(path.get('status'), str):
            raise ValueError('admission_acceptance_path_invalid')
        if path['status'] in {'target', 'stop'}:
            value, delay = path.get('net_pct'), path.get('delay_sec')
            clock = datetime.fromisoformat(row['ts']).astimezone(F.KST)
            close = clock.replace(hour=15, minute=30, second=0, microsecond=0).timestamp()
            if (type(value) not in (int, float) or not math.isfinite(value)
                or (path['status'] == 'target' and value != .1)
                or (path['status'] == 'stop' and value >= 0)
                or type(delay) not in (int, float) or not math.isfinite(delay)
                or not 0 < delay <= min(3600, close - stamp)):
                raise ValueError('admission_acceptance_binary_invalid')
        rows.append(row)
    return rows


def _metrics(rows, action):
    selected = R.replay(rows, action)
    metrics = R.metrics(selected)
    metrics['selected_source_dates'] = sorted({r['day'] for r in selected})
    metrics['boundary_source_dates'] = sorted({r['day'] for r in selected
                                               if r['path']['status'] in {'target', 'stop'}})
    return metrics, selected


def _hurdles(old, new, floor):
    raw = new['win_rate_pct'] is not None and old['win_rate_pct'] is not None
    support = (new['support_adjusted_win_rate_pct'] is not None
               and old['support_adjusted_win_rate_pct'] is not None)
    return dict(baseline_boundary_present=old['boundary_cluster_count'] > 0,
        selected_boundary_clusters_minimum=new['boundary_cluster_count'] >= floor,
        raw_win_rate_improves=bool(raw and new['win_rate_pct'] > old['win_rate_pct']),
        support_adjusted_win_rate_improves_5pp=bool(support and
            new['support_adjusted_win_rate_pct'] - old['support_adjusted_win_rate_pct'] >= 5))


def _retention(old, new):
    old_wins = {r['trace'] for r in old if r['path']['status'] == 'target'}
    new_wins = {r['trace'] for r in new if r['path']['status'] == 'target'}
    new_ids = {r['trace'] for r in new}
    return dict(baseline_wins=len(old_wins), retained_wins=len(old_wins & new_wins),
        excluded_wins=len(old_wins - new_ids), new_wins=len(new_wins - old_wins),
        avoided_losses=sum(r['path']['status'] == 'stop' and r['trace'] not in new_ids for r in old),
        role='diagnostic_only')


def evaluate(analysis, *, target_date, consumed_dates):
    """Freeze train choice before inspecting the latest unconsumed forward day."""
    _day(target_date)
    if not isinstance(consumed_dates, list) or consumed_dates != sorted(set(consumed_dates)):
        raise ValueError('admission_acceptance_consumed_dates_invalid')
    for day in consumed_dates:
        _day(day)
    rows = _rows(analysis, target_date)
    events = F.first_signal_events(rows)
    first = F.mask_first_signals(rows, events)
    dates = sorted({r['day'] for r in rows})
    # Never test an older unconsumed day using a newer already-consumed day as
    # training. The latest source day alone can be the forward holdout.
    held_dates = dates[-1:] if dates and dates[-1] > DISCOVERY_THROUGH and dates[-1] not in consumed_dates else []
    train_dates = [day for day in dates if day not in held_dates]
    train = [r for r in first if r['day'] in train_dates]
    held = [r for r in first if r['day'] in held_dates]
    old_train, old_rows = _metrics(train, 'parent_action')
    new_train, new_rows = _metrics(train, 'candidate_action')
    checks = _hurdles(old_train, new_train, 30)
    train_ok = bool(train_dates and all(checks.values()))
    # Do not consume a new test date to select or rescue a rejected train arm.
    old_held, old_held_rows = _metrics(held if train_ok else [], 'parent_action')
    new_held, new_held_rows = _metrics(held if train_ok else [], 'candidate_action')
    held_checks = _hurdles(old_held, new_held, 10)
    held_evaluated = bool(train_ok and held_dates)
    held_ok = held_evaluated and all(held_checks.values())
    errors = ['train:' + key for key, ok in checks.items() if not ok]
    if not train_dates:
        errors.append('train_dates_missing')
    if not held_dates:
        errors.append('admission_recipe_forward_date_after_2026_10_02_required')
    elif not train_ok:
        errors.append('holdout_not_evaluated_train_ineligible')
    else:
        errors.extend('holdout:' + key for key, ok in held_checks.items() if not ok)
    selection = bool(train_ok and held_ok and not errors)
    identity = lambda values: S.digest([[r['day'], r['trace'], r['raw_sha256'], r['path']]
                                       for r in sorted(values, key=lambda r: (r['ts'], r['trace']))])
    return dict(contract=CONTRACT, evaluation_unit=UNIT,
        metric_role='main_entry_win_rate_selection', coverage_role='diagnostic_only',
        success_retention_role='diagnostic_only', discovery_through_date=DISCOVERY_THROUGH,
        source_dates=dates, train_dates=train_dates, holdout_dates=held_dates,
        consumed_holdout_dates=consumed_dates,
        source_date_census={day: dict(observation_count=sum(r['day'] == day for r in rows),
            native_observation_count=sum(r['day'] == day and r['native_provenance'] is not None for r in rows)) for day in dates},
        candidate_computed=bool(rows), candidate_train_qualified=train_ok,
        candidate_validation_evaluated=held_evaluated, candidate_selected=selection,
        fresh_validation=('passed' if held_ok else 'failed' if held_evaluated
                          else 'not_observed' if not held_dates else 'not_run_train_ineligible'),
        baseline=dict(train=old_train, holdout=old_held), candidate=dict(train=new_train, holdout=new_held),
        train_hurdles=checks, holdout_hurdles=held_checks if held_evaluated else None,
        selection_coverage={part: (new['selected_observation_count'] / old['selected_observation_count']
            if old['selected_observation_count'] else None) for part, old, new in
            [('train', old_train, new_train), ('holdout', old_held, new_held)]},
        success_retention_diagnostics=dict(train=_retention(old_rows, new_rows),
            holdout=_retention(old_held_rows, new_held_rows) if held_evaluated else None),
        first_signal_event_count=len(events), first_signal_manifest_sha256=S.digest(events),
        selected_train_manifest_sha256=identity(new_rows),
        selected_holdout_manifest_sha256=identity(new_held_rows) if held_evaluated else None,
        hurdle_errors=errors)


def apply(report, analysis, parent):
    """Preserve the old native census as diagnostics, then bind the new decision."""
    from src.engine.scalping.entry_admission_recipe import candidate_policy
    result = deepcopy(report)
    result['native_diagnostics'] = {k: deepcopy(report.get(k)) for k in
        ('baseline', 'candidate', 'candidate_training_diagnostics', 'hurdle_errors',
         'train_dates', 'holdout_dates', 'accepted_attempt_count', 'excluded_attempt_counts')}
    contract = evaluate(analysis, target_date=report['target_date'],
                        consumed_dates=report['consumed_holdout_dates'])
    proposed = candidate_policy(parent)
    result.update(acceptance_contract=CONTRACT, acceptance_kernel_sha256=kernel_sha256(),
        selection_objective_version=OBJECTIVE, opportunity_identity_contract=UNIT,
        census_role='native_lineage_diagnostic_not_selection_population',
        admission_acceptance=contract, candidate_search_count=1,
        candidate_evaluated=contract['candidate_train_qualified'],
        candidate_holdout_opportunity_manifest_sha256=contract['selected_holdout_manifest_sha256'],
        candidate_machine_policy_sha256=S.digest(proposed),
        candidate_policy=proposed if contract['candidate_selected'] else None,
        disposition='successor_selected' if contract['candidate_selected'] else 'incumbent_carried',
        chronological_opportunity_split=None,
        samsung_policy_status=dict(candidate_recipe_id='absorption_p60_v10',
            runtime_registration_status='unregistered_report_recipe', disposition='incumbent_carried',
            reason='separate_samsung_candidate_not_registered', owner='SamsungFrozenCandidateValidation1006'))
    for key in ('candidate_computed', 'candidate_train_qualified', 'candidate_validation_evaluated',
                'candidate_selected', 'fresh_validation', 'baseline', 'candidate', 'train_dates',
                'holdout_dates', 'hurdle_errors', 'success_retention_diagnostics'):
        result[key] = deepcopy(contract[key])
    result['candidate_training_diagnostics'] = [dict(recipe_id='pullback_p60_v0',
        metrics=contract['candidate']['train'], successor_hurdles=contract['train_hurdles'],
        eligible_train=contract['candidate_train_qualified'],
        metric_role='main_entry_win_rate_selection', evaluation_unit=UNIT,
        retained_baseline_winning_attempt_count=contract['success_retention_diagnostics']['train']['retained_wins'],
        baseline_winning_attempt_count=contract['success_retention_diagnostics']['train']['baseline_wins'])]
    result['policy_by_scope'] = {'KRX|KRX_REGULAR': proposed} if contract['candidate_selected'] else {}
    result['policy_sha256'] = S.digest(result['policy_by_scope'])
    result.pop('artifact_content_sha256', None)
    result['artifact_content_sha256'] = S.digest(result)
    return result


def validate_source(source, *, require_files=False):
    """Recompute qualification rather than trust selected flags or report metrics."""
    if (source.get('acceptance_contract') != CONTRACT
        or source.get('candidate_kind') != 'admission_recipe'
        or source.get('candidate_recipe_id') != 'pullback_p60_v0'
        or source.get('selection_objective_version') != OBJECTIVE
        or source.get('opportunity_identity_contract') != UNIT
        or not re.fullmatch(r'[0-9a-f]{64}', str(source.get('acceptance_kernel_sha256') or ''))
        or (require_files and source['acceptance_kernel_sha256'] != kernel_sha256())):
        raise ValueError('admission_acceptance_contract_invalid')
    expected = evaluate(source['admission_analysis'], target_date=source['target_date'],
                        consumed_dates=source['consumed_holdout_dates'])
    if S.digest(source.get('admission_acceptance')) != S.digest(expected):
        raise ValueError('admission_acceptance_recomputation_mismatch')
    for key in ('candidate_computed', 'candidate_train_qualified', 'candidate_validation_evaluated',
                'candidate_selected', 'fresh_validation', 'baseline', 'candidate', 'train_dates',
                'holdout_dates', 'hurdle_errors', 'success_retention_diagnostics'):
        if S.digest(source.get(key)) != S.digest(expected[key]):
            raise ValueError('admission_acceptance_field_mismatch:' + key)
    if (source.get('candidate_evaluated') is not expected['candidate_train_qualified']
        or source.get('candidate_holdout_opportunity_manifest_sha256') != expected['selected_holdout_manifest_sha256']
        or source.get('disposition') != ('successor_selected' if expected['candidate_selected'] else 'incumbent_carried')):
        raise ValueError('admission_acceptance_selection_mismatch')
    return expected
