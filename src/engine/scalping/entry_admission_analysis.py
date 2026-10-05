"""Postclose action-union analysis from existing captures and completed prices.

This report producer never fetches prices, creates native identities, selects a
Samsung policy, or calls a broker. Costs and stop boundaries retain their owner.
"""
from bisect import bisect_right
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime
import hashlib
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.scalping import entry_strategy_policy as S

SCHEMA = 'main_entry_admission_analysis_v1'
KST = ZoneInfo('Asia/Seoul')
AUTHORITY = dict(runtime_effect=False, allowed_runtime_apply=False,
    actual_order_submitted=False, broker_order_forbidden=True,
    metric_role='main_entry_win_rate_selection', decision_authority='report_only',
    window_policy='exact_session_10m_then_60m_no_future_features',
    sample_floor='source_valid_rows_with_separate_native_qualification',
    primary_decision_metric='cost_bound_target_before_stop',
    source_quality_gate='raw_capture_and_completed_price_cost_stop_binding',
    forbidden_uses=['native_identity_synthesis', 'realized_profit', 'broker_orders'])


def file_sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def kernel_manifest():
    names = ('entry_admission_analysis.py', 'entry_admission_recipe.py',
        'entry_setup_evidence.py', 'entry_strategy_policy.py',
        'entry_first_signal_exit_research.py', 'entry_observation_recipe_policy.py',
        'ai_action_outcome_calibration.py', 'postclose_entry_validation.py')
    return {name: file_sha(Path(__file__).with_name(name)) for name in names}


def capture_clock(row):
    stamp = datetime.fromisoformat(row['decision_ts'])
    if (stamp.utcoffset() is None
        or stamp.astimezone(KST).date().isoformat() != row['source_date']):
        raise ValueError('admission_capture_clock_invalid')
    raw = (row.get('setup_evidence') or {}).get('strategy_raw_input') or {}
    cutoff = S._number(raw.get('entry_machine_input_as_of'))
    if cutoff is None or not 0 <= stamp.timestamp() - cutoff <= 60:
        raise ValueError('admission_capture_cutoff_invalid')
    return stamp.astimezone(KST)


def price_index(data_root, days):
    from src.engine.scalping.ai_decision_quality import _price_source_usable
    from src.engine.scalping.entry_policy_hypothesis_research import stream_array
    index, sources = defaultdict(dict), []
    conflicts = set()
    for day in sorted(set(days)):
        path = Path(data_root) / 'report' / 'machine_completed_price_source' / f'machine_completed_price_source_{day}.json'
        if not path.exists():
            sources.append(dict(path=str(path.resolve()), source_date=day, status='missing'))
            continue
        before = file_sha(path)
        for row in stream_array(path, key='prices'):
            if not _price_source_usable(row) or row.get('completed_bar_only') is not True:
                continue
            try:
                stamp = datetime.fromisoformat(row['timestamp'])
                key = (day, row['stock_code'], row['effective_venue'], row['session_bucket'], row['source_request_code'])
                values = {k: S._number(row.get(k)) for k in ('open', 'high', 'low', 'close')}
                if (stamp.tzinfo is None or stamp.astimezone(KST).date().isoformat() != day
                    or any(v is None for v in values.values())
                    or not 0 < values['low'] <= min(values['open'], values['close'])
                        <= max(values['open'], values['close']) <= values['high']):
                    continue
                bar = dict(t=stamp.timestamp(), **values)
            except (KeyError, TypeError, ValueError, OverflowError):
                continue
            old = index[key].get(bar['t'])
            if old is not None and old != bar:
                conflicts.add(key)
            index[key][bar['t']] = bar
        if file_sha(path) != before:
            raise ValueError('admission_price_source_changed')
        sources.append(dict(path=str(path.resolve()), source_date=day, sha256=before, status='observed'))
    return {key: sorted(values.values(), key=lambda b: b['t'])
            for key, values in index.items() if key not in conflicts}, sources, sorted(conflicts)


