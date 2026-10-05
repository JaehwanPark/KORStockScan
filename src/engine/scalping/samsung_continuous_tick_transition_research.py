"""Two frozen, offline tick-window hypotheses on existing Samsung captures.

Only normalized, hash-bound research archives are consumed. No broker protocol,
source acquisition, policy publisher or runtime consumer is changed here.
"""
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import json
from pathlib import Path
from functools import cmp_to_key
from statistics import mean

from src.engine.scalping import samsung_absorption_differential_research as D
from src.engine.scalping import samsung_absorption_acceptance_research as A
from src.engine.scalping import entry_flat_buy_flow_research as F
from src.engine.scalping import entry_admission_analysis as H
from src.engine.scalping import entry_strategy_policy as S
from src.engine.scalping import entry_first_signal_exit_research as E
from src.engine.scalping import entry_observation_recipe_policy as R
from src.engine.scalping import samsung_event_timing_research as T

IDS = ('absorption_p60_tick_shift1_v1', 'absorption_p60_tick_disjoint10_v1')
DAYS = ('2026-09-29', '2026-09-30', '2026-10-02')
AUTHORITY = dict(**D.AUTHORITY, decision_authority='offline_research_only',
    primary_decision_metric='date_equal_complete_path_positive_rate',
    window_policy='frozen_three_previously_explored_dates',
    sample_floor='three_complete_paths_per_arm_on_two_comparable_dates',
    source_quality_gate='exact_current_window_and_received_prior_contiguous_ticks',
    forbidden_uses=['runtime_policy', 'orders', 'realized_profit', 'independent_holdout_claim'])


def verify_seals(seals):
    for path, sha in seals.items():
        if not Path(path).is_file() or H.file_sha(path) != sha:
            raise ValueError('tick_research_source_changed:' + str(path))


def artifact(path):
    value = json.loads(Path(path).read_text())
    if value != A.seal(value):
        raise ValueError('tick_research_artifact_seal_invalid:' + str(path))
    return value['result']


def archive_index(rows):
    index = defaultdict(list)
    for i, row in enumerate(rows):
        index[(row.get('ep'), row.get('seq'))].append(i)
    return index


def pressure(rows):
    buy = sum(r['q'] for r in rows if r['side'] == 'BUY')
    sell = sum(r['q'] for r in rows if r['side'] == 'SELL')
    return round(100 * buy / (buy + sell), 2) if buy + sell > 0 else None


def samsung_scope(raw):
    # Match the existing absorption evaluator's case normalization; raw bytes
    # and the hash-bound receipt retain their original spelling.
    return (raw.get('stock_code'), str(raw.get('effective_venue') or '').upper(),
            str(raw.get('session_bucket') or '').upper()) == ('005930','KRX','KRX_REGULAR')


