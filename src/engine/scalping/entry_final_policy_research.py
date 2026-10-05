"""Finite offline entry comparison; no policy publication or runtime imports.

Sensitivity holds selected entries fixed. Unknown labels are hypothetical binary
assignments, not recovered observations, confidence intervals or trading PnL.
"""
from collections import Counter, defaultdict
from datetime import datetime
from fractions import Fraction

from src.engine.scalping import entry_first_signal_exit_research as F
from src.engine.scalping import entry_observation_recipe_policy as R
from src.engine.trade_profit import calculate_net_profit_rate

AUTHORITY = dict(
    **R.AUTHORITY,
    primary_decision_metric='equal_cluster_cost_bound_target_first_win_rate',
    window_policy='frozen_first_signals_60m_20260929_20260930_20261002',
    sample_floor='existing_observation_comparison_contract',
    source_quality_gate='frozen_source_parent_kernel_and_trace_identity',
)
UNKNOWN = frozenset({
    'horizon_source_missing', 'horizon_identity_mismatch',
    'cost_missing_or_mismatched', 'entry_reference_mismatch', 'cost_missing',
    'first_partial_bar_ambiguous', 'same_bar_ambiguous', 'insufficient_followup',
    'horizon_contract_invalid', 'horizon_hit_clock_invalid', 'price_gap_before_hit',
})


def _index(rows):
    result = {}
    for row in rows:
        F.event_key(row)
        F.epoch(row)
        trace = row['trace']
        if not isinstance(trace, str) or not trace or trace in result:
            raise ValueError('final_comparison_duplicate_or_invalid_trace')
        if row['path']['status'] not in UNKNOWN | {'target', 'stop', 'timeout'}:
            raise ValueError('final_comparison_unknown_outcome_contract')
        result[trace] = row
    return result


def binary_assignment_sensitivity(parent, candidate):
    """Exact affine range within a declared all-unknowns-binary scenario.

Shared trace labels are coupled. Timeouts remain nonbinary. A missing row may
in reality time out or remain unidentifiable; this scenario does not impute it.
Weights include newly resolvable clusters, so the all-stop intercept generally
differs from the observed resolved-only difference. Occupancy is not replayed.
"""
    indices = [_index(parent), _index(candidate)]
    for trace in indices[0].keys() & indices[1].keys():
        if indices[0][trace] != indices[1][trace]:
            raise ValueError('final_comparison_shared_trace_mismatch')
    coefficients = defaultdict(Fraction)
    intercept = Fraction(0)
    arms = {}
    for name, rows, sign in [('parent', parent, -1), ('candidate', candidate, 1)]:
        groups = defaultdict(list)
        for row in rows:
            if row['path']['status'] != 'timeout':
                groups[R.cluster(row)].append(row)
        arms[name] = dict(binary_scenario_clusters=len(groups),
            known_timeout_excluded=sum(r['path']['status'] == 'timeout' for r in rows),
            unknown_count=sum(r['path']['status'] in UNKNOWN for r in rows))
        if not groups:
            return dict(status='binary_scenario_denominator_unavailable', arms=arms,
                lower_delta_pp=None, upper_delta_pp=None)
        for group in groups.values():
            weight = Fraction(sign * 100, len(groups) * len(group))
            for row in group:
                if row['path']['status'] == 'target':
                    intercept += weight
                elif row['path']['status'] in UNKNOWN:
                    coefficients[row['trace']] += weight
    lower = intercept + sum(min(Fraction(0), v) for v in coefficients.values())
    upper = intercept + sum(max(Fraction(0), v) for v in coefficients.values())
    # Fewest adverse target assignments from the all-unknown-stop scenario.
    # Candidate-only unknowns stay stop in this explicit stress scenario.
    delta, adverse = intercept, []
    for trace, value in sorted(coefficients.items(), key=lambda item: (item[1], item[0])):
        if delta <= 0 or value >= 0:
            break
        delta += value
        adverse.append(trace)
    overturn = (dict(count=len(adverse), trace_ids=adverse, delta_pp=float(delta))
                if delta <= 0 else None)
    return dict(status='hypothetical_binary_assignment_only', arms=arms,
        fixed_selected_entries=True, timeouts_imputed=False,
        missing_labels_recovered=False, occupancy_replayed=False,
        statistical_confidence_interval=False,
        shared_unknown_count=sum(t in indices[1] and r['path']['status'] in UNKNOWN
                                 for t, r in indices[0].items()),
        all_unknown_stop_delta_pp=float(intercept),
        all_unknown_target_delta_pp=float(intercept + sum(coefficients.values())),
        lower_delta_pp=float(lower), upper_delta_pp=float(upper),
        adverse_targets_to_nonpositive_from_all_stop=overturn,
        delta_formula=dict(intercept_pp=float(intercept),
            target_assignment_coefficients_pp={k: float(v) for k, v in sorted(coefficients.items())}),
        limitation='Unknowns are assumed target or stop; unknown-to-timeout and changed occupancy are not modelled.')


