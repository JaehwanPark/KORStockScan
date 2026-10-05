"""Frozen Samsung absorption diagnosis and later-date offline intake.

This adapter preserves Samsung identity, full original captures and cost/stop
owners. It has no policy publisher, broker, network or runtime mutation path.
"""
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from statistics import mean
import argparse
import json
import math

from src.engine.scalping import entry_strategy_policy as S
from src.engine.scalping import entry_observation_recipe_policy as R
from src.engine.scalping import entry_first_signal_exit_research as E
from src.engine.scalping import entry_admission_analysis as H
from src.engine.scalping import entry_flat_buy_flow_research as F

SCHEMA = 'samsung_absorption_first_signal_research_v1'
FROZEN = 'samsung_absorption_forward_contract_v1'
RECIPE = 'absorption_p60_v10'
AUTHORITY = dict(runtime_effect=False, allowed_runtime_apply=False,
    actual_order_submitted=False, policy_selected=False, registered_runtime_policy=False,
    decision_authority='offline_frozen_samsung_absorption_research',
    metric_role='cost_bound_price_path_diagnostic', realized_profit_claimed=False)


def seal(value):
    value = {k:v for k,v in value.items() if k != 'artifact_content_sha256'}
    return {**value, 'artifact_content_sha256': S.digest(value)}


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(seal(value), stream, indent=2, allow_nan=False)
        stream.write('\n')


def _key(row):
    if (row.get('group') != 'samsung' or row.get('symbol') != '005930'
        or not row.get('outcome_request_code') or not row.get('source_bundle_sha256')):
        raise ValueError('samsung_observation_scope_invalid')
    return R.cluster(row) + (row['outcome_request_code'], row['source_bundle_sha256'])


def fixed_watch(row):
    native = row.get('native_provenance')
    return (isinstance(native, list) and len(native) == 7 and
        native[:5] == [row['day'], '005930', 'KRX', 'KRX_REGULAR', 'MAIN_FIXED_WATCH']
        and all(isinstance(v, str) and v for v in native[5:]))


def metrics(rows):
    base = R.metrics(rows)
    groups = defaultdict(list)
    for row in rows:
        groups[row['day']].append(row)
    metric_names = ('boundary_win_rate_pct', 'target_with_timeout_rate_pct', 'positive_path_rate_pct')
    by_date = {}
    for day, items in groups.items():
        counts = Counter(r['path']['status'] for r in items)
        binary = counts['target'] + counts['stop']
        complete = [r for r in items if r['path']['status'] in {'target','stop','timeout'}
                    and type(r['path'].get('net_pct')) in (int,float)
                    and math.isfinite(r['path']['net_pct'])]
        by_date[day] = dict(selected_count=len(items), boundary_count=binary,
            complete_path_count=len(complete), unknown_count=len(items)-len(complete),
            target_count=counts['target'], stop_count=counts['stop'], timeout_count=counts['timeout'],
            positive_count=sum(r['path']['net_pct'] > 0 for r in complete),
            zero_count=sum(r['path']['net_pct'] == 0 for r in complete),
            negative_count=sum(r['path']['net_pct'] < 0 for r in complete),
            boundary_win_rate_pct=100*counts['target']/binary if binary else None,
            target_with_timeout_rate_pct=100*sum(r['path']['status']=='target' for r in complete)/len(complete) if complete else None,
            positive_path_rate_pct=100*sum(r['path']['net_pct']>0 for r in complete)/len(complete) if complete else None,
            selected_ids=[r['trace'] for r in items])
    base['by_date'] = by_date
    # A single stock supplies one cluster per day, never one per watch retry.
    base['date_equal_metrics'] = {key: mean(values) if (values := [v[key] for v in by_date.values() if v[key] is not None]) else None
                                 for key in metric_names}
    base['metric_date_support'] = {key: sorted(d for d,v in by_date.items() if v[key] is not None) for key in metric_names}
    return base


def compare(rows):
    selected = {arm: R.replay(rows, arm + '_action') for arm in ('parent', 'candidate')}
    out = {arm: metrics(values) for arm, values in selected.items()}
    out['conclusions'] = {}
    for key in out['parent']['date_equal_metrics']:
        old, new = (out[a]['date_equal_metrics'][key] for a in ('parent','candidate'))
        same_dates = out['parent']['metric_date_support'][key] == out['candidate']['metric_date_support'][key]
        out['conclusions'][key] = ('not_identifiable' if old is None or new is None or not same_dates
            else 'improves' if new > old else 'no_improvement')
    return out


