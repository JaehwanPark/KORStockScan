"""Pinned, read-only later-date consumer for the frozen Samsung shift1 rule.

Uses existing normalized trade shards, original machine captures and completed
prices. Independent collector corroboration never asserts Main tick identity.
"""
import argparse
from bisect import bisect_right
from collections import Counter
from datetime import date
import json
from pathlib import Path

from src.engine.scalping import samsung_continuous_tick_transition_research as C
from src.engine.scalping import samsung_policy_compatibility as K
from src.engine.scalping import ai_action_outcome_calibration as Q
from src.engine.scalping.entry_policy_hypothesis_research import stream_array
from src.engine.scalping.postclose_entry_validation import opportunity_identity

A, D, F, H, S, E, R = C.A, C.D, C.F, C.H, C.S, C.E, C.R
CANDIDATE = C.IDS[0]
RULE = dict(offset=1, width=10, pressure_boundary=60, endpoint_ttl_sec=5,
            unknown='absorption_action', known_fail='RECHECK')
SCHEMA = 'samsung_tick_transition_forward_consumer_v1'
AUTHORITY = dict(C.AUTHORITY, candidate_reselection=False, data_collected=False,
                 registered_runtime_policy=False, native_promotion_support=False)


def read(path):
    return json.loads(Path(path).read_text())


def registration(root, frozen_path):
    """Separate adapter receipt; never rewrite the original research frozen."""
    frozen_path = Path(frozen_path).resolve()
    frozen_sha = H.file_sha(frozen_path)
    frozen = read(frozen_path)
    body = frozen.get('result') or {}
    if (frozen != A.seal(frozen) or any(frozen.get(k) != v for k,v in C.AUTHORITY.items())
            or body.get('candidate_id') != CANDIDATE or body.get('rule') != RULE
            or body.get('base_action') != 'absorption_p60_v10'
            or body.get('later_source_after_date') != '2026-10-05'
            or body.get('recommendation_scope') != 'all_origins'
            or not body.get('source_seals') or not body.get('evidence')):
        raise ValueError('tick_forward_frozen_contract_changed')
    evidence = {}
    for name, sha in body['evidence'].items():
        if Path(name).name != name:
            raise ValueError('tick_forward_evidence_path_invalid')
        evidence[str(frozen_path.parent/name)] = sha
    C.verify_seals({**body['source_seals'], **evidence, str(frozen_path): frozen_sha})
    bases = [p for p in body['source_seals'] if Path(p).name == 'samsung-frozen.json']
    if len(bases) != 1:
        raise ValueError('tick_forward_absorption_parent_missing')
    base = read(bases[0]); A.validate_frozen(base, root=root)
    kernels = {str(Path(p).resolve()): H.file_sha(p) for p in (
        __file__, C.__file__, K.__file__, C.T.__file__, C.T.R.__file__)}
    kernels.update({str(Path(H.__file__).with_name(n)):h for n,h in A.kernels().items()})
    C.verify_seals({**body['source_seals'], **evidence, str(frozen_path): frozen_sha})
    return A.seal(dict(schema=SCHEMA, **AUTHORITY, candidate_id=CANDIDATE, rule=RULE,
        frozen_path=str(frozen_path), frozen_file_sha256=frozen_sha,
        base_frozen_path=bases[0], base_frozen_file_sha256=H.file_sha(bases[0]),
        later_source_after_date=body['later_source_after_date'], kernel_manifest=kernels,
        source_contract='original_capture_and_prices_plus_existing_normalized_SOR_trade_shards',
        clock_rule='original_input_asof_then_original_feature_receipt_if_unmatched',
        epoch_domain='independent_archive_collector', main_epoch_equivalence=False,
        owner='SamsungFrozenCandidateValidation1006', forward_adapter_status='implemented'))


def validate_registration(root, contract):
    if contract != registration(root, contract.get('frozen_path')):
        raise ValueError('tick_forward_consumer_contract_changed')


def current_receipt(raw, ticks, times, archive_sha):
    """The two already reviewed source clocks, with fixed priority, no search."""
    cutoff = D.number(raw.get('entry_machine_input_as_of'))
    def at(clock):
        end = bisect_right(times, clock) if D.number(clock) is not None else 0
        return F.historical_receipt(raw, ticks[max(0,end-10):end],
            archive_sha256=archive_sha, window_cutoff=clock)
    latest = at(cutoff)
    if F.valid_receipt(raw,latest):
        return latest, 'raw_entry_machine_input_as_of'
    trace = raw.get('entry_machine_input_trace') or {}
    receipt = (trace.get('entry_machine_input_quote_clock_comparison') or {}).get('feature_receipt') or {}
    owner = 'machine_refresh_clock'
    if not receipt:
        bbo = (((raw.get('ai_market_snapshot_v1') or {}).get('sources') or {}).get('bbo') or {})
        candidate = bbo.get('quote_source_receipt') or {}
        if (candidate.get('item') == '005930_AL'
                and all(candidate.get(k) == (raw.get('quote') or {}).get(k) for k in ('best_bid','best_ask'))):
            receipt = candidate
            owner = 'market_snapshot_bbo'
    clock = D.number(receipt.get('observed_epoch'))
    # Reject a future/missing canonical receipt rather than substitute a later tick.
    if (cutoff is None or clock is None or clock > cutoff
            or receipt.get('item') != '005930_AL'
            or receipt.get('market_route') != 'krx_nxt_integrated'):
        clock = None
    return at(clock), owner if clock is not None else 'source_clock_missing'