def compare_selected(parent, candidate, events):
    pi, ci = _index(parent), _index(candidate)
    sensitivity = binary_assignment_sensitivity(parent, candidate)
    shared = pi.keys() & ci.keys()
    arms = {name: R.metrics(rows) for name, rows in [('parent', parent), ('candidate', candidate)]}
    paired_clusters = set(R.cluster(r) for r in parent if r['path']['status'] in {'target', 'stop'})
    paired_clusters &= set(R.cluster(r) for r in candidate if r['path']['status'] in {'target', 'stop'})
    paired = {name: R.metrics([r for r in rows if R.cluster(r) in paired_clusters])
              for name, rows in [('parent', parent), ('candidate', candidate)]}
    selected_events = {name: {e['event_id'] for e in events
        if e['first_by_arm'].get(name + '_action') in index}
        for name, index in [('parent', pi), ('candidate', ci)]}
    for name, rows in [('parent', parent), ('candidate', candidate)]:
        if len(selected_events[name]) != len(rows):
            raise ValueError('final_comparison_selected_event_binding_invalid')
        arms[name]['selected_event_count'] = len(selected_events[name])
        arms[name]['event_participation_pct'] = 100 * len(selected_events[name]) / len(events) if events else None
        arms[name]['unresolved_count'] = sum(r['path']['status'] in UNKNOWN for r in rows)
    return dict(**arms,
        shared_trace_count=len(shared),
        shared_selected_event_count=len(selected_events['parent'] & selected_events['candidate']),
        parent_only=R.metrics([r for t, r in pi.items() if t not in ci]),
        candidate_only=R.metrics([r for t, r in ci.items() if t not in pi]),
        common_resolved_cluster_comparison=paired,
        binary_assignment_sensitivity=sensitivity)


def bar_reach_diagnostic(row, bars, *, policy):
    """Observe full-bar highs in the fixed window, even after a hypothetical exit.

No reach in available bars is not proof of no reach in partial/missing bars.
This is intentionally separate from the ordered conditional exit simulation.
"""
    F.validate_exit_policy(policy)
    start = F.epoch(row)
    end = min(start + 3600, datetime.fromisoformat(row['ts']).astimezone(F.KST)
              .replace(hour=15, minute=30, second=0, microsecond=0).timestamp())
    entry = R.number(row.get('reference_price'))
    cost = R.number((row.get('features') or {}).get('entry_cost_pct'))
    unknown = lambda reason: dict(status='not_evaluable', reason=reason,
        trailing_start_observed=None, real_fill=False)
    if entry is None or entry <= 0 or row.get('capture_valid') is not True or row.get('reference_type') != 'executable_ask':
        return unknown('entry_reference_invalid')
    if cost is None or cost < 0:
        return unknown('cost_contract_missing')
    times = [R.number(b.get('t')) for b in bars]
    if any(t is None for t in times) or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('final_reach_bar_clock_invalid')
    selected = [b for b in bars if start < b['t'] <= end]
    for b in selected:
        if (any(R.number(b.get(k)) is None for k in ('open', 'high', 'low', 'close'))
                or not 0 < b['low'] <= min(b['open'], b['close'])
                or max(b['open'], b['close']) > b['high']):
            return unknown('bar_invalid')
    full = [b for b in selected if b['t'] >= start + 60]
    if not full:
        return unknown('no_full_postentry_bar')
    hits = [b for b in full if calculate_net_profit_rate(entry, b['high'],
        cost_rate=policy['runtime_cost_rate']) >= policy['start_pct']]
    stamps = [start] + [b['t'] for b in selected] + [end]
    return dict(status='observed_full_bar_reach' if hits else 'not_observed_in_available_full_bars',
        trailing_start_observed=bool(hits), first_reach_bar_at=hits[0]['t'] if hits else None,
        full_bar_count=len(full), partial_bar_excluded=len(selected) != len(full),
        max_interval_sec=max(b-a for a, b in zip(stamps, stamps[1:])),
        after_hypothetical_exit_bars_included=True, real_fill=False,
        actual_trailing_armed_proven=False)


def exit_cross_table(rows, reach, paths):
    _index(rows)
    table = Counter()
    for row in rows:
        trace = row['trace']
        for width in ('weak', 'strong'):
            path = paths[width][trace]
            net = path.get('net_pct')
            if net is not None and (R.number(net) is None or path['status'] != 'conditional_bar_exit'):
                raise ValueError('final_exit_numeric_outcome_invalid')
            outcome = 'unknown' if net is None else 'positive' if net > 0 else 'nonpositive'
            table[(row['path']['status'], reach[trace]['status'], width,
                   path['status'], str(path.get('rule')), outcome)] += 1
    return dict(selected_count=len(rows),
        reach_counts=dict(Counter(reach[r['trace']]['status'] for r in rows)),
        scenarios={w: F.summarize_paths(rows, paths[w]) for w in ('weak', 'strong')},
        cells=[dict(entry_outcome=k[0], reach=k[1], width=k[2], exit_status=k[3],
                    exit_rule=k[4], exit_sign=k[5], count=v) for k, v in sorted(table.items())],
        entry_selection_veto=False, actual_operating_pnl=False)