def transition(raw, receipt, rows, index, archive_sha256, offset):
    """No outcome argument: match original W0, then inspect only its prefix."""
    if offset not in (1, 10):
        raise ValueError('unregistered_tick_window_offset')
    missing = lambda reason: dict(condition=None, reason=reason)
    if not samsung_scope(raw) or not F.valid_receipt(raw, receipt):
        return missing('current_receipt_invalid')
    if (receipt.get('schema') != F.HISTORICAL_SCHEMA
            or receipt.get('source_scope') != '005930_AL/SOR/SOR_REGULAR'
            or receipt.get('archive_sha256') != archive_sha256):
        return missing('current_window_not_exact')
    current = receipt['archive_window']
    locations = index.get((current[-1]['ep'], current[-1]['seq']), [])
    if len(locations) != 1:
        return missing('current_window_not_exact')
    end = locations[0] + 1
    if end < 10 or rows[end-10:end] != current:
        return missing('current_window_not_exact')
    if end < 10 + offset:
        return missing('prior_ticks_missing')
    combined = rows[end-10-offset:end]
    cutoff = raw['entry_machine_input_as_of']
    for tick in combined:
        if (type(tick.get('ep')) is not int or type(tick.get('seq')) is not int
                or len(index.get((tick['ep'], tick['seq']), [])) != 1
                or tick['ep'] != current[-1]['ep'] or tick.get('continuous') is not True):
            return missing('epoch_or_sequence_gap')
        if (D.number(tick.get('t')) is None or D.number(tick.get('ex')) is None
                or not 0 <= cutoff-tick['t'] or not 0 <= tick['t']-tick['ex'] <= 5):
            return missing('clock_unproven')
        if (D.number(tick.get('p')) is None or tick['p'] <= 0
                or D.number(tick.get('q')) is None or tick['q'] <= 0
                or tick.get('side') not in ('BUY', 'SELL')
                or tick.get('valid') is not True or tick.get('flow_valid') is not True):
            return missing('quantity_or_side_invalid')
    if any(b['seq'] != a['seq']+1 or b['t'] < a['t'] for a, b in zip(combined, combined[1:])):
        return missing('epoch_or_sequence_gap')
    previous = rows[end-10-offset:end-offset]
    if cutoff-previous[-1]['t'] > 5:
        return missing('prior_endpoint_stale')
    before, now = pressure(previous), pressure(current)
    return dict(condition=before < 60 <= now, reason='observed',
        previous_pressure=before, current_pressure=now,
        current_window_sha256=S.digest(current), previous_window_sha256=S.digest(previous),
        archive_sha256=archive_sha256, archive_epoch=current[-1]['ep'],
        archive_index_range=[end-10-offset, end], prior_endpoint_age_sec=cutoff-previous[-1]['t'],
        oldest_tick_age_sec=cutoff-combined[0]['t'], cutoff=cutoff,
        source_epoch_domain='independent_archive_collector', main_epoch_equivalence=False)


def event_key(row):
    native = row.get('native_provenance')
    watch = tuple(native[4:]) if isinstance(native, list) and len(native) == 7 else (
        'watch_identity_unavailable', row.get('source_lane'))
    return A._key(row) + (row['archive_epoch'],) + watch


def action(row, arm):
    if arm == 'baseline':
        return row['parent_action']
    if arm == 'absorption':
        return row['absorption_action']
    condition = row['conditions']['H2'] if arm == 'H2' else row['tick_conditions'][arm]['condition']
    return D.filtered_action(row['absorption_action'], condition)


def compare(rows, *, key_function=event_key):
    result = {}
    for scope, population in [('all_origins', rows), ('fixed_watch', [r for r in rows if A.fixed_watch(r)])]:
        arms = {}
        for arm in ('baseline', 'absorption', 'H2') + IDS:
            changed = [dict(r, candidate_action=action(r, arm)) for r in population]
            events = E.observed_action_runs(changed, key_function=key_function)
            chosen = R.replay(E.mask_first_signals(changed, events), 'candidate_action')
            metric = A.metrics(chosen)
            metric.update(selected_ids=[r['trace'] for r in chosen], observed_event_count=len(events),
                complete_path_count=sum(v['complete_path_count'] for v in metric['by_date'].values()),
                outcome_counts=dict(Counter(D.outcome(r) for r in chosen)))
            arms[arm] = metric
        result[scope] = arms
    return result


