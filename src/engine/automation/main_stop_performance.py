"""Isolated, measured Main stop capture/reader performance evidence.

This offline producer owns its temporary sink and invokes native quote context,
pin lookup, decision receipt, bounded queue, serialization and source reader.
It cannot certify the unexecuted Main wake/claim/dispatch or concurrent-load
phases. It never creates a runtime-and-postclose PASS from a microbenchmark.
"""
from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import resource
import tempfile
import time

from src.engine.scalping import main_stop_policy as policy

SCHEMA = 'main_stop_performance_v2'
SCOPE = 'isolated_native_capture_and_reader'
COVERED = ('pin_lookup', 'native_quote_context', 'native_capture',
           'native_stage_receipts', 'normal_decision_receipt', 'bounded_queue_admission',
           'native_source_serialization', 'postclose_source_reader')
EXCLUDED = ('main_ws_wake_and_scheduling', 'main_holding_and_fast_dispatch',
            'claim_and_exit_registration', 'main_lock_wait_and_hold',
            'concurrent_main_and_postclose_load', 'postclose_selector_publish_handoff')
MAX_SCENARIOS = 64
MAX_REPEATS = 100
MAX_BYTES = 8 * 1024 * 1024


def _summary(values):
    ordered=sorted(values)
    if not ordered:return dict(n=0,p50_ns=None,p95_ns=None,p99_ns=None,max_ns=None)
    return dict(n=len(ordered), **{f'p{p}_ns':ordered[max(0,math.ceil(len(ordered)*p/100)-1)]
                for p in (50,95,99)},max_ns=ordered[-1])


def _frozen(value):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    if len(raw)>MAX_BYTES:raise ValueError('stop_performance_input_unbounded')
    return json.loads(raw)


