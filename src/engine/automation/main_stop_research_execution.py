"""Execute bounded, report-only stop research against immutable native sources.

Outputs live in an explicit private directory. No policy/bootstrap pointer,
source journal, account, provider, or order is written. Historical comparison
is diagnostic and cannot masquerade as a prospective holdout experiment.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import ExitStack
from dataclasses import asdict
from datetime import datetime
import fcntl
import hashlib
import json
import math
import resource
import tempfile
import time
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.automation import main_stop_postclose as post
from src.engine.automation import main_stop_source_index as source_index
from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.holding_window_generation import byte_generation, source_stat
from src.engine.lifecycle.research_disk_budget import use
from src.engine.scalping import main_stop_policy as policy
from src.engine.scalping.main_stop_replay import candidates, holding_contracts, preset_decision, replay
from src.engine.scalping.pre_submit_delay_initial_policy import _atomic

SCHEMA = 'main_stop_execution_research_v1'
KST = ZoneInfo('Asia/Seoul')
MAX_EXAMPLES = 16
MAX_SECONDS = 14400
MAX_REPORT_BYTES = 1024 * 1024
COST_GRADES = ('exact_execution', 'exact_position_total', 'broker_total_allocated')
RESEARCH_CODE_PATHS = (
    'automation/main_stop_research_execution.py', 'automation/operator_policy_succession.py',
    'lifecycle/main_stop_research_cost.py', 'lifecycle/broker_cost_allocation.py',
    'lifecycle/broker_cost_reconciliation.py', 'lifecycle/broker_cost_source.py',
    'lifecycle/research_storage.py', 'lifecycle/research_disk_budget.py',
    'lifecycle/research_input_budget.py', 'lifecycle/research_json_stream.py',
    'infrastructure/validation_digest_session.py', 'scalping/pre_submit_delay_initial_policy.py',
    'scalping/strategy_owner_components.py', 'lifecycle/retirement.py',
    'sniper_trade_review_report.py', 'trade_profit.py', 'sniper_trade_utils.py',
    '../utils/jsonl_io.py', '../trading/order/owner_custody_registry.py',
    '../trading/config/owner_retirement.py',
)


def research_code_generation():
    """Seal offline execution/cost owners in addition to the native family code."""
    engine=Path(__file__).parents[1]
    files={name:hashlib.sha256((engine/name).read_bytes()).hexdigest()
           for name in sorted(set(policy.implementation_paths())|set(RESEARCH_CODE_PATHS))}
    return dict(schema='main_stop_research_code_generation_v1',files=files,
                runtime_policy_code_sha256=post.code_sha())


def _io():
    values = dict(line.split(':', 1) for line in Path('/proc/self/io').read_text().splitlines())
    return {k:int(values[k]) for k in ('rchar', 'wchar', 'read_bytes', 'write_bytes')}


def _measurement(start, cpu, before):
    after = _io()
    return dict(wall_seconds=time.perf_counter()-start, cpu_seconds=time.process_time()-cpu,
                peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                io_delta={k:after[k]-before[k] for k in before})


def _sealed_read(path):
    path = Path(path).absolute()
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError('stop_research_input_symlink')
    value, sha = policy.bounded_object(path)
    return value, dict(path=str(Path(path).resolve()), sha256=sha)


def _bounded_write(path, value):
    if len(storage.encoded(value)) > MAX_REPORT_BYTES:
        raise ValueError('stop_research_output_partition_required')
    _atomic(path, value)


def _verify_reference(reference):
    if (not isinstance(reference, dict) or not isinstance(reference.get('path'), str)
            or byte_generation(Path(reference['path']))['sha256'] != reference.get('sha256')):
        raise ValueError('stop_research_input_reference_changed')


def _output_path(data_root, output_root, input_report, cost_data_root):
    path = Path(output_root).absolute()
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError('stop_research_output_symlink')
    path = path.resolve()
    for protected in (data_root, cost_data_root):
        if path == protected or protected in path.parents or path in protected.parents:
            raise ValueError('stop_research_output_must_not_be_live_source_or_policy')
    source = Path(input_report).resolve(strict=True)
    if path == source or path in source.parents:
        raise ValueError('stop_research_output_overlaps_input')
    return path


def _external_index_measurement(output_root, inventory):
    path=output_root/'cold_index_measurement.json'
    if not path.exists():return None
    body,reference=_sealed_read(path)
    files=[Path(post.__file__),Path(source_index.__file__),
           Path(source_index.__file__).with_name('main_stop_source_projection.py')]
    code={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    if (body.get('schema')!='main_stop_cold_index_measurement_v1' or body.get('status')!='completed'
            or body.get('receipt_sha256')!=policy.digest({k:v for k,v in body.items() if k!='receipt_sha256'})
            or body.get('source_inventory')!=inventory or body.get('source_sha256')!=policy.digest(inventory)
            or body.get('decoder_files')!=code or body.get('allowed_runtime_apply') is not False
            or body.get('policy_mutated') is not False
            or not all(policy.finite(body.get(k)) and body[k]>=0 for k in ('wall_seconds','cpu_seconds','peak_rss_kib'))
            or not isinstance(body.get('census'),dict) or not isinstance(body.get('digest_session'),dict)):
        raise ValueError('stop_research_external_index_measurement_invalid')
    return dict(reference=reference,wall_seconds=body['wall_seconds'],cpu_seconds=body['cpu_seconds'],
        peak_rss_kib=body['peak_rss_kib'],digest_session=body['digest_session'],
        census_sha256=policy.digest(body['census']),
        scope='separately_measured_native_source_index')


def _operator_snapshot(data_root, target_date):
    from .operator_policy_succession import source_snapshot
    return source_snapshot(data_root/'runtime', data_root/'threshold_cycle/operator_runtime_env_locks',
                           {'KORSTOCKSCAN_'+policy.KEYS['grace_sec']}, target_date)


def _economic_matches_position(economic, source):
    quantity=economic.get('quantity_basis') or {}
    terminal=economic.get('terminal_observation') or {}
    return bool(economic.get('schema')=='main_stop_research_cost_v1'
        and economic.get('artifact_sha256')==policy.digest({k:v for k,v in economic.items() if k!='artifact_sha256'})
        and economic.get('status')=='eligible' and economic.get('economics_scope')=='main_stop_research_only'
        and economic.get('manual_exit') is False and economic.get('runtime_effect') is False
        and economic.get('allowed_runtime_apply') is False
        and economic.get('custody_status')=='verified_registry_fill_census'
        and economic.get('fill_state') in {'fully_closed','fully_closed_multi_fill'}
        and (economic.get('main_exit_source') or {}).get('status')=='verified_native_decision_submit_chain'
        and economic.get('evidence_grade') in COST_GRADES
        and str(economic.get('record_id'))==str(source.get('record_id'))
        and quantity.get('buy_qty')==source.get('quantity')
        and quantity.get('sell_qty')==source.get('quantity') and quantity.get('residual_qty')==0
        and str(terminal.get('code'))==str(source.get('item')).split('_',1)[0])


def _paired_metrics(cell, outcomes, source, economic, admitted):
    """Aggregate only an identical candidate denominator, by cost evidence."""
    parent=outcomes['parent'];basis=source.get('buy_basis_krw')
    numerical=bool(policy.finite(basis) and basis>0 and all(
        all(policy.finite(row.get(k)) for k in ('modeled_net_krw','mae_pct','exposure_sec'))
        for row in outcomes.values()))
    all_grades=cell.setdefault('paired_metrics',{})
    for grade in COST_GRADES:
        stats=all_grades.setdefault(grade,{})
        for name,row in outcomes.items():
            if name=='parent':continue
            stat=stats.setdefault(name,dict(n=0,delta_sum_krw=0.,delta_sum_squares_krw=0.,
                delta_sum_bps=0.,mae_worse_count=0,exposure_longer_count=0))
            if not (admitted and numerical and economic.get('evidence_grade')==grade):continue
            delta=row['modeled_net_krw']-parent['modeled_net_krw']
            stat['n']+=1;stat['delta_sum_krw']+=delta;stat['delta_sum_squares_krw']+=delta*delta
            stat['delta_sum_bps']+=10000.*delta/basis
            stat['mae_worse_count']+=int(row['mae_pct']<parent['mae_pct'])
            stat['exposure_longer_count']+=int(row['exposure_sec']>parent['exposure_sec'])


def _finish_paired_metrics(cells):
    for cell in cells.values():
        for candidates_by_grade in cell.get('paired_metrics',{}).values():
            for stat in candidates_by_grade.values():
                n=stat['n'];valid=bool(n and not cell['mixed_parent_values'])
                stat.update(evidence_kind='paired_modeled_cost_adjusted_delta_not_actual_profit',
                    cost_basis='observed_decision_cost_model',
                    equal_weight_avg_paired_delta_krw=stat['delta_sum_krw']/n if valid else None,
                    mean_delta_bps=stat['delta_sum_bps']/n if valid else None,
                    equal_weight_avg_paired_delta_pct=stat['delta_sum_bps']/n/100. if valid else None,
                    standard_error_krw=(math.sqrt(max(0.,(stat['delta_sum_squares_krw']-stat['delta_sum_krw']**2/n)/(n-1))/n)
                                        if valid and n>1 else None),
                    unavailable_reason=('mixed_parent_values_not_aggregated' if cell['mixed_parent_values']
                                        else 'no_eligible_common_denominator' if not n else None))
                if not valid:
                    for key in ('delta_sum_krw','delta_sum_squares_krw','delta_sum_bps'):
                        stat[key]=None


def _snapshot_diagnostics(rows, parent, normal_decision=None):
    counts = Counter();minimum = None;first_soft = None;first_preset = None
    first_at = last_at = None; first_source = last_source = normal_source = None
    tail=dict(observations=0,first_at=None,last_at=None)
    for row in rows:
        counts['observations'] += 1
        if normal_source is not None:
            tail['observations']+=1
            if policy.finite(row.get('at')):
                tail['first_at']=row['at'] if tail['first_at'] is None else min(tail['first_at'],row['at'])
                tail['last_at']=row['at'] if tail['last_at'] is None else max(tail['last_at'],row['at'])
        if row.get('schema') != 'main_stop_source_v1':
            counts['lifecycle_receipts'] += 1
            continue
        if first_source is None:first_source=row
        last_source=row
        at, profit = row.get('at'), row.get('decision_profit_pct')
        if policy.finite(at):
            first_at = at if first_at is None else min(first_at, at)
            last_at = at if last_at is None else max(last_at, at)
        if row.get('source_sha256') != policy.digest({k:v for k,v in row.items() if k!='source_sha256'}):
            counts['invalid_source_seal'] += 1
            continue
        if (normal_decision is not None and row.get('at')==normal_decision['decision_at']
                and row.get('bid')==normal_decision['executable_bid']):
            if normal_source is not None:raise ValueError('stop_research_normal_exit_source_ambiguous')
            normal_source=row
        for name in ('partial_fill','pending_add','pending_exit','manual'):
            if row.get(name):counts[name] += 1
        for name in ('coverage_complete','automatic_management_allowed'):
            if row.get(name) is not True:counts[name+':false_or_missing'] += 1
        if policy.finite(profit):
            minimum = profit if minimum is None else min(minimum, profit)
            if profit <= parent.soft_stop_pct and first_soft is None:first_soft = at
        if row.get('role') == 'SCALP_PRESET_TP':
            try:
                decision = preset_decision(row)
                if decision and decision.disposition in {'exit_candidate','manual_handoff'}:
                    if first_preset is None:first_preset=at
                    counts['preset:'+decision.disposition] += 1
            except (ValueError, KeyError, TypeError):counts['preset_receipt_invalid_or_missing'] += 1
    return dict(counts=dict(counts),minimum_observed_decision_profit_pct=minimum,
                first_observed_soft_at=first_soft,first_observed_preset_at=first_preset,
                first_at=first_at,last_at=last_at,
                source_endpoints=dict(first=first_source,last=last_source,normal_exit=normal_source,
                    normal_decision_expected=normal_decision is not None,excluded_tail=tail),
                observation_kind='source_diagnostics_not_actual_stop_or_profit')


def _terminal_outcome(endpoints, economic):
    from src.engine.scalping.main_stop_replay import normal_exit_terminal_outcome
    try:
        if endpoints.get('normal_decision_expected') and endpoints.get('normal_exit') is None:
            raise ValueError('stop_terminal_exact_original_decision_row_missing')
        result=normal_exit_terminal_outcome(first_row=endpoints.get('first'),
            last_row=endpoints.get('normal_exit') or endpoints.get('last'),economic=economic)
        return result,None
    except ValueError as exc:
        return None,str(exc)


def _prefix_rows(rows, terminal):
    for row in rows:
        yield row
        if terminal is not None and row.get('source_sha256')==terminal['last_source_sha256']:
            return
    if terminal is not None:raise ValueError('stop_research_terminal_source_not_replayed')


def _cached_outcomes(path, identity, grid, parent, parent_verified, terminal, reason):
    if not path.exists():return None
    value,_=_sealed_read(path)
    if (value.get('sha256')!=policy.digest({k:v for k,v in value.items() if k!='sha256'})
            or value.get('identity')!=identity or set(value.get('outcomes',{}))!=set(grid)
            or value.get('parent_values')!=asdict(parent) or value.get('parent_verified') is not parent_verified
            or value.get('terminal_sha256')!=policy.digest(terminal)):
        raise ValueError('stop_research_replay_cache_invalid')
    return dict(value,terminal_reason=reason)


def _position_outcomes(position, directory, default_parent, code_sha, vote_sources, economic):
    """Price replay cache excludes late cost overlays; votes remain dependencies."""
    from src.engine.ai.holding_vote_replay_source import assemble_votes, PreparedVotes
    first = next(position.rows(), {})
    try:
        parent = policy.StopValues.parse(first['source_stop_values'])
        if (first.get('parent_values_sha256') != policy.digest(asdict(parent))
                or first.get('source_sha256') != policy.digest({k:v for k,v in first.items() if k!='source_sha256'})):
            raise ValueError('source_stop_values_unverified')
        parent_verified = True
    except (KeyError, TypeError, ValueError):
        parent, parent_verified = default_parent, False
    grid = {k:v for k,v in candidates(parent).items() if k=='parent' or k.startswith('grace_sec:')}
    source = first.get('holding_vote_source')
    reference = assemble_votes(directory['data'], directory['output'], source, vote_sources) if source else None
    logical = {k:v for k,v in reference.items() if k!='root'} if reference else None
    base_identity = policy.digest(dict(code=code_sha,position=position.key,source=position.source_sha256,
                                  grid={k:asdict(v) for k,v in grid.items()},votes=storage.logical_value(logical)))
    from src.engine.scalping.main_stop_replay import normal_exit_decision_from_economic
    try:normal_decision=normal_exit_decision_from_economic(economic)
    except ValueError:normal_decision=None
    endpoint_identity=policy.digest(dict(base_identity=base_identity,normal_decision=normal_decision))
    endpoints_path=directory['output']/'endpoint_cache'/f'{endpoint_identity}.json'
    endpoints=None
    if endpoints_path.exists():
        endpoint_cache,_=_sealed_read(endpoints_path)
        if (endpoint_cache.get('identity')!=endpoint_identity
                or endpoint_cache.get('sha256')!=policy.digest({k:v for k,v in endpoint_cache.items() if k!='sha256'})
                or not isinstance(endpoint_cache.get('endpoints'),dict)):
            raise ValueError('stop_research_endpoint_cache_invalid')
        endpoints=endpoint_cache['endpoints']
        terminal,reason=_terminal_outcome(endpoints,economic)
        identity=policy.digest(dict(base_identity=base_identity,terminal_sha256=policy.digest(terminal)))
        path=directory['output']/'replay_cache'/f'{identity}.json'
        value=_cached_outcomes(path,identity,grid,parent,parent_verified,terminal,reason)
        if value is not None:return first,value,True
    with tempfile.TemporaryDirectory(prefix='.stop-votes-',dir=directory['output']) as scratch:
        prepared = PreparedVotes(reference, scratch)
        try:
            def vote_reader(row, at):
                try:
                    snap = prepared.snapshot(row.get('holding_vote_source'),at,market=row['market'],
                        route=row['route'],epoch=row['transport_epoch'],entry_at=position.first)
                    return dict(snap,source_verified=True)
                except (ValueError,OSError,KeyError,TypeError):return dict(source_verified=False)
            with position.materialized(directory['output']) as materialized:
                diagnostics=_snapshot_diagnostics(materialized(),parent,normal_decision)
                observed=diagnostics.pop('source_endpoints')
                if endpoints is not None and endpoints!=observed:
                    raise ValueError('stop_research_endpoint_cache_changed')
                endpoints=observed
                endpoint_cache=dict(identity=endpoint_identity,endpoints=endpoints)
                endpoint_cache['sha256']=policy.digest(endpoint_cache)
                if not endpoints_path.exists():_bounded_write(endpoints_path,endpoint_cache)
                terminal,reason=_terminal_outcome(endpoints,economic)
                identity=policy.digest(dict(base_identity=base_identity,terminal_sha256=policy.digest(terminal)))
                path=directory['output']/'replay_cache'/f'{identity}.json'
                value=_cached_outcomes(path,identity,grid,parent,parent_verified,terminal,reason)
                if value is not None:return first,value,True
                def observed_prefix():return _prefix_rows(materialized(),terminal)
                value = dict(identity=identity,parent_values=asdict(parent),parent_verified=parent_verified,
                    terminal_sha256=policy.digest(terminal),terminal_reason=reason,
                    replay_window=dict(kind='verified_normal_exit_prefix' if terminal else 'complete_native_position',
                        end_at=terminal['at'] if terminal else position.last,
                        excluded_tail=endpoints['excluded_tail'] if terminal else None,
                        source_evidence_preserved=True),
                    operating_contract=holding_contracts(observed_prefix()),
                    diagnostics=diagnostics,
                    outcomes={name:replay(observed_prefix(),v,vote_reader=vote_reader,terminal_outcome=terminal)
                              for name,v in grid.items()})
        finally:prepared.close()
    value['sha256']=policy.digest(value)
    _atomic(path,value)
    return first,value,False


def _decision_measurement(value, iterations=20000):
    """Measure pure loaded decisions; explicitly not the live Main latency gate."""
    durations=[];start=time.perf_counter();cpu=time.process_time()
    samples=[dict(ts=980.+n,price=9800.) for n in range(21)]
    for n in range(iterations):
        before=time.perf_counter_ns()
        policy.soft_decision(value,profit_pct=-3.25,now=1000.+n/1000.,touch_at=999.)
        policy.protect_confirmed(value,samples,now=1000.,price_line=10000.,profit_pct=-.5)
        durations.append(time.perf_counter_ns()-before)
    durations.sort()
    return dict(iterations=iterations,wall_seconds=time.perf_counter()-start,
        cpu_seconds=time.process_time()-cpu,
        p50_ns=durations[int(iterations*.50)],p95_ns=durations[int(iterations*.95)],
        p99_ns=durations[int(iterations*.99)],max_ns=durations[-1],
        scope='loaded_pure_soft_and_protect_decisions_not_full_main_or_capture')


def run_research(*, data_root, output_root, source_date, target_date, input_report, cost_data_root=None):
    """Stream every opportunity into bounded evidence; reuse failed-run caches."""
    data_root=Path(data_root).resolve(strict=True)
    cost_root=Path(cost_data_root).resolve(strict=True) if cost_data_root is not None else data_root
    output_root=_output_path(data_root,output_root,input_report,cost_root)
    output_root.mkdir(parents=True,exist_ok=True)
    state=dict(positions_completed=0,examples=[],cells={},parent_outcomes=Counter(),
               first=None,last=None,cache_hits=0,attempt_started_at=datetime.now(KST).isoformat())
    lock_path=output_root/'.execution.lock'
    if lock_path.is_symlink():raise ValueError('stop_research_output_symlink')
    with lock_path.open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:raise ValueError('stop_research_attempt_running') from exc
        if (output_root/'report.json').exists():raise ValueError('stop_research_attempt_already_sealed')
        token=post._DEADLINE.set(time.monotonic()+MAX_SECONDS)
        try:
            with use(output_root,durable_limit=2*1024**3,temp_limit=2*1024**3), ExitStack() as resources:
                return _run_research(data_root=data_root,output_root=output_root,source_date=source_date,
                    target_date=target_date,input_report=input_report,cost_data_root=cost_root,state=state,
                    resources=resources)
        except (Exception, KeyboardInterrupt) as exc:
            failure=dict(schema='main_stop_execution_failure_v1',status='incomplete',
                source_date=source_date,target_date=target_date,reason=type(exc).__name__+':'+str(exc)[:1024],
                started_at=state['attempt_started_at'],finished_at=datetime.now(KST).isoformat(),
                positions_completed=state['positions_completed'],replay_cache_hits=state['cache_hits'],
                resume_mode='same_verified_dependencies_and_completed_replay_cache',
                allowed_runtime_apply=False,policy_mutated=False,target_policy_published=False)
            failure['receipt_sha256']=policy.digest(failure)
            # Failure evidence survives a later retry; the existing sources and
            # any completed policy/report are never rewritten by recovery.
            _bounded_write(output_root/'failures'/f"{failure['receipt_sha256']}.json",failure)
            if not (output_root/'report.json').exists():
                _bounded_write(output_root/'progress.json',failure)
            raise
        finally:post._DEADLINE.reset(token)


def _run_research(*, data_root, output_root, source_date, target_date, input_report, cost_data_root, state, resources):
    from src.engine.infrastructure.validation_digest_session import postclose_session
    from src.engine.lifecycle.main_stop_research_cost import prepare_economic_source, prepare_economic_record
    post.checkpoint()
    original,original_ref=_sealed_read(input_report)
    if (original.get('schema')!='main_stop_research_v1' or original.get('source_date')!=source_date
            or original.get('target_date')!=target_date
            or original.get('report_sha256')!=policy.digest({k:v for k,v in original.items() if k!='report_sha256'})):
        raise ValueError('stop_research_original_report_invalid')
    for name in ('parent_receipt','snapshot_receipt'):_verify_reference(original[name])
    initial_parent=original['parent_receipt'].get('effective_values')
    if initial_parent is None:
        parent_file,_=_sealed_read(original['parent_receipt']['path'])
        initial_parent=parent_file.get('values')
    parent=policy.StopValues.parse(initial_parent)
    expected=original['source_inventory']
    if (not isinstance(expected,dict) or len(expected)>4096
            or original.get('source_sha256')!=policy.digest(expected)):
        raise ValueError('stop_research_original_inventory_invalid')
    if any(output_root==Path(name).resolve() or output_root in Path(name).resolve().parents for name in expected):
        raise ValueError('stop_research_output_overlaps_input')
    code_generation=research_code_generation();code_sha=policy.digest(code_generation)
    operator_sources=_operator_snapshot(data_root,target_date)
    measured_start=time.perf_counter();measured_cpu=time.process_time();before=_io()
    stages={};vote_sources={};decode_calls=0
    def source_events(*args,**kwargs):
        nonlocal decode_calls
        decode_calls+=1
        yield from post.source_events(*args,**kwargs)
    with postclose_session(data_root,source_date) as digests:
        inventory={name:byte_generation(Path(name)) for name in expected}
        if inventory!=expected:raise ValueError('stop_research_native_source_revision_changed')
        source_sha=policy.digest(inventory)
        external_index=_external_index_measurement(output_root,inventory)
        original_stats={name:source_stat(Path(name).stat()) for name in inventory}
        input_receipt=dict(schema='main_stop_research_input_v1',
            source_date=source_date,target_date=target_date,original_report=original_ref,
            source_inventory=inventory,source_sha256=source_sha,code_sha256=code_sha,
            research_code_generation=code_generation,
            data_root=str(data_root),cost_data_root=str(cost_data_root),
            parent_values=asdict(parent),operator_sources=operator_sources,allowed_runtime_apply=False)
        input_receipt['receipt_sha256']=policy.digest(input_receipt)
        receipt_path=output_root/'input_receipt.json'
        if receipt_path.exists():
            previous,_=_sealed_read(receipt_path)
            if previous!=input_receipt:raise ValueError('stop_research_resume_dependency_changed')
        else:_bounded_write(receipt_path,input_receipt)
        start=time.perf_counter();cpu=time.process_time();io_before=_io();census=Counter()
        prepared=source_index.prepare(output_root,inventory,source_events,census)
        if external_index is not None and external_index['census_sha256']!=policy.digest(dict(census)):
            raise ValueError('stop_research_external_index_census_changed')
        stages['source_index_initial']=_measurement(start,cpu,io_before)
        stages['source_index_initial'].update(raw_decode_calls=decode_calls,
            cache_state='cache_reused' if decode_calls==0 else 'source_decoded')
        economic=resources.enter_context(prepare_economic_source(data_root,source_date,cost_data_root=cost_data_root))
        stage_start=time.perf_counter();stage_cpu=time.process_time();stage_io=_io()
        valid_cells={f'{role}|{market}' for role in policy.ROLES for market in policy.MARKETS}
        def position_rows():
            for position in source_index.positions(prepared,output_root/'position_sort',Counter(),checkpoint=post.checkpoint):
                post.checkpoint()
                original_row=next(position.rows(),{})
                try:
                    cost=prepare_economic_record({'id':original_row.get('record_id')},data_root=data_root,
                        source_date=source_date,prepared=economic,cost_data_root=cost_data_root)
                except ValueError as exc:
                    if str(exc)!='research_cost_record_identity_invalid':raise
                    cost=dict(status='source_gap',reason=str(exc),record_id=None,allowed_runtime_apply=False)
                original_row,value,cached=_position_outcomes(position,dict(data=data_root,output=output_root),parent,code_sha,vote_sources,cost)
                state['first']=position.first if state['first'] is None else min(state['first'],position.first)
                state['last']=position.last if state['last'] is None else max(state['last'],position.last)
                outcomes=value['outcomes'];common=all(v.get('status')=='modeled' for v in outcomes.values())
                economic_match=_economic_matches_position(cost,original_row)
                row=dict(position_key=position.key,record_id=original_row.get('record_id'),
                    cell=position.cell,first_at=position.first,last_at=position.last,
                    parent_values=value['parent_values'],parent_verified=value['parent_verified'],
                    operating_contract=value['operating_contract'],diagnostics=value['diagnostics'],
                    replay_window=value['replay_window'],
                    outcomes=outcomes,economic=cost,economic_position_match=economic_match,
                    terminal_source_gap=value['terminal_reason'],common_modeled=common,replay_cache_hit=cached)
                group=position.cell if position.cell in valid_cells else 'UNMAPPED'
                cell=state['cells'].setdefault(group,dict(opportunities=0,parent_outcomes=Counter(),
                    economic=Counter(),terminal_source_gaps=Counter(),common_modeled=0,eligible_paired=0,parent_values=value['parent_values'],
                    parent_verified=value['parent_verified'],mixed_parent_values=False,
                    first_at=position.first,last_at=position.last))
                cell['opportunities']+=1
                cell['parent_verified'] &= value['parent_verified']
                cell['mixed_parent_values'] |= cell['parent_values']!=value['parent_values']
                cell['first_at']=min(cell['first_at'],position.first);cell['last_at']=max(cell['last_at'],position.last)
                result=outcomes['parent'];reason=result['status']+':'+str(result['reason'])
                cell['parent_outcomes'][reason]+=1;state['parent_outcomes'][reason]+=1
                cell['economic'][cost['status']]+=1;cell['common_modeled']+=int(common)
                admitted=common and economic_match and value['parent_verified']
                cell['eligible_paired']+=int(admitted)
                _paired_metrics(cell,outcomes,original_row,cost,admitted)
                if value['terminal_reason']:cell['terminal_source_gaps'][value['terminal_reason']]+=1
                state['positions_completed']+=1;state['cache_hits']+=int(cached)
                if len(state['examples'])<MAX_EXAMPLES:
                    state['examples'].append({k:row[k] for k in ('position_key','record_id','cell','first_at','last_at','common_modeled','replay_cache_hit')} |
                        dict(parent_status=result['status'],parent_reason=result['reason'],economic_status=cost['status']))
                if state['positions_completed']==1 or state['positions_completed']%32==0:
                    _bounded_write(output_root/'progress.json',dict(status='running',
                        positions_completed=state['positions_completed'],last_position_key=position.key,
                        input_receipt_sha256=input_receipt['receipt_sha256'],policy_mutated=False))
                yield row
        evidence=storage.write_tree(output_root,position_rows())
        stages['positions_and_economic_overlay']=_measurement(stage_start,stage_cpu,stage_io)
        start=time.perf_counter();cpu=time.process_time();io_before=_io();warm_census=Counter()
        cold_calls=decode_calls
        source_index.prepare(output_root,inventory,source_events,warm_census)
        stages['source_index_warm']=_measurement(start,cpu,io_before)
        stages['source_index_warm']['raw_decode_calls']=decode_calls-cold_calls
        if warm_census!=census or decode_calls!=cold_calls:raise ValueError('stop_research_warm_census_changed')
        if any(source_stat(Path(name).stat())!=generation for name,generation in original_stats.items()):
            raise ValueError('stop_research_source_changed_during_execution')
        economic.validate_unchanged()
        for name,generation in vote_sources.items():
            if byte_generation(Path(name))!=generation:raise ValueError('stop_research_vote_source_changed')
        if _sealed_read(input_report)[1]!=original_ref:raise ValueError('stop_research_original_report_changed')
        for name in ('parent_receipt','snapshot_receipt'):_verify_reference(original[name])
        if research_code_generation()!=code_generation:raise ValueError('stop_research_code_changed_during_execution')
        if external_index is not None and _external_index_measurement(output_root,inventory)!=external_index:
            raise ValueError('stop_research_external_index_measurement_changed')
        digest_metrics=dict(digests.stats)
    post.checkpoint()
    pure=_decision_measurement(parent)
    total=_measurement(measured_start,measured_cpu,before)
    total['scope']='source_validation_index_replay_economic_overlay_and_pure_decisions_excludes_final_serialization'
    performance=dict(schema='main_stop_performance_v1',status='measured',
        scope='offline_research_and_pure_decisions',source_sha256=source_sha,code_sha256=code_sha,
        research_code_generation=code_generation,
        allowed_runtime_apply=False,unresolved_findings=['live_capture_latency_not_measured'],
        metrics=dict(total=total,stages=stages,pure_decisions=pure,digest_session=digest_metrics,
                     external_cold_index=external_index,
                     source_files=len(inventory),positions=state['positions_completed'],replay_cache_hits=state['cache_hits']))
    performance_path=output_root/f'performance_{policy.digest(performance)}.json'
    _bounded_write(performance_path,performance)
    performance_ref=dict(path=str(performance_path),sha256=hashlib.sha256(performance_path.read_bytes()).hexdigest())
    # A historical study never manufactures a prospective freeze timestamp or
    # a runtime policy. Its registration is explicit about retrospective use.
    registration=None;registration_reason='no_supported_registration_scope'
    scopes=[(name,cell) for name,cell in sorted(state['cells'].items()) if name!='UNMAPPED'
            and cell['parent_verified'] and not cell['mixed_parent_values'] and cell['last_at']-cell['first_at']>120]
    if scopes and inventory:
        from src.engine.scalping.main_stop_experiment import register_experiment,finalize_experiment
        scope,cell=max(scopes,key=lambda item:(item[1]['opportunities'],item[0]))
        selected_parent=policy.StopValues.parse(cell['parent_values'])
        first,last=cell['first_at'],cell['last_at']
        grid={k:asdict(v) for k,v in candidates(selected_parent).items() if k=='parent' or k.startswith('grace_sec:')}
        params=dict(parent_sha256=policy.digest(asdict(selected_parent)),code_sha256=code_sha,
            operator_lock_sha256=policy.digest(operator_sources),allowed_keys=['grace_sec'],max_daily_change={'grace_sec':60},
            split_at=(first+last)/2,embargo_sec=60.,min_train=2,min_holdout=2,
            minimum_paired_ev_krw=0.,max_censoring_ratio=0.,max_standard_error_krw=0.,
            candidate_grid=grid,source_start_at=first,source_end_at=last,
            hypothesis='Historical grace reachability and source eligibility; no live promotion.')
        prereg=register_experiment(output_root/'experiments',experiment_id='stop-grace-source-study',revision=1,
            cell=scope,parameters=params,mode='historical_report_only')
        registration=finalize_experiment(output_root/'experiments',prereg,source_inventory=inventory,
            performance_receipt=performance_ref,observed_start_at=first,observed_end_at=last)
        registration_reason=None
    post.checkpoint()
    census_ref=storage.write_tree(output_root,(dict(name=name,count=count) for name,count in sorted(census.items())))
    _finish_paired_metrics(state['cells'])
    report=dict(schema=SCHEMA,status='completed_report_only',started_at=state['attempt_started_at'],finished_at=datetime.now(KST).isoformat(),
        source_date=source_date,target_date=target_date,input_receipt=str(output_root/'input_receipt.json'),
        input_receipt_sha256=input_receipt['receipt_sha256'],
        original_report=original_ref,source_sha256=source_sha,code_sha256=code_sha,
        research_code_generation=code_generation,
        operator_sources=operator_sources,operator_lock_sha256=policy.digest(operator_sources),
        economic_source_reference=economic.source_reference,economic_cost_generation=economic.cost_generation,
        source_census={k:v for k,v in census.items() if ':' not in k},source_census_reference=census_ref,
        position_count=state['positions_completed'],cells=state['cells'],
        parent_outcomes=dict(state['parent_outcomes']),position_evidence=evidence,examples=state['examples'],
        performance_path=str(performance_path),performance_reference=performance_ref,
        historical_experiment=registration,historical_registration_reason=registration_reason,
        terminal_adapter_status='verified_native_normal_exit_only',
        metric_contract=dict(metric_role='source_quality_gate',decision_authority='report_only',
            window_policy='exact_native_source_historical',sample_floor='diagnostic_only_not_for_authority',
            primary_decision_metric='eligible_paired_source_coverage',
            source_quality_gate='sealed_native_sources_same_position_quote_pin_and_verified_cost_scope',
            forbidden_uses=['live_promotion','orders','actual_pnl','source_gap_as_zero_edge']),
        paired_metric_contract=dict(metric_role='primary_ev',decision_authority='report_only',
            window_policy='identical_position_candidate_intersection_split_by_cost_evidence_grade',
            sample_floor='historical_exploration_no_selection_authority',
            primary_decision_metric='equal_weight_avg_paired_delta_krw',
            source_quality_gate='all_candidates_modeled_matched_native_completion_and_cost_same_parent',
            forbidden_uses=['live_promotion','orders','actual_pnl','mixing_allocated_and_exact_cost_grades']),
        selected_policy=None,policy_mutated=False,
        actual_order_submitted=False,actual_profit_verified=False,allowed_runtime_apply=False)
    report['report_sha256']=policy.digest(report)
    if _sealed_read(input_report)[1]!=original_ref:raise ValueError('stop_research_original_report_changed')
    if research_code_generation()!=code_generation:raise ValueError('stop_research_code_changed_during_execution')
    if _operator_snapshot(data_root,target_date)!=operator_sources:
        raise ValueError('stop_research_operator_source_changed')
    if any(source_stat(Path(name).stat())!=generation for name,generation in original_stats.items()):
        raise ValueError('stop_research_source_changed_during_execution')
    if _sealed_read(receipt_path)[0]!=input_receipt:raise ValueError('stop_research_input_receipt_changed')
    _verify_reference(performance_ref)
    if external_index is not None and _external_index_measurement(output_root,inventory)!=external_index:
        raise ValueError('stop_research_external_index_measurement_changed')
    economic.validate_unchanged()
    _bounded_write(output_root/'report.json',report)
    _bounded_write(output_root/'progress.json',dict(status='completed_report_only',positions_completed=state['positions_completed'],
        report_sha256=report['report_sha256'],policy_mutated=False))
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',required=True);parser.add_argument('--output-root',required=True)
    parser.add_argument('--date',required=True);parser.add_argument('--target',required=True)
    parser.add_argument('--input-report',required=True)
    parser.add_argument('--cost-data-root')
    args=parser.parse_args()
    result=run_research(data_root=args.data_root,output_root=args.output_root,source_date=args.date,
                        target_date=args.target,input_report=args.input_report,cost_data_root=args.cost_data_root)
    print(json.dumps({k:result[k] for k in ('status','source_date','position_count','parent_outcomes','selected_policy')},ensure_ascii=False))


if __name__=='__main__':main()