def recommend(comparisons, rows):
    scopes = {}
    primary, binary = 'positive_path_rate_pct', 'boundary_win_rate_pct'
    for scope, arms in comparisons.items():
        population = rows if scope == 'all_origins' else [r for r in rows if A.fixed_watch(r)]
        details, eligible = {}, []
        for candidate in IDS:
            arm = arms[candidate]
            # Compare on common evaluable dates. An abstention date has no
            # win rate; it is neither zero nor a requirement to preserve entry.
            dates = sorted(set(arm['metric_date_support'][primary]).intersection(
                *(arms[k]['metric_date_support'][primary] for k in ('baseline','absorption'))))
            common_counts = {k: sum(arms[k]['by_date'][d]['complete_path_count'] for d in dates)
                             for k in ('baseline','absorption',candidate)}
            common_rates = {k: mean(arms[k]['by_date'][d][primary] for d in dates) if dates else None
                            for k in ('baseline','absorption',candidate)}
            supported = len(dates) >= 2 and min(common_counts.values()) >= 3
            identifiable = sum(r['tick_conditions'][candidate]['condition'] is not None for r in population)
            uplift = common_rates[candidate]-common_rates['absorption'] if supported else None
            binary_dates = sorted(set(dates).intersection(arm['metric_date_support'][binary],
                arms['absorption']['metric_date_support'][binary]))
            binary_uplift = mean(arm['by_date'][d][binary]-arms['absorption']['by_date'][d][binary]
                                 for d in binary_dates) if binary_dates else None
            improves = bool(supported and uplift > 1e-9)
            conflict = improves and binary_uplift is not None and binary_uplift < -1e-9
            details[candidate] = dict(known_condition_count=identifiable, supported=supported,
                comparable_dates=dates, common_complete_counts=common_counts, common_positive_rates=common_rates,
                binary_comparable_dates=binary_dates,
                candidate_abstention_dates=sorted({r['day'] for r in population}-set(arm['by_date'])),
                positive_path_uplift_pp=uplift, binary_winrate_uplift_pp=binary_uplift,
                metric_conflict=conflict, improves_absorption=improves,
                status='not_identifiable' if not identifiable else 'insufficient_support' if not supported
                    else 'metric_conflict' if conflict else 'improves' if improves else 'no_improvement')
            if identifiable and improves and not conflict:
                eligible.append(candidate)
        def rank(left, right):
            delta = details[left]['positive_path_uplift_pp'] - details[right]['positive_path_uplift_pp']
            if abs(delta) > 1e-9:
                return -1 if delta > 0 else 1
            a, b = (details[k]['binary_winrate_uplift_pp'] for k in (left, right))
            if a is not None and b is not None and abs(a-b) > 1e-9:
                return -1 if a > b else 1
            return IDS.index(left)-IDS.index(right)
        eligible.sort(key=cmp_to_key(rank))
        selected = eligible[0] if eligible else None
        statuses = {v['status'] for v in details.values()}
        scopes[scope] = dict(candidate_id=selected, hypotheses=details,
            status='recommend_register_for_forward' if selected else 'not_identifiable' if statuses == {'not_identifiable'}
            else 'insufficient_support' if not any(v['supported'] for v in details.values())
            else 'metric_conflict' if 'metric_conflict' in statuses else 'no_improvement')
    selected = scopes['all_origins']['candidate_id'] or scopes['fixed_watch']['candidate_id']
    return dict(scopes=scopes, recommended_candidate=selected, selection_limit=1,
                status='recommend_register_for_forward' if selected else scopes['all_origins']['status'])


def census(rows):
    result = {}
    for scope, population in [('all_origins', rows), ('fixed_watch', [r for r in rows if A.fixed_watch(r)])]:
        details = {}
        for candidate in IDS:
            def counts(items):
                return dict(observations=len(items), known=sum(r['tick_conditions'][candidate]['condition'] is not None for r in items),
                    conditions=dict(Counter(str(r['tick_conditions'][candidate]['condition']) for r in items)),
                    reasons=dict(Counter(r['tick_conditions'][candidate]['reason'] for r in items)),
                    newly_known_vs_H2=sum(r['conditions']['H2'] is None and r['tick_conditions'][candidate]['condition'] is not None for r in items))
            details[candidate] = dict(total=counts(population),
                by_date={d: counts([r for r in population if r['day'] == d]) for d in DAYS},
                by_parent_action={a: counts([r for r in population if r['parent_action'] == a]) for a in ('ENTER_NOW','RECHECK','BLOCK')},
                absorption_enters=counts([r for r in population if r['absorption_action'] == 'ENTER_NOW']))
        result[scope] = details
    return result


