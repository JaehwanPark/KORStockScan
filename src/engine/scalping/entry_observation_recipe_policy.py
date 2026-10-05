"""Explicit offline recipe selection for source-bound machine observations.

Consumed by build_machine_policy_report only on an explicit isolated request.
Observation clusters are never scanner promotions, independent trials or fills.
The native strategy publisher does not accept this candidate schema.
"""
from collections import Counter, defaultdict
from datetime import date, datetime, timezone, timedelta
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

from src.engine.scalping import entry_strategy_policy as S

REQUEST = 'machine_observation_recipe_request_v1'
EXPRESSION = 'machine_observation_recipe_expression_v1'
REPORT = 'main_machine_observation_recipe_report_v1'
UNIT = 'equal_symbol_date_venue_session_observation_cluster_v1'
KST = timezone(timedelta(hours=9))
GROUPS = ('samsung', 'non_samsung')
RECIPES = dict(samsung='absorption_p60_v10', non_samsung='pullback_p60_v0')
AUTHORITY = dict(runtime_effect=False, allowed_runtime_apply=False,
    actual_order_submitted=False, broker_order_forbidden=True, promotion_pass=False,
    decision_authority='isolated_observation_recipe_selection',
    metric_role='main_entry_win_rate_selection',
    forbidden_uses=['native_identity_synthesis', 'runtime_apply', 'policy_publication',
                    'realized_pnl', 'independent_holdout_claim'])


def file_sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def number(value):
    return float(value) if type(value) in (int, float) and math.isfinite(value) else None


def kernel_manifest():
    names = ('entry_observation_recipe_policy.py', 'ai_action_outcome_calibration.py',
        'entry_strategy_policy.py', 'entry_setup_evidence.py', 'entry_candle_context.py',
        'entry_flat_buy_flow_research.py', 'entry_pullback_buy_flow_research.py',
        'entry_machine_observation.py', 'entry_policy_hypothesis_research.py',
        'postclose_entry_validation.py')
    return {name: file_sha(Path(__file__).with_name(name)) for name in names}


def expression(group, parent):
    if group not in GROUPS:
        raise ValueError('observation_recipe_group_invalid')
    return dict(schema=EXPRESSION, group=group, recipe_id=RECIPES[group],
        scope=['KRX', 'KRX_REGULAR'], symbol_predicate='005930' if group == 'samsung' else 'exclude_005930',
        admission_mode='replace', parent_sha256=S.digest(parent),
        kernel_sha256=S.digest(kernel_manifest()), **AUTHORITY)


def validate_expression(value, parent):
    if not isinstance(value, dict) or value.get('group') not in GROUPS:
        return ['observation_recipe_expression_invalid']
    return [] if value == expression(value['group'], parent) else ['observation_recipe_expression_mismatch']


def _verify_files(files):
    if not isinstance(files, list) or not files:
        raise ValueError('observation_source_manifest_missing')
    seen = set()
    for item in files:
        path = str(Path(item['path']).resolve())
        if path in seen or item['role'] not in {'capture', 'horizon', 'samsung_receipt', 'evidence'}:
            raise ValueError('observation_source_manifest_invalid')
        seen.add(path)
        if file_sha(path) != item['sha256']:
            raise ValueError('observation_source_file_changed:' + path)
    roles = Counter(item['role'] for item in files)
    if not roles['capture'] or not roles['horizon'] or roles['samsung_receipt'] != 1:
        raise ValueError('observation_source_roles_missing')


def _index(rows, key):
    result, seen, conflicts = {}, set(), set()
    for row in rows:
        identity = row.get(key)
        if not isinstance(identity, str) or not identity:
            raise ValueError('observation_source_index_identity_missing')
        if identity in seen:
            result.pop(identity, None)
            conflicts.add(identity)
            continue
        seen.add(identity)
        result[identity] = row
    return result, conflicts