def research(rows):
    for row in rows:
        _key(row)
    result = dict(schema=SCHEMA, recipe_id=RECIPE, **AUTHORITY,
        pristine_holdout=False, evaluation_unit=R.UNIT, policy_by_scope={}, cohorts={})
    for name, population in [('all_origins', rows), ('fixed_watch', [r for r in rows if fixed_watch(r)])]:
        events = E.observed_action_runs(population, key_function=_key)
        first = E.mask_first_signals(population, events)
        days = sorted({r['day'] for r in population})
        result['cohorts'][name] = dict(observation_count=len(population), observed_event_count=len(events),
            event_manifest=events, source_dates=days,
            native_observation_count=sum(r['native_provenance'] is not None for r in population),
            original_nonoverlap=compare(population), first_signal_nonoverlap=compare(first),
            by_date={day: dict(original_nonoverlap=compare([r for r in population if r['day']==day]),
                first_signal_nonoverlap=compare([r for r in first if r['day']==day])) for day in days},
            selection_sha256=S.digest([(r['trace'], r['parent_action'], r['candidate_action'], r['raw_sha256']) for r in first]))
    return seal(result)


def kernels():
    names = set(H.kernel_manifest()) | {'samsung_absorption_acceptance_research.py',
        'entry_flat_buy_flow_research.py', 'entry_machine_observation.py'}
    return {name: H.file_sha(Path(__file__).with_name(name)) for name in sorted(names)}


def freeze(parent, evidence):
    from src.engine.scalping.entry_setup_evidence import validate_mechanistic_entry_threshold_policy
    if not evidence or validate_mechanistic_entry_threshold_policy(parent):
        raise ValueError('samsung_freeze_parent_or_evidence_invalid')
    return seal(dict(schema=FROZEN, **AUTHORITY, recipe_id=RECIPE, admission_mode='replace',
        parent_policy=parent, parent_sha256=S.digest(parent), kernel_manifest=kernels(),
        later_source_after_date='2026-10-05', evaluation_unit=R.UNIT,
        comparison_objectives=['boundary_win_rate_pct','target_with_timeout_rate_pct','positive_path_rate_pct'],
        owner='SamsungFrozenCandidateValidation1006', evidence=[dict(path=str(Path(p).resolve()), sha256=H.file_sha(p)) for p in evidence]))


def validate_frozen(value, root=None):
    expected = freeze(value.get('parent_policy'), [p['path'] for p in value.get('evidence', [])])
    if S.digest(value) != S.digest(expected):
        if root is None or {k:v for k,v in value.items() if k not in {'kernel_manifest','artifact_content_sha256'}} != {k:v for k,v in expected.items() if k not in {'kernel_manifest','artifact_content_sha256'}}:
            raise ValueError('samsung_frozen_contract_changed')
        from src.engine.scalping.samsung_policy_compatibility import validate
        validate(root,value,kernels())