def path(row, prices, *, seconds):
    """Certify a boundary only on the continuous prefix before any price gap."""
    from src.engine.scalping.ai_action_outcome_calibration import _full_entry_cost_pct
    missing = lambda reason: dict(status=reason, delay_sec=None, net_pct=None)
    raw = (row.get('setup_evidence') or {}).get('strategy_raw_input') or {}
    cost_contract = (row.get('comparison') or {}).get('entry_cost_contract') or {}
    cost = _full_entry_cost_pct(cost_contract, source_date=row['source_date'])
    charged = S._number((row.get('comparison') or {}).get('conservative_execution_cost_pct'))
    original = row.get('entry_quality_path') or {}
    stop = S._number(original.get('exact_stop_distance_pct'))
    recorded_stop = S._number(row.get('outcome_stop_distance_pct'))
    ask = S._number((raw.get('quote') or {}).get('best_ask'))
    if (cost is None or charged is None or abs(cost - charged) > 1e-9
        or (cost_contract.get('effective_venue'), cost_contract.get('session_bucket'))
            != (row.get('effective_venue'), row.get('session_bucket'))):
        return missing('cost_missing_or_mismatched')
    if (stop is None or stop >= 0 or recorded_stop is None or stop != recorded_stop
        or not row.get('outcome_stop_owner')):
        return missing('stop_source_missing_or_mismatched')
    if ask is None or ask <= 0:
        return missing('entry_reference_missing')
    if seconds not in (600, 3600):
        return missing('horizon_contract_invalid')
    try:
        start = capture_clock(row)
    except (KeyError, TypeError, ValueError, OverflowError):
        return missing('capture_clock_or_cutoff_invalid')
    close = start.replace(hour=15, minute=30, second=0, microsecond=0).timestamp()
    end = min(start.timestamp() + seconds, close)
    if ((row.get('effective_venue'), row.get('session_bucket')) != ('KRX', 'KRX_REGULAR')
        or not 9 * 60 <= start.hour * 60 + start.minute < 15 * 60 + 30):
        return missing('outside_regular_session')
    times = [bar['t'] for bar in prices]
    bars = prices[bisect_right(times, start.timestamp()):bisect_right(times, end)]
    target_price, stop_price = ask * (1 + (cost + .1) / 100), ask * (1 + stop / 100)
    previous = start.timestamp()
    for bar in bars:
        if (any(S._number(bar.get(k)) is None for k in ('t', 'open', 'high', 'low', 'close'))
            or not 0 < bar['low'] <= min(bar['open'], bar['close'])
                <= max(bar['open'], bar['close']) <= bar['high']):
            return missing('price_bar_invalid')
        if bar['t'] - previous > 90:
            return missing('price_gap_before_hit')
        up, down = bar['high'] >= target_price, bar['low'] <= stop_price
        if up or down:
            delay = bar['t'] - start.timestamp()
            if delay < 60 and start.timestamp() % 60 > .001:
                return missing('first_partial_bar_ambiguous')
            if up and down:
                return missing('same_bar_ambiguous')
            return dict(status='target' if up else 'stop', delay_sec=delay,
                net_pct=.1 if up else stop - cost, cost_pct=cost,
                stop_distance_pct=stop, reference_price=ask,
                requested_seconds=seconds, observed_at=bar['t'])
        previous = bar['t']
    if start.timestamp() + seconds > close:
        return missing('session_censored')
    if not bars or end - bars[-1]['t'] > 90:
        return missing('insufficient_followup')
    return dict(status='timeout', delay_sec=None, net_pct=None,
        requested_seconds=seconds, cost_pct=cost, stop_distance_pct=stop,
        reference_price=ask, cadence_complete_within_90s=True)


