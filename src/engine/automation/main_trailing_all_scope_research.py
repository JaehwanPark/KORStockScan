"""Isolated, resumable all-scope Main exit research; no provider/order calls.

The automation package owns orchestration. Scalping modules own scope,
classification, shared runtime decisions and executable path semantics.
The default command is a read-only preflight. Explicit output roots contain
only minimal results/checkpoints and a parent-equivalent initial bundle.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import ExitStack
from datetime import date
import hashlib
import json
from pathlib import Path

from src.engine.lifecycle.holding_window_generation import capture_window, verify_window
from src.engine.lifecycle.holding_window_generation import byte_generation, source_stat
from src.engine.scalping.main_exit_scope import build_scope, scope_digest
from src.engine.scalping.pre_submit_delay_initial_policy import digest, _atomic, number
from src.engine.lifecycle.research_input_budget import Claim, health as budget_health
from src.engine.scalping.trailing_mechanical_policy import market_values_hash
from src.engine.scalping.trailing_mechanical_policy import classifier_hash
from src.engine.automation.main_trailing_path_projection import load_or_build
from src.engine.scalping.trailing_situation_policy import initial_bundle, research_registered_grid
from src.engine.scalping.universal_trailing_replay import summarize_partitions, common_evaluation

SCHEMA = 'main_all_scope_exit_research_v1'
INPUT_SCHEMA = 'main_all_scope_exit_input_manifest_v1'
MAX_PARTITIONS = 1024
MAX_POSITIONS = 20000
MAX_SHARED_BYTES = 64 * 1024 * 1024
CODE_PATHS = ('automation/main_trailing_all_scope_research.py', 'lifecycle/holding_window_generation.py',
              'automation/main_trailing_path_projection.py',
              'lifecycle/research_input_budget.py',
              'scalping/main_exit_scope.py', 'scalping/universal_trailing_replay.py',
              'scalping/trailing_situation_policy.py', 'scalping/trailing_mechanical_strength.py',
              'scalping/trailing_exit_decision.py', 'scalping/trailing_threshold_policy.py',
              'scalping/trailing_mechanical_policy.py', 'scalping/pre_submit_delay_initial_policy.py',
              'sniper_state_handlers.py', 'sniper_trade_review_report.py', 'holding_exit_observation_report.py',
              'scalping/position_peak_ledger.py', 'scalping/holding_profit_exit_semantics.py',
              'lifecycle/broker_cost_source.py', 'lifecycle/broker_cost_reconciliation.py',
              '../utils/pipeline_event_logger.py',
              '../trading/market/session_contract.py')


def code_contract():
    root = Path(__file__).resolve().parents[1]
    return digest({name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in CODE_PATHS})


def _cost_revision_result(previous):
    """An unchanged normalized input cannot supply revised actual costs.

    Invalidate its actual economics without reparsing unchanged tick histories.
    Frozen model-only populations are cost-source independent. A newly sealed
    reconciled position changes the source key and follows the normal replay.
    """
    result = json.loads(json.dumps(previous))
    for identity, context in result['population_context'].items():
        if context['evidence_kind'] != 'actual_completed':
            continue
        for outcome in result['minimal_results'][identity].values():
            if outcome.get('actual_pnl_krw') is not None:
                outcome.update(status='source_gap', reason='actual_completed_cost_or_terminal_unverified',
                    actual_pnl_krw=None, modeled_net_pnl_krw=None, modeled_profit_rate_pct=None,
                    slippage_net_pnl_krw=None, modeled_residual_qty=None)
    result['common_ids'] = sorted(identity for identity, values in result['minimal_results'].items()
                                 if all(row['modeled_net_pnl_krw'] is not None for row in values.values()))
    result['excluded_ids'] = sorted(set(result['population_ids']) - set(result['common_ids']))
    result['status_counts'] = dict(Counter(row['status'] for values in result['minimal_results'].values()
                                         for row in values.values()))
    result.pop('artifact_sha256')
    result['artifact_sha256'] = digest(result)
    return result


def _source_path(root, name):
    path = root / name
    if not isinstance(name, str) or Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError('all_scope_source_path_invalid')
    if (path.resolve().is_relative_to(root.resolve()) is not True or path.is_symlink()
            or any(parent.is_symlink() for parent in path.parents)):
        raise ValueError('all_scope_source_path_invalid')
    return path


def _sealed(path, expected=None, generations=None):
    before = path.stat()
    if path.is_symlink() or before.st_size > 4 * 1024 * 1024:
        raise ValueError('all_scope_source_partition_budget_invalid')
    raw = path.read_bytes()
    if source_stat(path.stat()) != source_stat(before) or len(raw) != before.st_size:
        raise ValueError('all_scope_source_changed_during_read')
    value = json.loads(raw)
    body = {k:v for k,v in value.items() if k != 'artifact_sha256'}
    sha = digest(body)
    if value.get('artifact_sha256') != sha or (expected is not None and digest(value) != expected):
        raise ValueError('all_scope_source_generation_invalid')
    if generations is not None:
        generations[str(path)] = hashlib.sha256(raw).hexdigest()
    return value


def preflight(manifest_path, input_root, generations=None, *, scope_budget=None):
    manifest = _sealed(Path(manifest_path), generations=generations)
    if (manifest.get('schema') != INPUT_SCHEMA or len(manifest.get('partitions', [])) > MAX_PARTITIONS
            or not '2026-06-05' <= manifest['source_date'] <= manifest['target_date']
            or date.fromisoformat(manifest['source_date']).isoformat() != manifest['source_date']
            or date.fromisoformat(manifest['target_date']).isoformat() != manifest['target_date']):
        raise ValueError('all_scope_input_manifest_invalid')
    receipt = manifest['approved_parent_receipt']
    parent_source = manifest.get('approved_parent_source')
    if not isinstance(parent_source, dict):
        raise ValueError('all_scope_approved_parent_source_unverified')
    parent_path = _source_path(Path(input_root), parent_source['path'])
    parent_generation = byte_generation(parent_path)
    if parent_generation['sha256'] != parent_source.get('sha256') or parent_generation['size'] > 4*1024*1024:
        raise ValueError('all_scope_approved_parent_source_changed')
    parent = json.loads(parent_path.read_bytes())
    from src.engine.automation.runtime_policy_bootstrap import _digest_json
    if (parent.get('manifest_sha256') != _digest_json({k:v for k,v in parent.items() if k != 'manifest_sha256'})
            or parent.get('scalp_trailing_mechanical_policy_receipt') != receipt):
        raise ValueError('all_scope_approved_parent_receipt_unbound')
    if generations is not None:
        generations[str(parent_path)] = parent_generation['sha256']
    if (receipt.get('source') not in {'operator_directed_m1_baseline', 'reviewed_selected_candidate', 'rollback_incumbent'}
            or market_values_hash(receipt['market_values'], receipt['classifier_parameters']) != receipt['market_values_sha256']):
        raise ValueError('all_scope_approved_parent_generation_invalid')
    if scope_budget is not None:
        from src.engine.scalping.reversal_registered_catalog import ROUTES
        # Reserve the complete scope expansion before constructing its rows.
        scope_budget.grow(len(manifest['universe']) * sum(map(len, ROUTES.values())) * 512)
    scope = build_scope(manifest['universe'], as_of=manifest['as_of'],
        universe_source_sha256=manifest['universe_source_sha256'], operating=manifest.get('operating'),
        coverage=manifest.get('coverage'), custody=manifest.get('custody'))
    inventory = []
    for part in manifest['partitions']:
        path = _source_path(Path(input_root), part['path'])
        if not path.is_file() or path.stat().st_size > 4 * 1024 * 1024:
            inventory.append({'path':part['path'], 'status':'source_gap_or_partition_required'})
        else:
            inventory.append({'path':part['path'], 'status':'bounded_observed'})
    return manifest, scope, inventory


def run(manifest_path, *, input_root, output_root=None, dry_run=True, resume=False):
    with ExitStack() as budget:
        budget.enter_context(Claim(Path(manifest_path).stat().st_size * 8))
        return _run(manifest_path, input_root=input_root, output_root=output_root,
                    dry_run=dry_run, resume=resume, budget=budget)


def _run(manifest_path, *, input_root, output_root, dry_run, resume, budget):
    root = Path(input_root)
    generations = {}
    scope_claim = budget.enter_context(Claim(0))
    manifest, scope, inventory = preflight(manifest_path, root, generations, scope_budget=scope_claim)
    as_of = scope['as_of']
    if output_root is None:
        return {'schema':SCHEMA, 'status':'preflight_only', 'scope':scope, 'inventory':inventory,
                'runtime_effect':False, 'allowed_runtime_apply':False}
    out = Path(output_root)
    # Research never overwrites the operator's source or operational output.
    if out.resolve() == root.resolve() or out.resolve().is_relative_to(root.resolve()):
        raise ValueError('all_scope_isolated_output_root_required')
    if not dry_run and len(scope['scopes']) > 4000:
        partitions = []
        for offset in range(0, len(scope['scopes']), 4000):
            block = {'schema':scope['schema'], 'universe_snapshot_sha256':scope['universe_snapshot_sha256'],
                     'offset':offset, 'scopes':scope['scopes'][offset:offset+4000]}
            block['artifact_sha256'] = digest(block)
            name = f'scope-{scope["universe_snapshot_sha256"]}-{offset}.json'
            _atomic(out / 'scope' / name, block)
            partitions.append({'path':'scope/'+name, 'artifact_sha256':block['artifact_sha256'], 'count':len(block['scopes'])})
        scope = {k:v for k,v in scope.items() if k != 'scopes'}
        scope['partitions'] = partitions
        del block
        scope_claim.close()
        budget.enter_context(Claim(len(json.dumps(scope).encode()) * 8))
    window = capture_window(root, manifest['consumed_dates'])
    contract = code_contract()
    parent = manifest['approved_parent_receipt']
    candidates = manifest.get('candidates', {})
    global_results, seen, influence, gaps = [], set(), {}, []
    retained_claims, binary_sources, projection_bytes = [], {}, {}
    counters = Counter()
    for part, status in zip(manifest['partitions'], inventory):
        if status['status'] != 'bounded_observed':
            gaps.append(status)
            continue
        path = _source_path(root, part['path'])
        dates = part.get('consumed_dates')
        if (not isinstance(dates, list) or not dates or len(dates) != len(set(dates))
                or not set(dates) <= set(window['dates'])):
            raise ValueError('all_scope_partition_dependency_unverified')
        costs = {day:window['dependencies'][day]['cost_generation'] for day in dates}
        context = {'source_date':manifest['source_date'], 'as_of':manifest['as_of'],
                   'consumed_dates':sorted(dates), 'schema':INPUT_SCHEMA}
        generation = digest([part['artifact_sha256'], context, costs, parent, candidates, contract])
        source_base = digest([part['artifact_sha256'], context, parent, candidates, contract])
        index_path = out / 'source_dependencies' / (source_base + '.json')
        cache_path = out / 'partitions' / (generation + '.json')
        cached = None
        checkpoint_claim = None
        if resume and cache_path.exists():
            # Checkpoints are derived data. A damaged bounded checkpoint can
            # be rebuilt from the independently sealed input partition; it
            # must not invalidate other healthy partitions or relax inputs.
            if cache_path.stat().st_size <= 4 * 1024 * 1024:
                checkpoint_claim = budget.enter_context(Claim(cache_path.stat().st_size * 8))
                try:
                    cached = _sealed(cache_path)
                    result = cached['result']
                    if (cached.get('input_generation_sha256') != generation
                            or result.get('artifact_sha256') != digest({
                                k:v for k,v in result.items() if k != 'artifact_sha256'})):
                        raise ValueError('all_scope_checkpoint_generation_invalid')
                except (OSError, ValueError, KeyError, TypeError, AttributeError):
                    cached = None
            if cached is None:
                counters['checkpoint_invalid_rebuilt'] += 1
                if checkpoint_claim is not None:
                    checkpoint_claim.close()
            else:
                counters['checkpoint_reused'] += 1
        if (cached is None and not cache_path.exists() and resume and index_path.is_file()
                and index_path.stat().st_size <= 4096):
            index_claim = budget.enter_context(Claim(index_path.stat().st_size * 8))
            try:
                index = _sealed(index_path)
                prior_generation = index.get('result_generation')
                if (index.get('source_base_generation') != source_base or not isinstance(prior_generation, str)
                        or len(prior_generation) != 64 or any(c not in '0123456789abcdef' for c in prior_generation)):
                    raise ValueError('all_scope_dependency_index_invalid')
                prior_path = out / 'partitions' / (prior_generation + '.json')
                if prior_path.stat().st_size > 4*1024*1024:
                    raise ValueError('all_scope_dependency_checkpoint_invalid')
                checkpoint_claim = budget.enter_context(Claim(prior_path.stat().st_size * 8))
                prior = _sealed(prior_path)
                if (prior.get('source_base_generation') != source_base
                        or prior.get('input_generation_sha256') != prior_generation
                        or prior.get('source_binary_generation') != byte_generation(path)
                        or prior['result'].get('artifact_sha256') != digest({
                            k:v for k,v in prior['result'].items() if k != 'artifact_sha256'})):
                    raise ValueError('all_scope_dependency_checkpoint_invalid')
                cached = {**prior, 'input_generation_sha256':generation,
                          'result':_cost_revision_result(prior['result'])}
                cached.pop('artifact_sha256')
                cached['artifact_sha256'] = digest(cached)
                del prior
                counters['cost_only_source_reused'] += 1
                if not dry_run:
                    _atomic(cache_path, cached)
            except (OSError, ValueError, KeyError, TypeError, AttributeError):
                cached = None
                counters['dependency_index_invalid_rebuilt'] += 1
                if checkpoint_claim is not None:
                    checkpoint_claim.close()
            finally:
                index_claim.close()
        if cached is None:
            if dry_run:
                claim = budget.enter_context(Claim(path.stat().st_size * 8))
                payload = _sealed(path, part['artifact_sha256'], generations)
                paths = payload['paths']
                if any(isinstance(events,dict) and 'segments' in events for events in paths.values()):
                    raise ValueError('all_scope_segmented_replay_requires_explicit_isolated_checkpoint_output')
                source_paths = {str(path):byte_generation(path)}
                counters['decoded_partitions'] += 1
            else:
                configs = {}
                for candidate in [parent,*candidates.values()]:
                    config = candidate.get('classifier_parameters') if 'market_values' in candidate else None
                    configs[classifier_hash(config)] = config
                payload, paths, claim = load_or_build(path,root=root,out=out/'source_features',
                    expected=part['artifact_sha256'],as_of=as_of,source_date=manifest['source_date'],
                    configs=list(configs.values()),counters=counters,resume=resume,used_bytes=projection_bytes)
                budget.enter_context(claim)
                source_paths = payload['sources']
            if payload.get('source_date') != manifest['source_date']:
                raise ValueError('all_scope_partition_date_invalid')
            positions = payload['positions']
            if len(positions) > 500:
                raise ValueError('all_scope_partition_position_budget_exceeded')
            positions = [{**row, 'entry_at':None} if number(row.get('entry_at')) is None
                          or number(row['entry_at']) > as_of else row for row in positions]
            for row in positions:
                actual = row.get('actual_cost_reconciliation') or {}
                if row.get('evidence_kind') == 'actual_completed' and (number(actual.get('known_at')) is None
                        or number(actual['known_at']) > as_of):
                    row['actual_cost_reconciliation'] = {}
            # Old actual-cost revisions never reuse a stale reconciled row.
            if payload.get('cost_generations') != costs:
                positions = [{**row, 'actual_cost_reconciliation':{}} if row.get('evidence_kind') == 'actual_completed'
                             else row for row in positions]
            filtered_paths = {}
            for identity, events in paths.items():
                if not isinstance(events, list):
                    filtered_paths[identity] = events
                    continue
                filtered_paths[identity] = [event for event in events if not isinstance(event, dict)
                    or number(event.get('known_at')) is None or number(event['known_at']) <= as_of]
                excluded = len(events) - len(filtered_paths[identity])
                if excluded:
                    counters['as_of_future_events_excluded'] += excluded
            result = summarize_partitions(positions, filtered_paths, candidates, incumbent={
                'market_values':parent['market_values'], 'classifier_parameters':parent['classifier_parameters']})
            del positions, paths, filtered_paths, payload
            claim.close()
            cached = {'schema':SCHEMA, 'input_generation_sha256':generation,
                      'source_base_generation':source_base,
                      'source_binary_generation':byte_generation(path),
                      'source_path_generations':source_paths,
                      'source_partition_sha256':part['artifact_sha256'], 'consumed_dates':dates, 'result':result}
            cached['artifact_sha256'] = digest(cached)
            if not dry_run:
                _atomic(cache_path, cached)
        if not dry_run:
            index = {'schema':'main_all_scope_source_dependency_index_v1',
                     'source_base_generation':source_base, 'result_generation':generation}
            index['artifact_sha256'] = digest(index)
            _atomic(index_path, index)
        binary_sources[str(path)] = cached['source_binary_generation']
        binary_sources.update(cached.get('source_path_generations', {}))
        result_size = len(json.dumps(cached['result'], allow_nan=False).encode())
        if dry_run:
            retained_claims.append(budget.enter_context(Claim(result_size * 4)))
        ids = set(cached['result']['population_ids'])
        if seen & ids or len(seen | ids) > MAX_POSITIONS:
            raise ValueError('all_scope_global_population_identity_or_budget_invalid')
        seen.update(ids)
        if dry_run:
            global_results.append(cached['result'])
        else:
            global_results.append({'path':str(cache_path), 'artifact_sha256':cached['artifact_sha256'],
                                   'input_generation_sha256':generation, 'result_bytes':result_size})
        influence[part['path']] = dates
        if checkpoint_claim is not None:
            checkpoint_claim.close()
        if not dry_run:
            del cached
            result = None
        # Both research families share this declared resident-data ceiling.
        # Larger inputs require another sealed partition, never a tail slice.
    expected_ids = manifest.get('population_ids')
    if not isinstance(expected_ids, list) or len(expected_ids) != len(set(expected_ids)):
        raise ValueError('all_scope_global_census_unverified')
    missing = sorted(set(expected_ids) - seen)
    extra = sorted(seen - set(expected_ids))
    if extra:
        raise ValueError('all_scope_global_census_unexpected_identity')
    baseline = initial_bundle(parent['market_values'], parent_sha256=parent['market_values_sha256'],
        source_date=manifest['source_date'], target_date=manifest['target_date'],
        parent_classifier_parameters=parent['classifier_parameters'], classifier=manifest.get('situation_classifier'))
    def result_stream():
        for reference in global_results:
            path = Path(reference['path'])
            with Claim(path.stat().st_size * 8):
                checkpoint = _sealed(path)
                if (checkpoint.get('artifact_sha256') != reference['artifact_sha256']
                        or checkpoint.get('input_generation_sha256') != reference['input_generation_sha256']):
                    raise ValueError('all_scope_checkpoint_changed_during_aggregation')
                yield checkpoint['result']
    evaluation = common_evaluation(global_results if dry_run else result_stream)
    type_research = research_registered_grid(global_results if dry_run else result_stream,
        grid=manifest.get('situation_classifier_grid'), candidates=candidates,
        parent_values=parent['market_values'], parent_classifier_parameters=parent['classifier_parameters'],
        evaluation=evaluation)
    if type_research.get('classifier') is not None:
        baseline = initial_bundle(parent['market_values'], parent_sha256=parent['market_values_sha256'],
            source_date=manifest['source_date'], target_date=manifest['target_date'],
            parent_classifier_parameters=parent['classifier_parameters'], classifier=type_research['classifier'])
    # Aggregation and type training may be long. Verify immutable sources at
    # the last publication boundary, not just before those consumers run.
    verify_window(root, window)
    for name, sha in generations.items():
        if byte_generation(Path(name))['sha256'] != sha:
            raise ValueError('all_scope_manifest_or_partition_changed_during_research')
    for name, expected in binary_sources.items():
        if byte_generation(Path(name)) != expected:
            raise ValueError('all_scope_source_changed_after_checkpoint')
    if code_contract() != contract:
        raise ValueError('all_scope_code_changed_during_research')
    body = {'schema':SCHEMA, 'source_date':manifest['source_date'], 'target_date':manifest['target_date'],
        'status':'complete' if not missing and not gaps else 'source_gap', 'scope':scope,
        'population_ids':sorted(seen), 'missing_population_ids':missing, 'source_gaps':gaps,
        'partition_results':global_results, 'cost_influence_graph':influence,
        'common_population_evaluation':evaluation,
        'trailing_situation_research':type_research,
        'input_window_dependencies':window, 'input_window_generation_sha256':window['input_window_generation_sha256'],
        'code_contract_sha256':contract, 'counters':dict(counters), 'shared_resident_budget_bytes':MAX_SHARED_BYTES,
        'shared_budget_health':budget_health(),
        'initial_policy':baseline, 'runtime_effect':False, 'allowed_runtime_apply':False,
        'actual_pid_consumed':False}
    report = {**body, 'artifact_sha256':scope_digest(body)}
    if not dry_run:
        if 'scopes' in scope and len(json.dumps(scope, allow_nan=False).encode()) > 2 * 1024 * 1024:
            partitions = []
            for offset in range(0, len(scope['scopes']), 4000):
                block = {'schema':scope['schema'], 'universe_snapshot_sha256':scope['universe_snapshot_sha256'],
                         'offset':offset, 'scopes':scope['scopes'][offset:offset+4000]}
                block['artifact_sha256'] = digest(block)
                name = f'scope-{scope["universe_snapshot_sha256"]}-{offset}.json'
                _atomic(out / 'scope' / name, block)
                partitions.append({'path':'scope/'+name, 'artifact_sha256':block['artifact_sha256'], 'count':len(block['scopes'])})
            report['scope'] = {k:v for k,v in scope.items() if k != 'scopes'}
            report['scope']['partitions'] = partitions
            report['artifact_sha256'] = digest({k:v for k,v in report.items() if k != 'artifact_sha256'})
        _atomic(out / ('research_' + manifest['source_date'] + '.json'), report)
        _atomic(out / ('initial_policy_' + manifest['target_date'] + '.json'), baseline)
    scope_claim.close()
    for claim in retained_claims:
        claim.close()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-manifest', type=Path, required=True)
    parser.add_argument('--input-root', type=Path, required=True)
    parser.add_argument('--output-root', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args(argv)
    report = run(args.input_manifest, input_root=args.input_root, output_root=args.output_root,
                 dry_run=args.dry_run or args.output_root is None, resume=args.resume)
    print(json.dumps({key:report.get(key) for key in ('status','source_date','target_date','counters','missing_population_ids')}))
    return 0 if report['status'] in {'complete','preflight_only'} else 2


if __name__ == '__main__':
    raise SystemExit(main())