def _source_error(row, *, through):
    from src.engine.scalping.ai_action_outcome_calibration import _machine_source_contract_valid
    setup = row.get('setup_evidence') or {}
    raw = setup.get('strategy_raw_input') or {}
    try:
        stamp = datetime.fromisoformat(row['decision_ts'])
        day = stamp.astimezone(KST).date().isoformat()
        symbol = row['stock_code']
        local = stamp.astimezone(KST)
        if (stamp.utcoffset() is None or day != row['source_date']
                or not '2026-09-29' <= day <= through
                or not isinstance(symbol, str) or len(symbol) != 6 or not symbol.isdigit()
                or not 9 * 60 <= local.hour * 60 + local.minute < 15 * 60 + 30):
            return 'observation_date_or_symbol_invalid'
        if not _machine_source_contract_valid(row):
            return 'observation_original_source_invalid'
        if (not raw or setup.get('strategy_raw_sha256') != S.digest(raw)
                or raw.get('stock_code') != symbol
                or str(raw.get('effective_venue')).upper() != 'KRX'
                or str(raw.get('session_bucket')).upper() != 'KRX_REGULAR'):
            return 'observation_raw_binding_invalid'
        cutoff = number(raw.get('entry_machine_input_as_of'))
        if cutoff is None or not 0 <= stamp.timestamp() - cutoff <= 60:
            return 'observation_capture_cutoff_invalid'
        if not isinstance(row.get('evaluation_attempt_id'), str) or not row['evaluation_attempt_id']:
            return 'observation_attempt_identity_missing'
    except (KeyError, ValueError, TypeError, OverflowError):
        return 'observation_identity_invalid'
    return None


def _path(row, outcome):
    """Bind an already sealed 60m label to the actual capture/cost, not 10m v1."""
    from src.engine.scalping.ai_action_outcome_calibration import _full_entry_cost_pct
    missing = lambda reason: dict(status=reason, net_pct=None, delay_sec=None)
    if outcome is None:
        return missing('horizon_source_missing')
    if ((outcome.get('trace'), outcome.get('day'), outcome.get('symbol'), outcome.get('ts'),
            (outcome.get('tags') or {}).get('venue'), (outcome.get('tags') or {}).get('session'), outcome.get('action'))
            != (row['decision_trace_id'], row['source_date'], row['stock_code'], row['decision_ts'],
                'KRX', 'KRX_REGULAR', row['machine_action'])):
        return missing('horizon_identity_mismatch')
    raw = row['setup_evidence']['strategy_raw_input']
    cost_contract = (row.get('comparison') or {}).get('entry_cost_contract') or {}
    cost = _full_entry_cost_pct(cost_contract, source_date=row['source_date'])
    recorded_cost = number((outcome.get('features') or {}).get('entry_cost_pct'))
    if (cost is None or recorded_cost is None or abs(cost - recorded_cost) > 1e-8
            or (cost_contract.get('effective_venue'), cost_contract.get('session_bucket')) != ('KRX', 'KRX_REGULAR')):
        return missing('cost_missing_or_mismatched')
    ask = number((raw.get('quote') or {}).get('best_ask'))
    reference = number(outcome.get('reference_price'))
    if (outcome.get('capture_valid') is not True or outcome.get('reference_type') != 'executable_ask'
            or ask is None or ask <= 0 or reference != ask):
        return missing('entry_reference_mismatch')
    path = (outcome.get('paths') or {}).get('60m') or {}
    status = path.get('status')
    if status in {'cost_missing', 'first_partial_bar_ambiguous', 'same_bar_ambiguous', 'insufficient_followup'}:
        return missing(status)
    start = datetime.fromisoformat(row['decision_ts']).astimezone(KST)
    close = start.replace(hour=15, minute=30, second=0, microsecond=0).timestamp()
    if path.get('requested_seconds') != 3600:
        return missing('horizon_contract_invalid')
    try:
        end = datetime.fromisoformat(path['requested_end'])
        if end.utcoffset() is None or abs(end.timestamp() - start.timestamp() - 3600) > .001:
            return missing('horizon_contract_invalid')
    except (KeyError, TypeError, ValueError, OverflowError):
        return missing('horizon_contract_invalid')
    delay = number(path.get('delay_sec'))
    if status in {'late_target_first', 'stop_first'}:
        if delay is None or not 0 < delay <= min(3600, close - start.timestamp()):
            return missing('horizon_hit_clock_invalid')
        # Historical Samsung labels predate the strict partial-bar guard.
        if delay < 60 and start.timestamp() % 60 > .001:
            return missing('first_partial_bar_ambiguous')
        for gap in path.get('gaps') or []:
            end = number(gap.get('to_ts'))
            if end is None or end <= start.timestamp() + delay:
                return missing('price_gap_before_hit')
        return dict(status='target' if status == 'late_target_first' else 'stop',
            delay_sec=delay, net_pct=.1 if status == 'late_target_first' else -.7-cost)
    if status == 'neither_by_horizon':
        net = number(path.get('observed_terminal_net_pct'))
        if (path.get('complete_to_requested_end') is True and not path.get('gaps')
                and end.timestamp() <= close and net is not None):
            return dict(status='timeout', net_pct=net, delay_sec=3600)
    return missing('horizon_contract_invalid')