def native_path_value(row, observation):
    """Use only a report label bound to this original raw/cost/stop capture."""
    missing = (None, None, 'admission_horizon_missing_or_invalid')
    if not isinstance(observation, dict):
        return missing
    setup = row.get('setup_evidence') or {}
    if (observation.get('raw_sha256') != setup.get('strategy_raw_sha256')
        or observation.get('trace') != row.get('decision_trace_id')
        or (observation.get('day'), observation.get('symbol'), observation.get('ts'))
            != (row.get('source_date'), row.get('stock_code'), row.get('decision_ts'))
        or observation.get('cost_contract_sha256') != S.digest((row.get('comparison') or {}).get('entry_cost_contract') or {})):
        return missing
    selected = observation.get('path') or {}
    if selected.get('status') not in {'target', 'stop'}:
        return None, None, selected.get('status') or missing[2]
    from src.engine.scalping.ai_action_outcome_calibration import _full_entry_cost_pct
    cost = _full_entry_cost_pct((row.get('comparison') or {}).get('entry_cost_contract'), source_date=row['source_date'])
    stop = S._number(row.get('outcome_stop_distance_pct'))
    delay = S._number(selected.get('delay_sec'))
    charged = S._number((row.get('comparison') or {}).get('conservative_execution_cost_pct'))
    try:
        stamp = capture_clock(row)
    except (KeyError, TypeError, ValueError, OverflowError):
        return missing
    seconds = selected.get('requested_seconds')
    expected = .1 if selected['status'] == 'target' else stop - cost if stop is not None and cost is not None else None
    if (cost is None or stop is None or selected.get('cost_pct') != cost
        or charged is None or abs(charged - cost) > 1e-9 or stop >= 0 or not row.get('outcome_stop_owner')
        or stop != S._number((row.get('entry_quality_path') or {}).get('exact_stop_distance_pct'))
        or selected.get('stop_distance_pct') != stop or delay is None
        or seconds not in (600, 3600) or not 0 < delay <= seconds
        or selected.get('net_pct') != expected
        or selected.get('observed_at') != stamp.timestamp() + delay
        or stamp.timestamp() + delay > stamp.replace(hour=15, minute=30, second=0, microsecond=0).timestamp()
        or selected.get('reference_price') != (setup.get('strategy_raw_input') or {}).get('quote', {}).get('best_ask')):
        return missing
    hit = 'net_target_first' if selected['status'] == 'target' else 'exact_stop_first'
    return .1 if hit == 'net_target_first' else stop - cost, hit, None


def build_report(rows, *, parent, target_date, data_root, designated_pair=None):
    from src.engine.scalping import entry_setup_evidence as E
    from src.engine.scalping import entry_admission_recipe as A
    from src.engine.scalping import entry_observation_recipe_policy as R
    from src.engine.scalping import entry_first_signal_exit_research as F
    from src.engine.scalping.ai_action_outcome_calibration import _machine_source_contract_valid
    from src.engine.scalping.postclose_entry_validation import opportunity_identity
    scoped = [r for r in rows if (r.get('effective_venue'), r.get('session_bucket')) == ('KRX', 'KRX_REGULAR')]
    kernels = kernel_manifest()
    index, sources, conflicts = price_index(data_root, [r['source_date'] for r in scoped])
    comparison_parent = parent
    if designated_pair is not None:
        from src.engine.scalping import entry_designated_policy as D
        D.validate_pair(designated_pair)
        D.arm(designated_pair, parent)
        comparison_parent = designated_pair['baseline_policy']
    candidate = designated_pair['candidate_policy'] if designated_pair else A.candidate_policy(parent)
    observations, exclusions, seen, duplicates = [], [], set(), set()
    for row in scoped:
        trace = row.get('decision_trace_id')
        if trace in seen:
            duplicates.add(trace)
            continue
        seen.add(trace)
        if not _machine_source_contract_valid(row):
            exclusions.append(dict(trace=trace, reason='original_source_contract_invalid'))
            continue
        setup = row.get('setup_evidence') or {}
        raw = setup.get('strategy_raw_input') or {}
        if (row.get('source_date', '') > target_date or row.get('source_date', '') < '2026-09-29'
            or raw.get('stock_code') != row.get('stock_code')
            or setup.get('strategy_raw_sha256') != S.digest(raw)):
            exclusions.append(dict(trace=trace, reason='capture_identity_invalid'))
            continue
        try:
            capture_clock(row)
            consumption = D.observation_policy(row, data_root=data_root, p=designated_pair) if designated_pair else {}
            decision = E.mechanistic_entry_policy_decision(setup, policy=comparison_parent)
            group = 'samsung' if row['stock_code'] == '005930' else 'non_samsung'
            proposed = decision if group == 'samsung' else E.mechanistic_entry_policy_decision(setup, policy=candidate)
            key = (row['source_date'], row['stock_code'], row['effective_venue'], row['session_bucket'], row.get('outcome_request_code'))
            primary = path(row, index.get(key, []), seconds=600)
            extended = primary if primary['status'] != 'timeout' else path(row, index.get(key, []), seconds=3600)
            try:
                native = list(opportunity_identity(row))
            except ValueError:
                native = None
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            exclusions.append(dict(trace=trace, reason='replay_or_path_invalid', detail=type(exc).__name__))
            continue
        observations.append(dict(**consumption, trace=trace, day=row['source_date'], symbol=row['stock_code'],
            ts=row['decision_ts'], group=group, raw_sha256=setup['strategy_raw_sha256'],
            outcome_request_code=row.get('outcome_request_code'),
            source_bundle_sha256=row.get('bundle_sha256'),
            cost_contract_sha256=S.digest((row.get('comparison') or {}).get('entry_cost_contract') or {}),
            captured_action=row.get('machine_action'), parent_action=decision['action'],
            source_lane=row.get('source_lane') or 'machine_observation_original_capture',
            candidate_action=proposed['action'], native_provenance=native,
            scope=[row['effective_venue'], row['session_bucket']], path_10m=primary,
            path=extended, evaluator_receipt=deepcopy(proposed.get('admission_recipe'))))
    observations = [r for r in observations if r['trace'] not in duplicates]
    exclusions.extend(dict(trace=trace, reason='capture_identity_conflict') for trace in sorted(duplicates, key=str))
    groups = {}
    for group in ('samsung', 'non_samsung'):
        chosen = [r for r in observations if r['group'] == group]
        events = F.first_signal_events(chosen) if group == 'non_samsung' else []
        first = F.mask_first_signals(chosen, events) if group == 'non_samsung' else chosen
        groups[group] = dict(input_observations=len(chosen), captured_action_counts=dict(Counter(r['captured_action'] for r in chosen)),
            path_counts=dict(Counter(r['path']['status'] for r in chosen)),
            comparison=R.compare(first), observed_first_signal_events=events,
            comparison_unit='frozen_first_observed_signal_equal_cluster' if group == 'non_samsung' else 'inherited_policy_diagnostic',
            by_date={day: R.compare([r for r in first if r['day'] == day]) for day in sorted({r['day'] for r in chosen})},
            native_observation_count=sum(r['native_provenance'] is not None for r in chosen),
            policy_owner='SamsungFrozenCandidateValidation1006' if group == 'samsung' else A.RECIPE_ID)
    for source in sources:
        if source.get('sha256') and file_sha(source['path']) != source['sha256']:
            raise ValueError('admission_price_source_changed_during_analysis')
    if kernel_manifest() != kernels:
        raise ValueError('admission_kernel_changed_during_analysis')
    body = dict(schema=SCHEMA, **AUTHORITY, target_date=target_date, parent_sha256=S.digest(parent),
        input_count=len(scoped), observations=observations, groups=groups,
        exclusions=exclusions, source_manifest=sources, conflicting_price_keys=conflicts,
        kernel_manifest=kernels, input_capture_sha256=S.digest(scoped),
        recipe_discovery_through_date='2026-10-02', pristine_holdout=False,
        success_retention_role='diagnostic_only', samsung_candidate_selection='separate_owner')
    if designated_pair is not None:
        body['designated_pair'] = deepcopy(designated_pair)
        body['designated_kernel_sha256'] = file_sha(Path(D.__file__))
    body['artifact_content_sha256'] = S.digest(body)
    return body