def load_inputs(source_dir):
    from src.engine.scalping.entry_policy_hypothesis_research import stream_array
    source_dir = Path(source_dir).resolve()
    seals = {str(p): H.file_sha(p) for p in (source_dir/n for n in (
        'source-manifest.json','observations.json','comparisons.json','frozen-candidate.json'))}
    original_seals = artifact(source_dir/'source-manifest.json')['seals']
    seals.update(original_seals)
    verify_seals(seals)
    request_path = next(p for p in original_seals if Path(p).name == 'research-request.json')
    request = json.loads(Path(request_path).read_text())
    for item in request['files']:
        if seals.get(item['path']) != item['sha256']:
            raise ValueError('request_manifest_disagreement')
    base_path = Path(request_path).with_name('samsung-frozen.json')
    base = json.loads(base_path.read_text())
    frozen = json.loads((source_dir/'frozen-candidate.json').read_text())
    if (base != A.seal(base) or frozen != A.seal(frozen)
            or frozen.get('base_frozen_sha256') != S.digest(base)
            or base.get('parent_sha256') != request['parent_sha256']):
        raise ValueError('original_frozen_binding_invalid')
    seals[str(base_path)] = H.file_sha(base_path)
    rows = artifact(source_dir/'observations.json')['rows']
    if (len(rows) != 519 or len({r['trace'] for r in rows}) != 519
            or sum(A.fixed_watch(r) for r in rows) != 206 or sorted({r['day'] for r in rows}) != list(DAYS)):
        raise ValueError('frozen_population_changed')
    old_rows = {r['trace']: r for r in json.loads(Path(next(p for p in seals if Path(p).name == 'observation-research-report.json')).read_text())['observations']}
    originals, proofs, archives = {}, {}, {}
    wanted = {r['trace'] for r in rows}
    for item in request['files']:
        p = Path(item['path'])
        if item['role'] == 'capture':
            for r in stream_array(p):
                if r.get('decision_trace_id') in wanted:
                    if r['decision_trace_id'] in originals:
                        raise ValueError('duplicate_capture_identity')
                    originals[r['decision_trace_id']] = r
        elif item['role'] == 'samsung_receipt':
            records = json.loads(p.read_text())
            if len({r['trace'] for r in records}) != len(records):
                raise ValueError('duplicate_receipt_identity')
            proofs = {r['trace']: r['source_receipt'] for r in records}
        elif p.parent.name == 'locked-source':
            manifest_path = p.with_name('manifest.json')
            manifest = json.loads(manifest_path.read_text())
            normalizer = str(Path(T.R.__file__).resolve())
            if (manifest.get('kernel_manifest',{}).get(normalizer) != H.file_sha(normalizer)
                    or manifest.get('files',{}).get(p.name[:10],{}).get('sha256') != item['sha256']):
                raise ValueError('archive_normalizer_or_identity_contract_changed')
            seals[str(manifest_path)] = H.file_sha(manifest_path)
            body = T.read_cache(p)
            if body['day'] in archives:
                raise ValueError('duplicate_archive_day')
            archives[body['day']] = (body['rows'], archive_index(body['rows']), item['sha256'])
    for row in rows:
        if any(row.get(k) != v for k, v in old_rows[row['trace']].items()):
            raise ValueError('original_observation_changed')
        original = originals[row['trace']]
        raw = original['setup_evidence']['strategy_raw_input']
        if (S.digest(raw) != row['raw_sha256'] or H.capture_clock(original).isoformat() != row['ts']
                or original['machine_action'] != row['parent_action']
                or not samsung_scope(raw)
                or F.valid_receipt(raw, proofs[row['trace']]) != row['absorption_receipt_valid']):
            raise ValueError('original_capture_binding_invalid')
    # The input normalizer owns t=local_receive_timestamp, ex=exchange_timestamp,
    # and exact 005930_AL/SOR/SOR_REGULAR filtering. Seal that code as evidence.
    kernel_paths = {Path(__file__), Path(T.__file__), Path(T.R.__file__), Path(D.__file__), Path(A.__file__), Path(F.__file__)}
    kernel_paths.update(Path(H.__file__).with_name(n) for n in H.kernel_manifest())
    for p in kernel_paths:
        old = seals.get(str(p.resolve()))
        if old is not None and old != H.file_sha(p):
            raise ValueError('original_kernel_changed')
        seals[str(p.resolve())] = H.file_sha(p)
    return rows, originals, proofs, archives, seals