def cluster(row):
    return row['day'], row['symbol'], 'KRX', 'KRX_REGULAR'


def replay(rows, action):
    """Missing/ambiguous outcomes keep occupancy; never skip to a nicer label."""
    busy, selected = {}, []
    for row in sorted(rows, key=lambda r: (r['ts'], r['trace'])):
        if row[action] != 'ENTER_NOW':
            continue
        stamp = datetime.fromisoformat(row['ts']).astimezone(KST)
        now, unit = stamp.timestamp(), cluster(row)
        if now <= busy.get(unit, -math.inf):
            continue
        selected.append(row)
        end = min(now + 3600, stamp.replace(hour=15, minute=30, second=0, microsecond=0).timestamp())
        path = row['path']
        busy[unit] = now + path['delay_sec'] if path['status'] in {'target', 'stop'} else end
    return selected


def metrics(selected):
    groups, nets = defaultdict(list), defaultdict(list)
    for row in selected:
        unit, path = cluster(row), row['path']
        if path['status'] in {'target', 'stop'}:
            groups[unit].append(int(path['status'] == 'target'))
        if path['net_pct'] is not None:
            nets[unit].append(path['net_pct'])
    counts = Counter(r['path']['status'] for r in selected)
    hits = counts['target'] + counts['stop']
    result = dict(evaluation_unit=UNIT, selected_observation_count=len(selected),
        selected_cluster_count=len({cluster(r) for r in selected}),
        boundary_cluster_count=len(groups), boundary_observation_count=hits,
        counts=dict(counts), win_rate_pct=100 * mean(map(mean, groups.values())) if groups else None,
        observation_weighted_win_rate_pct=100 * counts['target']/hits if hits else None,
        cluster_mean_price_cf_pct=mean(map(mean, nets.values())) if nets else None,
        observation_mean_price_cf_pct=mean([r['path']['net_pct'] for r in selected
            if r['path']['net_pct'] is not None]) if nets else None,
        source_lanes=dict(Counter(r['source_lane'] for r in selected)),
        native_selected_count=sum(r['native_provenance'] is not None for r in selected),
        selected_ids=[r['trace'] for r in selected])
    result['support_adjusted_win_rate_pct'] = S.machine_support_adjusted_win_rate(_rank_input(result))
    return result


def _rank_input(value):
    # Adapter only: output names remain clusters, never native opportunities.
    return dict(win_rate_pct=value['win_rate_pct'], selected_opportunity_count=value['boundary_cluster_count'])