def validate_report(report, *, parent, target_date, require_files=False):
    """Validate frozen provenance; only publication checks current local files."""
    if (not isinstance(report, dict) or report.get('schema') != SCHEMA
        or report.get('artifact_content_sha256') != S.digest({k: v for k, v in report.items() if k != 'artifact_content_sha256'})
        or report.get('parent_sha256') != S.digest(parent)
        or report.get('target_date') != target_date
        or any(report.get(k) != v for k, v in AUTHORITY.items())
        or report.get('recipe_discovery_through_date') != '2026-10-02'
        or report.get('pristine_holdout') is not False
        or not isinstance(report.get('kernel_manifest'), dict)
        or set(report['kernel_manifest']) != set(kernel_manifest())
        or not isinstance(report.get('source_manifest'), list)
        or not isinstance(report.get('observations'), list)):
        raise ValueError('admission_analysis_contract_invalid')
    traces = [r.get('trace') for r in report['observations']]
    if any(not isinstance(t, str) or not t for t in traces) or len(set(traces)) != len(traces):
        raise ValueError('admission_analysis_trace_invalid')
    if require_files:
        if report.get('designated_pair'):
            from src.engine.scalping import entry_designated_policy as D
            if report.get('designated_kernel_sha256') != file_sha(Path(D.__file__)):
                raise ValueError('admission_designated_kernel_changed')
        if report['kernel_manifest'] != kernel_manifest():
            raise ValueError('admission_analysis_kernel_changed')
        for source in report['source_manifest']:
            p = Path(source['path'])
            if (source.get('status') == 'observed' and file_sha(p) != source.get('sha256')) or (source.get('status') == 'missing' and p.exists()):
                raise ValueError('admission_analysis_price_source_changed')
    return report