def run(source_dir, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    rows, originals, proofs, archives, seals = load_inputs(source_dir)
    registry = dict(new_candidates={k: dict(offset=n, width=10, pressure_boundary=60,
        endpoint_ttl_sec=5, unknown='absorption_action', known_fail='RECHECK') for k, n in zip(IDS, (1, 10))},
        controls=['baseline','absorption','H2'], maximum_policies=5, dates=list(DAYS))
    def write(name, result):
        A.write(output/(name+'.json'), dict(**AUTHORITY, result=result))
    write('hypothesis-registry', registry)
    for row in rows:
        raw = originals[row['trace']]['setup_evidence']['strategy_raw_input']
        ticks, index, sha = archives[row['day']]
        row['tick_conditions'] = {k: transition(raw, proofs[row['trace']], ticks, index, sha, n)
                                 for k, n in zip(IDS, (1, 10))}
    availability = census(rows)
    write('source-availability', availability)
    write('window-receipts', [{'trace': r['trace'], 'conditions': r['tick_conditions']} for r in rows])
    # R1 is complete before consuming any outcome for selection/comparison.
    comparisons = compare(rows)
    recommendation = recommend(comparisons, rows)
    sensitivity = {day: recommend(compare([r for r in rows if r['day'] != day]),
        [r for r in rows if r['day'] != day]) for day in DAYS}
    event_sensitivity = {}
    for candidate in IDS:
        changed = [dict(r, parent_action=r['absorption_action'], candidate_action=action(r,candidate)) for r in rows]
        events = E.observed_action_runs(changed, key_function=event_key)
        event_sensitivity[candidate] = []
        for event in events:
            if event['first_by_arm'].get('parent_action') == event['first_by_arm'].get('candidate_action'):
                continue
            omitted = set(event['observations'])
            retained = [r for r in rows if r['trace'] not in omitted]
            after = recommend(compare(retained), retained)
            event_sensitivity[candidate].append(dict(event_id=event['event_id'], omitted_observations=len(omitted),
                scopes={s: result['hypotheses'][candidate] for s,result in after['scopes'].items()}))
    price_path = next(Path(p) for p in seals if Path(p).name == 'machine_completed_price_source_2026-09-29.json')
    prices, _, _ = H.price_index(price_path.parents[2], DAYS)
    paired = {}
    for scope, population in [('all_origins',rows),('fixed_watch',[r for r in rows if A.fixed_watch(r)])]:
        paired[scope] = {}
        for candidate in IDS:
            changed = [dict(r, parent_action=r['absorption_action'], candidate_action=action(r,candidate)) for r in population]
            paired[scope][candidate] = dict(arms={'baseline':'absorption','absorption':candidate},
                events=D.paired_events(changed, originals, prices))
    recommendation['leave_one_date_out'] = sensitivity
    recommendation['leave_one_changed_event_out'] = event_sensitivity
    chosen = recommendation['recommended_candidate']
    if chosen:
        recommendation['sensitivity'] = 'single_event_or_day_sensitive' if any(
            v['recommended_candidate'] != chosen for v in sensitivity.values()) else 'date_exclusion_stable'
    verify_seals(seals)
    write('intake', dict(seals={p: dict(sha256=h, size=Path(p).stat().st_size) for p,h in seals.items()},
        rows=len(rows),fixed_watch=sum(A.fixed_watch(r) for r in rows), source_dates=list(DAYS),
        relocated_sources=[], retained_archive_clock='t=local_receive_timestamp; ex=exchange_timestamp',
        producer=str(Path(T.R.__file__).resolve()),main_epoch_equivalence=False))
    write('decisions', rows)
    write('paired-events', paired)
    write('comparisons', dict(arms=comparisons,legacy_cluster_sensitivity=compare(rows,key_function=A._key),
        grouping='original_watch_and_archive_epoch_observed_runs_then_stock_day_nonoverlap'))
    write('recommendation', recommendation)
    write('validation', dict(source_hashes_unchanged=True, population=519, fixed_watch=206,
        maximum_policies=5, original_observation_parity=True, current_window_exact=True,
        outcome_not_used_in_conditions=True, reviewed_source_domain='independent_archive_collector'))
    if chosen:
        # Separate research registration; the old H2 and its forward adapter stay intact.
        write('frozen-candidate', dict(candidate_id=chosen, rule=registry['new_candidates'][chosen],
            base_action='absorption_p60_v10', recommendation_scope='all_origins' if recommendation['scopes']['all_origins']['candidate_id'] == chosen else 'fixed_watch',
            later_source_after_date='2026-10-05', source_seals=seals,
            evidence={p.name:H.file_sha(p) for p in output.glob('*.json')},
            forward_adapter_status='not_implemented_for_new_tick_window_definition'))
    return recommendation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.source_dir, args.output), ensure_ascii=False))


if __name__ == '__main__':
    main()