def compare(rows):
    parent, candidate = (metrics(replay(rows, action)) for action in ('parent_action', 'candidate_action'))
    reasons = []
    if not candidate['boundary_cluster_count']:
        reasons.append('candidate_boundary_unresolved')
    if parent['selected_observation_count'] and not parent['boundary_cluster_count']:
        reasons.append('baseline_boundary_unresolved')
    improves = not reasons and S.machine_winrate_improves(_rank_input(candidate), _rank_input(parent))
    if not improves and not reasons:
        reasons.append('raw_or_support_adjusted_win_rate_not_improved')
    return dict(parent=parent, candidate=candidate, improves=bool(improves), reasons=reasons,
        comparable_population_sha256=S.digest([(r['trace'], r['raw_sha256'], r['path'])
            for r in sorted(rows, key=lambda r: r['trace'])]))


def thin(rows, seconds=600):
    """Preselection clock thinning does not consult either action or outcome."""
    previous, kept = {}, []
    for row in sorted(rows, key=lambda r: (r['ts'], r['trace'])):
        now, unit = datetime.fromisoformat(row['ts']).timestamp(), cluster(row)
        if now - previous.get(unit, -math.inf) >= seconds:
            kept.append(row)
            previous[unit] = now
    return kept


def _selection(rows, *, boundary, recipe):
    train = [r for r in rows if r['day'] <= boundary]
    held = [r for r in rows if r['day'] > boundary]
    training = compare(train)
    # The train decision is frozen before the later comparison is examined.
    train_selected = recipe if training['improves'] else None
    comparison = compare(held)
    supported = bool(train_selected and comparison['improves'])
    return dict(**AUTHORITY, candidate=recipe, evaluated_candidate_count=1,
        training=training, later_comparison=comparison, selected_on_train=train_selected,
        observational_candidate_supported=supported,
        selected_observation_recipe=recipe if supported else None,
        status='observational_candidate_supported' if supported else 'incumbent_carried_in_observation_test',
        selection_errors=['train:' + r for r in training['reasons']] +
            ['comparison:' + r for r in comparison['reasons']],
        runtime_registration_status='unregistered_report_recipe', pristine_holdout=False,
        by_date={day: compare([r for r in rows if r['day'] == day]) for day in sorted({r['day'] for r in rows})},
        preselection_600s={day: compare(thin([r for r in rows if r['day'] == day]))
            for day in sorted({r['day'] for r in rows})})