def resolved_path(original, bars):
    path = H.path(original, bars, seconds=600)
    if path['status'] == 'timeout':
        path = H.path(original, bars, seconds=3600)
    if path['status'] == 'timeout':
        end = H.capture_clock(original).timestamp()+3600
        last = [b for b in bars if b['t'] <= end][-1]
        path = dict(path, net_pct=(last['close']/path['reference_price']-1)*100-path['cost_pct'],
                    delay_sec=3600, terminal_observed_at=last['t'])
    return path


def summarize(rows):
    result = {}
    for scope, population in [('all_origins',rows),('fixed_watch',[r for r in rows if A.fixed_watch(r)])]:
        arms = {}
        for arm in ('baseline','absorption','H2',CANDIDATE):
            changed = [dict(r,candidate_action=C.action(r,arm)) for r in population]
            events = E.observed_action_runs(changed,key_function=C.event_key)
            selected = R.replay(E.mask_first_signals(changed,events),'candidate_action')
            arms[arm] = dict(A.metrics(selected),selected_ids=[r['trace'] for r in selected],
                outcome_counts=dict(Counter(D.outcome(r) for r in selected)))
        contrasts = {}
        for control in ('baseline','absorption','H2'):
            comparisons = {}
            for metric in arms[CANDIDATE]['date_equal_metrics']:
                common = sorted(set(arms[CANDIDATE]['metric_date_support'][metric]).intersection(
                    arms[control]['metric_date_support'][metric]))
                a = sum(arms[CANDIDATE]['by_date'][d][metric] for d in common)/len(common) if common else None
                b = sum(arms[control]['by_date'][d][metric] for d in common)/len(common) if common else None
                comparisons[metric] = dict(comparable_dates=common, candidate=a, control=b,
                    uplift_pp=a-b if common else None,
                    status='not_identifiable' if not common else 'improves' if a>b else 'no_improvement')
            contrasts[control] = comparisons
        result[scope] = dict(observations=len(population), arms=arms, comparisons=contrasts,
            conditions=dict(Counter(str(r['tick_conditions'][CANDIDATE]['condition']) for r in population)),
            condition_reasons=dict(Counter(r['tick_conditions'][CANDIDATE]['reason'] for r in population)))
    return result


def evaluate_captures(captures, ticks, archive_sha, prices, parent, *, validate_source):
    """Pure outcome-independent receipt/decision pass, then fixed path comparison."""
    times = [r['t'] for r in ticks]
    if times != sorted(times):
        raise ValueError('tick_forward_archive_order_invalid')
    index = C.archive_index(ticks)
    accepted, exclusions, previous, seen = [], [], {}, set()
    for original in sorted(captures,key=lambda r:(r.get('decision_ts',''),r.get('decision_trace_id',''))):
        if (original.get('stock_code'),original.get('effective_venue'),original.get('session_bucket')) != ('005930','KRX','KRX_REGULAR'):
            continue
        trace = original.get('decision_trace_id')
        if not trace or trace in seen:
            raise ValueError('tick_forward_duplicate_or_missing_trace')
        seen.add(trace)
        try:
            validate_source(original)
            raw = original['setup_evidence']['strategy_raw_input']
            H.capture_clock(original)
            if (not C.samsung_scope(raw) or S.digest(raw) != original['setup_evidence']['strategy_raw_sha256']
                    or original.get('outcome_request_code') not in ('005930','005930_AL')):
                raise ValueError('original_scope_or_raw_invalid')
        except (KeyError,ValueError,TypeError,OSError) as exc:
            exclusions.append(dict(trace=trace,reason=str(exc)))
            continue
        proof, clock_owner = current_receipt(raw,ticks,times,archive_sha)
        decision = F.evaluate(original['setup_evidence'],parent,source_receipt=proof,admission_mode='replace')
        if decision['parent_action'] != original['machine_action']:
            raise ValueError('tick_forward_parent_replay_changed')
        epoch = proof['archive_window'][-1]['ep'] if proof['archive_window'] else None
        key = (original['source_date'],original['outcome_request_code'],epoch)
        h2, h2_evidence = D.h2(raw,proof,previous.get(key))
        condition = C.transition(raw,proof,ticks,index,archive_sha,1)
        previous[key] = (raw,proof)
        try:
            native = list(opportunity_identity(original))
        except ValueError:
            native = None
        row = dict(trace=trace,day=original['source_date'],ts=original['decision_ts'],symbol='005930',group='samsung',
            source_bundle_sha256=original['bundle_sha256'],outcome_request_code=original['outcome_request_code'],
            raw_sha256=S.digest(raw),native_provenance=native,source_lane=original.get('source_lane'),archive_epoch=epoch,
            parent_action=decision['parent_action'],absorption_action=decision['proposed_action'],
            candidate_action=D.filtered_action(decision['proposed_action'],condition['condition']),
            conditions={'H2':h2},h2_evidence=h2_evidence,tick_conditions={CANDIDATE:condition},
            evaluator_receipt=decision,current_receipt=proof,clock_owner=clock_owner)
        accepted.append((row,original))
    # Labels do not choose clocks, windows, conditions, or alternative candidates.
    rows = []
    for row,original in accepted:
        bars = prices.get((row['day'],'005930','KRX','KRX_REGULAR',row['outcome_request_code']),[])
        rows.append(dict(row,path=resolved_path(original,bars)))
    return rows, exclusions