@contextmanager
def _isolated_native_capture(root):
    """Only local adapter routing changes; the native capture/queue stay real.

    Call in an otherwise idle offline process. No handler/Main startup or
    broker/provider method is invoked. Restore every module-global binding.
    """
    from src.engine import sniper_state_handlers as handlers
    from src.utils import pipeline_event_logger as logger
    old=(handlers.DATA_DIR,logger.emit_pipeline_event,policy._SOURCE_SINK)
    path=root/'captured.jsonl'
    calls=Counter()
    def append(pipeline,name,code,stage,*,record_id=None,fields=None,observed_at_epoch=None):
        # Filesystem adapter only: _append_source still seals the native bytes,
        # and the production bounded queue freezes/admit/drains its envelope.
        event=dict(pipeline=pipeline,name=name,code=code,stage=stage,record_id=record_id,
                   fields=fields,observed_at_epoch=observed_at_epoch)
        raw=json.dumps(event,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n'
        with path.open('a') as handle:handle.write(raw)
        calls['native_serialized_events']+=1
        calls['serialized_bytes']+=len(raw.encode())
        return dict(structured_append_succeeded=True)
    handlers.DATA_DIR=root
    logger.emit_pipeline_event=append
    try:
        with ThreadPoolExecutor(max_workers=1,thread_name_prefix='stop-offline-capture') as executor:
            queue=logger.BoundedObservationQueue(executor)
            policy.configure_source_sink(queue.submit)
            try:yield handlers,queue,path,calls
            finally:
                if not queue.close(timeout=10):raise ValueError('stop_performance_queue_drain_incomplete')
    finally:
        handlers.DATA_DIR,logger.emit_pipeline_event=old[:2]
        policy.configure_source_sink(old[2])


def _run_arm(root, scenarios, values):
    from src.engine.scalping.position_peak_ledger import position_cycle_id
    from .main_stop_postclose import source_events
    from .main_stop_source_index import extract
    root.mkdir(parents=True,exist_ok=True)
    timings=[];receipts=[];contexts=[];calls=Counter();decisions=[];quantity=Counter()
    started=time.perf_counter_ns();cpu=time.process_time_ns()
    with _isolated_native_capture(root) as (h,queue,path,sink_calls):
        for scenario in scenarios:
            stock=deepcopy(scenario['stock']);quote_inputs=deepcopy(scenario['quote_inputs'])
            at=quote_inputs['now_ts'];code=stock['code'];key=position_cycle_id(stock)
            # A private, already-loaded pin is the hot-path baseline. Native
            # preload/bootstrap/durable first-pin are explicitly excluded.
            pinned=policy.pin(position_key=key,role=scenario['role'],market=quote_inputs['market_type'],
                              target=scenario['target_date'],baseline=values)
            stock.update(main_stop_policy_pin=pinned,_main_stop_typed_values=values,
                         _main_stop_position_key=key)
            before=time.perf_counter_ns()
            policy.pin_values(pinned,key);calls['pin_lookup']+=1
            context=h._main_stop_quote_context(stock,code,**quote_inputs)
            calls['native_quote_context']+=1
            stock['_main_stop_current_quote_context']=context
            contexts.append(dict(complete=context['complete'],bid=context['bid'],at=context['at']))
            accepted=h._capture_main_stop_observation(stock,code,context)
            calls['native_capture']+=1
            if not accepted:raise ValueError('stop_performance_native_capture_rejected:'+str(stock.get('main_stop_source_gap')))
            predecessor=None
            for evaluator,stage in scenario.get('evaluation_sequence',[['normal','common_soft']]):
                stock['_main_stop_current_quote_context']=dict(context,evaluator=evaluator)
                if stage=='preset_safety':
                    stage_receipt=h._observe_main_stop_preset_evaluation(stock,code,at=at,evaluator=evaluator,
                        decision_price=context['bid'],decision_price_basis='executable_bid',
                        profit_rate=context['decision_profit_pct'],hard_pct=-5.,emergency_pct=-6.,
                        grace_sec=0,held_sec=60.)
                    if evaluator=='normal':predecessor=stage_receipt
                elif stage=='common_soft':
                    stage_receipt=h._observe_main_stop_evaluation(stock,code,at=at,evaluator=evaluator,
                        stage=stage,decision_price=context['bid'],decision_price_basis='executable_bid',
                        decision_profit_pct=context['decision_profit_pct'],preset_predecessor=predecessor,
                        decision_inputs=dict(grace_enabled=True,after_add=False,handoff_enabled=False,
                                             protect_enabled=True,vote_max_worsen_pct=.8))
                else:raise ValueError('stop_performance_stage_invalid')
                if stage_receipt is None:
                    raise ValueError('stop_performance_native_stage_rejected:'+str(stock.get('main_stop_evaluation_source_gap')))
                calls['native_stage_receipts']+=1
                calls['stage:'+evaluator+':'+stage]+=1
                quantity[str((stage_receipt.get('quantity_source') or {}).get('status'))]+=1
                receipts.append(stage_receipt['source_sha256'])
            # The native pure decision result is retained separately from the
            # source/capture cost. Neither result dispatches an order.
            decision=policy.soft_decision(values,profit_pct=context['decision_profit_pct'],now=at)
            decisions.append(asdict(decision))
            receipt=policy.normal_exit_decision_source(stock,at=at,
                price=context['bid'],executable_bid=context['bid'],mark_price=context['bid'],
                exit_rule='scalp_trailing_take_profit')
            receipts.append(receipt['source_sha256']);calls['normal_decision_receipt']+=1
            timings.append(time.perf_counter_ns()-before)
        if not queue.close(timeout=10):raise ValueError('stop_performance_queue_drain_incomplete')
        queue_stats=dict(queue._stats)
        calls.update(sink_calls)
    census=Counter();decoded=0;read_started=time.perf_counter_ns()
    if path.exists():
        for event in source_events(path,census):
            observed=extract(event)
            if (not isinstance(observed,dict) or observed.get('source_sha256')!=policy.digest(
                    {k:v for k,v in observed.items() if k!='source_sha256'})):
                raise ValueError('stop_performance_capture_readback_invalid')
            decoded+=1
    reader_ns=time.perf_counter_ns()-read_started
    expected=len(scenarios)+calls['native_stage_receipts']
    if decoded!=expected or queue_stats['append_confirmed']!=expected:
        raise ValueError('stop_performance_capture_reader_population_mismatch')
    return dict(samples_ns=timings,capture=_summary(timings),reader_ns=reader_ns,
        wall_ns=time.perf_counter_ns()-started,cpu_ns=time.process_time_ns()-cpu,
        calls=dict(calls),queue=queue_stats,decoded_rows=decoded,census=dict(census),quantity_census=dict(quantity),
        decision_sha256=policy.digest(decisions),receipt_sha256=policy.digest(receipts),
        context_sha256=policy.digest(contexts),capture_sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def measure_capture_pair(output, *, scenarios, baseline, candidate, source_sha256, repeats=3):
    """Alternate equal frozen workloads; create measured, bounded evidence.

    Callers provide native quote-context inputs, not a timing/PASS dictionary.
    The immutable receipt explicitly excludes full Main and normal postclose
    publication, so successful capture measurements cannot promote a policy.
    """
    from src.engine.scalping.main_stop_experiment import _write_immutable
    if policy._LOADED or policy._SOURCE_SINK is not None:
        raise ValueError('stop_performance_requires_idle_offline_process')
    if type(repeats) is not int or not 3<=repeats<=MAX_REPEATS:
        raise ValueError('stop_performance_repeats_invalid')
    scenarios=_frozen(scenarios)
    if not isinstance(scenarios,list) or not 1<=len(scenarios)<=MAX_SCENARIOS:
        raise ValueError('stop_performance_scenarios_invalid')
    if not isinstance(source_sha256,str) or len(source_sha256)!=64:
        raise ValueError('stop_performance_source_sha_invalid')
    baseline=policy.StopValues.parse(asdict(baseline));candidate=policy.StopValues.parse(asdict(candidate))
    output=Path(output).absolute()
    from src.utils.constants import DATA_DIR
    if output.is_relative_to(Path(DATA_DIR).resolve()) or output.is_symlink():
        raise ValueError('stop_performance_live_output_forbidden')
    code=policy.implementation_sha();started=time.time()
    arms={'baseline':[],'candidate':[]};order=[]
    with tempfile.TemporaryDirectory(prefix='stop-capture-pair-') as scratch:
        for repeat in range(repeats):
            for name in (('baseline','candidate') if repeat%2==0 else ('candidate','baseline')):
                order.append(name)
                arms[name].append(_run_arm(Path(scratch)/f'{repeat}-{name}',scenarios,
                                          baseline if name=='baseline' else candidate))
    if policy.implementation_sha()!=code:raise ValueError('stop_performance_code_generation_changed')
    body=dict(schema=SCHEMA,status='measured',scope=SCOPE,code_sha256=code,source_sha256=source_sha256,
        source_sha256_role='expected_inventory_context_not_benchmark_input_provenance',
        input_sha256=policy.digest(scenarios),input_scenarios=scenarios,input_origin='frozen_offline_fixture',
        started_at=started,completed_at=time.time(),repeats=repeats,execution_order=order,
        baseline_values=asdict(baseline),candidate_values=asdict(candidate),arms=arms,
        coverage_scope=list(COVERED),excluded_phases=list(EXCLUDED)+['preload_and_durable_first_pin','production_pipeline_filesystem_adapter'],
        full_runtime_gate_status='blocked',unresolved_findings=['unmeasured:'+phase for phase in EXCLUDED],
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        allowed_runtime_apply=False,actual_order_submitted=False,actual_provider_called=False)
    body['performance_sha256']=policy.digest(body)
    validate_receipt(body,code_sha=code,source_sha=source_sha256,require_full=False)
    ref=_write_immutable(output,body,'performance_sha256')
    return body,{k:ref[k] for k in ('path','sha256')}


def validate_receipt(body, *, code_sha, source_sha, require_full):
    """Recompute the producer's measured population and coverage conclusions."""
    if (body.get('schema')!=SCHEMA or body.get('scope')!=SCOPE or body.get('status')!='measured'
            or body.get('code_sha256')!=code_sha or body.get('source_sha256')!=source_sha
            or body.get('source_sha256_role')!='expected_inventory_context_not_benchmark_input_provenance'
            or body.get('input_origin')!='frozen_offline_fixture'
            or body.get('performance_sha256')!=policy.digest({k:v for k,v in body.items() if k!='performance_sha256'})
            or body.get('allowed_runtime_apply') is not False or body.get('actual_order_submitted') is not False
            or body.get('actual_provider_called') is not False or body.get('coverage_scope')!=list(COVERED)
            or body.get('full_runtime_gate_status')!='blocked'
            or body.get('unresolved_findings')!=['unmeasured:'+phase for phase in EXCLUDED]
            or body.get('excluded_phases')!=list(EXCLUDED)+['preload_and_durable_first_pin','production_pipeline_filesystem_adapter']
            or body.get('input_sha256')!=policy.digest(body.get('input_scenarios'))):
        raise ValueError('stop_performance_producer_receipt_invalid')
    n=len(body['input_scenarios']);repeat=body.get('repeats')
    if type(repeat) is not int or not 3<=repeat<=MAX_REPEATS or not 1<=n<=MAX_SCENARIOS:
        raise ValueError('stop_performance_population_invalid')
    stages=sum(len(s.get('evaluation_sequence',[['normal','common_soft']])) for s in body['input_scenarios'])
    stage_calls=Counter('stage:'+evaluator+':'+stage for scenario in body['input_scenarios']
        for evaluator,stage in scenario.get('evaluation_sequence',[['normal','common_soft']]))
    expected=n+stages;contexts=[]
    for name in ('baseline','candidate'):
        runs=body.get('arms',{}).get(name,[])
        if len(runs)!=repeat:raise ValueError('stop_performance_population_invalid')
        for run in runs:
            samples=run.get('samples_ns',[])
            if (len(samples)!=n or any(type(v) is not int or v<=0 for v in samples)
                    or run.get('capture')!=_summary(samples) or run.get('decoded_rows')!=expected
                    or any(run.get('calls',{}).get(key)!=n for key in ('pin_lookup','native_quote_context',
                        'native_capture','normal_decision_receipt'))
                    or run.get('calls',{}).get('native_serialized_events')!=expected
                    or run.get('calls',{}).get('native_stage_receipts')!=stages
                    or run.get('queue',{}).get('append_confirmed')!=expected
                    or run['queue'].get('queued')!=expected or run['queue'].get('completed')!=expected
                    or any(run['queue'].get(key)!=0 for key in ('failed','unavailable','append_failed',
                        'append_unobservable','completed_without_append_receipt','intentionally_not_written'))
                    or any(run['calls'].get(key)!=count for key,count in stage_calls.items())
                    or any(type(value) is not int or value<0 for value in run.get('quantity_census',{}).values())
                    or sum(run.get('quantity_census',{}).values())!=stages):
                raise ValueError('stop_performance_population_invalid')
            contexts.append(run.get('context_sha256'))
    if len(set(contexts))!=1:raise ValueError('stop_performance_paired_input_changed')
    if require_full:
        raise ValueError('stop_performance_full_runtime_unmeasured:'+','.join(EXCLUDED))
    return body


def main():
    """Dedicated offline CLI. Requests contain inputs, never timing or PASS."""
    import argparse
    import sys
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    request,_=policy.bounded_object(args.request,MAX_BYTES)
    if set(request)!={'scenarios','baseline','candidate','source_sha256','repeats'}:
        raise ValueError('stop_performance_request_invalid')
    # A dedicated child process is the reproducible isolation boundary. Audit
    # denial is installed before any native handler is imported or called.
    def deny_external(event,args):
        if event in {'socket.connect','socket.connect_ex','socket.bind','socket.sendto',
                     'subprocess.Popen','os.system','os.exec','os.posix_spawn'}:
            raise RuntimeError('stop_performance_external_effect_forbidden')
    sys.addaudithook(deny_external)
    body,reference=measure_capture_pair(args.output,scenarios=request['scenarios'],
        baseline=policy.StopValues.parse(request['baseline']),candidate=policy.StopValues.parse(request['candidate']),
        source_sha256=request['source_sha256'],repeats=request['repeats'])
    print(json.dumps(dict(reference=reference,status=body['status'],scope=body['scope'],
                          full_runtime_gate_status=body['full_runtime_gate_status'])))
    return 0


if __name__=='__main__':raise SystemExit(main())