def build_report(request, *, target_date):
    """Read only sealed local inputs, replay both recipes and select offline."""
    from src.engine.scalping import entry_flat_buy_flow_research as F
    from src.engine.scalping import entry_pullback_buy_flow_research as P
    from src.engine.scalping.entry_policy_hypothesis_research import stream_array
    from src.engine.scalping.entry_setup_evidence import validate_mechanistic_entry_threshold_policy
    from src.engine.scalping.postclose_entry_validation import opportunity_identity
    if request.get('schema') != REQUEST or request.get('target_date') != target_date:
        raise ValueError('observation_request_invalid')
    boundary = request['training_through_date']
    if not date.fromisoformat('2026-09-29') <= date.fromisoformat(boundary) < date.fromisoformat(target_date):
        raise ValueError('observation_training_boundary_invalid')
    if request.get('evaluation_unit') != UNIT or request.get('pristine_holdout') is not False:
        raise ValueError('observation_evaluation_contract_invalid')
    parent = request['parent_policy']
    if request.get('parent_sha256') != S.digest(parent) or validate_mechanistic_entry_threshold_policy(parent):
        raise ValueError('observation_parent_invalid')
    if set(request.get('expressions') or {}) != set(GROUPS) or any(
            request['expressions'][g].get('group') != g
            or validate_expression(request['expressions'][g], parent) for g in GROUPS):
        raise ValueError('observation_expression_invalid')
    files = request['files']
    _verify_files(files)
    source_hashes = {item['sha256'] for item in files}
    kernels = kernel_manifest()
    horizon, receipts = [], []
    for item in files:
        if item['role'] == 'horizon':
            horizon.extend(json.loads(Path(item['path']).read_text()))
        elif item['role'] == 'samsung_receipt':
            receipts.extend(json.loads(Path(item['path']).read_text()))
    outcomes, outcome_conflicts = _index(horizon, 'trace')
    proofs, proof_conflicts = _index(receipts, 'trace')
    rows, seen, capture_conflicts = [], set(), set()
    exclusions = ([dict(trace=t, reason='horizon_identity_conflict') for t in sorted(outcome_conflicts)]
        + [dict(trace=t, reason='receipt_identity_conflict') for t in sorted(proof_conflicts)])
    for item in files:
        if item['role'] != 'capture':
            continue
        for row in stream_array(Path(item['path'])):
            if (row.get('effective_venue'), row.get('session_bucket')) != ('KRX', 'KRX_REGULAR'):
                continue
            trace = row.get('decision_trace_id')
            if not isinstance(trace, str) or not trace:
                exclusions.append(dict(trace=None, reason='capture_identity_missing', source=item['path']))
                continue
            if trace in seen:
                capture_conflicts.add(trace)
                continue
            seen.add(trace)
            error = _source_error(row, through=target_date)
            if error:
                exclusions.append(dict(trace=trace, reason=error))
                continue
            group = 'samsung' if row['stock_code'] == '005930' else 'non_samsung'
            setup = row['setup_evidence']
            proof = (proofs.get(trace) or {}).get('source_receipt')
            if (proof and proof.get('schema') == F.HISTORICAL_SCHEMA
                    and proof.get('archive_sha256') not in source_hashes):
                raise ValueError('observation_archive_source_unbound')
            decision = (F.evaluate(setup, parent, source_receipt=proof, admission_mode='replace')
                if group == 'samsung' else P.evaluate(setup, parent))
            if decision['parent_action'] != row['machine_action']:
                raise ValueError('observation_parent_replay_mismatch:' + trace)
            try:
                native = list(opportunity_identity(row))
            except ValueError:
                native = None
            rows.append(dict(trace=trace, day=row['source_date'], ts=row['decision_ts'],
                symbol=row['stock_code'], group=group, parent_action=decision['parent_action'],
                candidate_action=decision['proposed_action'], raw_sha256=setup['strategy_raw_sha256'],
                condition_match=decision['condition_match'], source_lane=str(row.get('source_lane')),
                native_provenance=native, zero_base_route=row.get('zero_base_route'),
                source_bundle_sha256=row.get('bundle_sha256'),
                outcome_request_code=row.get('outcome_request_code'),
                path=_path(row, outcomes.get(trace)), evaluator_receipt=decision))
    rows = [r for r in rows if r['trace'] not in capture_conflicts]
    exclusions.extend(dict(trace=t, reason='capture_identity_conflict') for t in sorted(capture_conflicts))
    _verify_files(files)
    if kernel_manifest() != kernels:
        raise ValueError('observation_kernel_changed_during_replay')
    selections = {g: _selection([r for r in rows if r['group'] == g], boundary=boundary,
        recipe=request['expressions'][g]) for g in GROUPS}
    body = dict(schema=REPORT, **AUTHORITY, target_date=target_date,
        training_through_date=boundary, evaluation_unit=UNIT, request_sha256=S.digest(request),
        parent_sha256=S.digest(parent), kernel_manifest=kernels, source_manifest=files,
        policy_by_scope={}, selections=selections, observations=rows, exclusions=exclusions,
        exclusion_counts=dict(Counter(r['reason'] for r in exclusions)),
        parent_replay_count=len(rows), preserved_native_identity=True,
        native_identity_required_for_observation_learning=False, pristine_holdout=False,
        status='observation_recipe_evaluation_complete')
    body['artifact_content_sha256'] = S.digest(body)
    return body