def prepare(root, day, frozen):
    """Read automatically generated original projections and completed prices."""
    from src.engine.scalping.entry_policy_hypothesis_research import stream_array
    from src.engine.scalping.ai_action_outcome_calibration import _machine_source_contract_valid
    from src.engine.scalping.postclose_entry_validation import opportunity_identity
    from src.engine.scalping import mechanistic_entry_runtime_policy as M
    validate_frozen(frozen,root=root)
    if date.fromisoformat(day).isoformat() != day or day <= frozen['later_source_after_date']:
        raise ValueError('samsung_forward_date_required')
    root = Path(root)
    capture = root / f'data/report/machine_observation_projection/machine_observation_projection_{day}_0_1.json'
    if not capture.exists():
        capture = capture.with_suffix('.json.gz')
    prices = root / f'data/report/machine_completed_price_source/machine_completed_price_source_{day}.json'
    missing = [str(p) for p in (capture, prices) if not p.exists()]
    body = dict(schema='samsung_absorption_forward_intake_v1', **AUTHORITY,
        day=day, frozen_sha256=frozen['artifact_content_sha256'], candidate_reselection=False, data_collected=False)
    if missing:
        return seal(dict(body, status='waiting_new_source_date', missing_source_paths=missing))
    current = M.load_effective(data_root=root/'data', target_date=day)
    parent = M.for_cohort(current, ('KRX','KRX_REGULAR'))['machine_policy']
    from src.engine.scalping import samsung_policy_compatibility as compatibility
    compatibility.effective_policy(root,frozen,bundle=current)
    parent=frozen['parent_policy']
    seals = {str(p): H.file_sha(p) for p in (capture, prices)}
    index, _, _ = H.price_index(root/'data', [day])
    observations, exclusions, seen = [], [], set()
    for row in stream_array(capture):
        if (row.get('stock_code'),row.get('effective_venue'),row.get('session_bucket')) != ('005930','KRX','KRX_REGULAR'):
            continue
        trace = row.get('decision_trace_id')
        if not trace or trace in seen:
            raise ValueError('samsung_forward_trace_invalid')
        seen.add(trace)
        if (row.get('source_date') != day or not _machine_source_contract_valid(row)):
            exclusions.append(dict(trace=trace, reason='original_source_invalid'))
            continue
        setup = row.get('setup_evidence') or {}
        raw = setup.get('strategy_raw_input') or {}
        if setup.get('strategy_raw_sha256') != S.digest(raw):
            raise ValueError('samsung_forward_raw_changed')
        if ((raw.get('stock_code'), raw.get('effective_venue'), raw.get('session_bucket'))
                != ('005930', 'KRX', 'KRX_REGULAR')
                or row.get('outcome_request_code') not in {'005930', '005930_AL'}):
            exclusions.append(dict(trace=trace, reason='capture_scope_invalid'))
            continue
        try:
            H.capture_clock(row)
        except (ValueError, TypeError, KeyError):
            exclusions.append(dict(trace=trace, reason='capture_clock_invalid'))
            continue
        try:
            compatibility.source_bundle(root,frozen,row)
        except (ValueError, OSError, KeyError, TypeError) as exc:
            exclusions.append(dict(trace=trace,reason='capture_policy_provenance_invalid',detail=str(exc)))
            continue
        decision = F.evaluate(setup, parent, admission_mode='replace')
        if not decision['source_valid']:
            exclusions.append(dict(trace=trace, reason='exact_asof_receipt_missing_or_invalid'))
            continue
        if decision['parent_action'] != row.get('machine_action'):
            raise ValueError('samsung_forward_parent_action_mismatch')
        bars = index.get((day,'005930','KRX','KRX_REGULAR',row.get('outcome_request_code')), [])
        path = H.path(row, bars, seconds=600)
        if path['status'] == 'timeout':
            path = H.path(row, bars, seconds=3600)
        if path['status'] == 'timeout':
            end = H.capture_clock(row).timestamp()+3600
            last = [b for b in bars if b['t'] <= end][-1]
            path = {**path, 'net_pct': (last['close']/path['reference_price']-1)*100-path['cost_pct'],
                'delay_sec':3600, 'terminal_observed_at':last['t']}
        try:
            native = list(opportunity_identity(row))
        except ValueError:
            native = None
        observations.append(dict(trace=trace,day=day,ts=row['decision_ts'],symbol='005930',group='samsung',
            raw_sha256=setup['strategy_raw_sha256'],outcome_request_code=row.get('outcome_request_code'),
            source_bundle_sha256=row['bundle_sha256'],source_lane=row.get('source_lane'),native_provenance=native,
            parent_action=decision['parent_action'],candidate_action=decision['proposed_action'],path=path,
            evaluator_receipt=decision))
    if any(H.file_sha(p) != sha for p,sha in seals.items()):
        raise ValueError('samsung_forward_input_changed')
    return seal(dict(body,status='evaluated' if observations else 'source_quality_excluded_all' if exclusions else 'valid_empty',
        source_seals=seals, observations=observations, exclusions=exclusions,
        result=research(observations) if observations else None))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--frozen', type=Path, required=True)
    parser.add_argument('--date', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    write(args.output, prepare(args.root,args.date,json.loads(args.frozen.read_text())))


if __name__ == '__main__':
    main()