def source_paths(root, day):
    root = Path(root)
    capture = root/f'data/report/machine_observation_projection/machine_observation_projection_{day}_0_1.json'
    if not capture.is_file() and capture.with_suffix('.json.gz').is_file():
        capture = capture.with_suffix('.json.gz')
    return dict(capture=capture,
        prices=root/f'data/report/machine_completed_price_source/machine_completed_price_source_{day}.json',
        trades=root/f'data/observations/scalp_micro_reversion_forward/trade_date={day}/venue=SOR/session=SOR_REGULAR/market_stream.manifest.json')


def prepare(root, day, contract, output):
    root, output = Path(root), Path(output)
    validate_registration(root,contract)
    if date.fromisoformat(day).isoformat() != day or day <= contract['later_source_after_date']:
        raise ValueError('tick_forward_requires_new_source_date')
    output.mkdir(parents=True,exist_ok=False)
    paths = source_paths(root,day)
    missing = {k:str(p) for k,p in paths.items() if not p.is_file()}
    body = dict(schema='samsung_tick_transition_forward_result_v1', **AUTHORITY, day=day,
        candidate_id=CANDIDATE,consumer_contract_sha256=contract['artifact_content_sha256'],
        frozen_file_sha256=contract['frozen_file_sha256'],later_than_discovery=True,
        forward_adapter_status='implemented',source_paths={k:str(p) for k,p in paths.items()})
    def finish(result):
        value = A.seal(dict(body,**result))
        A.write(output/'result.json',value)
        return value
    if missing:
        return finish(dict(status='waiting_new_source_date',missing_source_paths=missing,
                           observations=[],comparisons=None))
    seals = {str(p):H.file_sha(p) for p in paths.values()}
    ticks, trade_census = C.T.R.stream_rows(root,day,'trade',seals)
    cache = output/'normalized-trades.json.gz'
    C.T.write_cache(cache,dict(day=day,rows=ticks,source_seals=seals,
        archive_role='existing_normalized_trade_source_for_frozen_shift1'))
    archive_sha = H.file_sha(cache); seals[str(cache)] = archive_sha
    prices, _, conflicts = H.price_index(root/'data',[day])
    captures = [r for r in stream_array(paths['capture']) if r.get('stock_code') == '005930']
    base = read(contract['base_frozen_path'])
    def validate_source(row):
        if row.get('source_date') != day or not Q._machine_source_contract_valid(row):
            raise ValueError('original_source_contract_invalid')
        K.source_bundle(root,base,row)
        sha = row['bundle_sha256']
        generation = root/'data/runtime/mechanistic_entry_policy/generations'/(sha+'.json')
        seals.setdefault(str(generation),H.file_sha(generation))
    rows, exclusions = evaluate_captures(captures,ticks,archive_sha,prices,base['parent_policy'],validate_source=validate_source)
    C.verify_seals(seals)
    validate_registration(root,contract)
    comparisons = summarize(rows)
    known = sum(r['tick_conditions'][CANDIDATE]['condition'] is not None for r in rows)
    return finish(dict(status='evaluated' if rows else 'source_quality_excluded_all' if exclusions else 'valid_empty',
        observations=rows,exclusions=exclusions,comparisons=comparisons,source_seals=seals,
        source_quality=dict(condition_identifiable=known,condition_unknown=len(rows)-known,
            status='identified_all' if rows and known==len(rows) else 'partially_identified' if known else 'not_identifiable'),
        trade_census=trade_census,price_conflicts=conflicts,policy_publication=False,
        performance_acceptance='report_only_requires_review',source_hashes_unchanged=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--register-frozen',type=Path)
    group.add_argument('--contract',type=Path)
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--date')
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.register_frozen:
        if args.date: parser.error('registration does not accept --date')
        value = registration(args.root,args.register_frozen)
        A.write(args.output,value)
        print(json.dumps(dict(status='consumer_registered',output=str(args.output))))
    else:
        if not args.date: parser.error('validation requires --date')
        value = prepare(args.root,args.date,read(args.contract),args.output)
        print(json.dumps(dict(status=value['status'],observations=len(value['observations']),output=str(args.output))))


if __name__ == '__main__':
    main()
