"""Continuous reversal postclose producer and durable uncapped actual AI replay.

Owns normalized all-turn population and cumulative raw win-fraction selection.
No broker, provider routing changes, trade execution or legacy trace selection.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import fcntl
import gzip
import hashlib
import json
import os
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.scalping import continuous_reversal as kernel
from src.engine.scalping.reversal_auxiliary_contract import (
    ARMS, TIE_ORDER, PRODUCTION_VERSION, production_request, validate_response,
)

KST = ZoneInfo('Asia/Seoul')
SCHEMA = 'continuous_reversal_research_v1'
AUTH = dict(runtime_effect=False, allowed_runtime_apply=False,
            actual_order_submitted=False, broker_order_forbidden=True)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def file_hash(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def write(path, value):
    from src.engine.scalping.mechanistic_entry_runtime_policy import _atomic_write_json
    _atomic_write_json(Path(path), value)


def seal(value):
    value = {k: v for k, v in value.items() if k != 'artifact_content_sha256'}
    value['artifact_content_sha256'] = digest(value)
    return value


def append(path, value):
    with Path(path).open('a') as handle:
        handle.write(json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(',', ':'))+'\n')
        handle.flush()
        os.fsync(handle.fileno())


def directory(data_root, day):
    return Path(data_root)/'report'/'continuous_reversal'/day


def result_paths(data_root,day,name='provider-results.jsonl'):
    root=Path(data_root)/'report'/'continuous_reversal'
    return [p for p in sorted(root.glob('????-??-??/'+name)) if '2026-06-05'<=p.parent.name<=day]


def completed_bars(data_root,day,*,snapshot_sink=None):
    """Same-item cached completed bars only; unresolved rows stay excluded."""
    sources=defaultdict(dict);native=set();receipts=[]
    paths=[Path(data_root)/'report'/'machine_completed_price_source'/f'machine_completed_price_source_{day}.json']
    paths+=sorted((Path(data_root)/'runtime'/'shared_ws_completed_bars').glob('*/*/*.json'))
    for path in paths:
        if not path.is_file():continue
        raw_bytes=path.read_bytes()
        value=json.loads(raw_bytes)
        if value.get('source_date',value.get('trade_date'))!=day:continue
        broker=path.name.startswith('machine_completed_price_source_')
        if broker and value.get('artifact_content_sha256')!=digest({k:v for k,v in value.items() if k!='artifact_content_sha256'}):
            continue
        receipt_path=snapshot_sink(path,raw_bytes) if snapshot_sink else path
        receipts.append(dict(path=str(Path(receipt_path).resolve()),sha256=hashlib.sha256(raw_bytes).hexdigest()))
        for bar in value.get('prices',[]) if broker else value.get('bars',[]):
            if broker:
                if bar.get('completed_bar_only') is not True or bar.get('source_quality')!='pass_completed_ka10080_bar':continue
                item=bar.get('source_request_code');stamp=datetime.fromisoformat(bar['timestamp'])
                if stamp.tzinfo is None:continue
                t=stamp.timestamp()
            else:
                if bar.get('status')!='complete' or bar.get('issues') or bar.get('source_item')!=value.get('source_item'):continue
                item=value.get('source_item');t=bar.get('minute_epoch')
            prices=[bar.get(k) for k in ['open','high','low','close']]
            if not item or any(type(p) not in {int,float} or not __import__('math').isfinite(p) or p<=0 for p in prices):continue
            if not bar['low']<=min(bar['open'],bar['close'])<=max(bar['open'],bar['close'])<=bar['high']:continue
            if type(t) not in {int,float} or datetime.fromtimestamp(t,KST).date().isoformat()!=day:continue
            key=(day,item)
            if not broker and (key,t) in native:continue
            record=dict(t=t,h=bar['high'],l=bar['low'])
            old=sources[key].get(t)
            if old is not None and old!=record:record['invalid']=True
            sources[key][t]=record
            if broker:native.add((key,t))
    return {key:kernel.Bars(list(rows.values())) for key,rows in sources.items()},receipts


def ensure_population(data_root,day):
    out=directory(data_root,day);path=out/'source.json'
    if path.is_file():return json.loads(path.read_text())
    from src.engine.scalping.continuous_reversal_source import freeze_normalized_sources
    out.mkdir(parents=True,exist_ok=True)
    previous=[p for p in sorted(out.parent.glob('????-??-??/source.json')) if '2026-06-05'<=p.parent.name<day]
    parent=json.loads(previous[-1].read_text()) if previous else None
    if parent and parent['artifact_content_sha256']!=digest({k:v for k,v in parent.items() if k!='artifact_content_sha256'}):
        raise ValueError('cumulative_reversal_parent_invalid')
    normalized=freeze_normalized_sources(data_root,day,out/'normalized')
    events=[];selected={};bars,bar_receipts=completed_bars(data_root,day)
    for source in normalized:
        raw=json.loads(gzip.decompress(Path(source['path']).read_bytes()))
        output=out/f"events-{source['venue']}-{source['session']}.jsonl.gz"
        count=0
        with gzip.open(output,'wt') as handle:
            for symbol,rows in sorted(raw['symbols'].items()):
                turns,coverage=kernel.analyze_symbol(rows,day,source['venue'],source['session'],symbol)
                market=kernel.market_bucket(source['session']);key='|'.join((day,symbol,market))
                rank=(coverage['valid_price_rows'],{'SOR':2,'NXT':1,'KRX':0}[source['venue']])
                if key not in selected or tuple(selected[key]['rank'])<rank:
                    selected[key]=dict(rank=rank,venue=source['venue'],session=source['session'])
                for event in turns:
                    supplement=bars.get((day,event['source_item']))
                    if event['outcome']['status']=='UNRESOLVED' and supplement:
                        label=supplement.label(event['epoch'],event['entry_ask'],1800)
                        if label['status']!='UNRESOLVED':
                            event['raw_outcome']=event['outcome']
                            event['outcome']={**label,'source':'same_item_completed_bar_backfill'}
                    if event['outcome']['status']=='FAIL_TIMEOUT':
                        if supplement and (event.get('late_outcome') or {}).get('status') == 'UNRESOLVED':
                            event['late_outcome']=supplement.label(event['epoch'],event['entry_ask'],3600)
                    handle.write(json.dumps(event,allow_nan=False,separators=(',',':'))+'\n');count+=1
        events.append(dict(day=day,venue=source['venue'],session=source['session'],path=str(output.resolve()),sha256=file_hash(output),events=count))
    manifest=seal(dict(schema=SCHEMA,source_date=day,generated_at=datetime.now(KST).isoformat(),
        normalized_sources=dict(partitions=(parent or {}).get('normalized_sources',{}).get('partitions',[])+normalized),
        reviewed_events=(parent or {}).get('reviewed_events',[])+events,
        selected_routes={**(parent or {}).get('selected_routes',{}),**selected},
        completed_bar_receipts=bar_receipts,parent_manifest_sha256=(parent or {}).get('artifact_content_sha256'),
        code_sha256=file_hash(kernel.__file__),machine_decisions_used=False,new_raw_partition_count=len(normalized),**AUTH))
    write(path,manifest)
    return manifest


def prepare_auxiliary_points(data_root,day):
    out=directory(data_root,day)
    if (out/'provider-inputs.json').is_file() and (out/'evaluation-labels-private.json').is_file():return
    previous=[p for p in sorted(out.parent.glob('????-??-??/provider-inputs.json')) if p.parent.name<day]
    inputs=json.loads(previous[-1].read_text()) if previous else []
    labels=json.loads(previous[-1].with_name('evaluation-labels-private.json').read_text()) if previous else []
    source=json.loads((out/'source.json').read_text());machine=json.loads((out/'machine.json').read_text())
    rules={c['key']:c['payload']['rule'] for c in machine['cells']};pools=defaultdict(list)
    for record in source['reviewed_events']:
        if record['day']!=day:continue
        with gzip.open(record['path'],'rt') as handle:
            for line in handle:
                event=json.loads(line);route=source['selected_routes']['|'.join((day,event['symbol'],event['market']))]
                if (event['venue'],event['session'])!=(route['venue'],route['session']) or event['outcome']['status']=='UNRESOLVED':continue
                key=kernel.cell_key(event['symbol'],event['market'],event['confirmation_price'])
                if kernel.conditions(event)[rules[key]]:pools[key].append(event)
    chosen=[e for pool in pools.values() for e in sorted(pool,key=lambda e:digest(e['event_id']))[:24]]
    partitions={(p['venue'],p['session']):p for p in source['normalized_sources']['partitions'] if p['day']==day}
    for route in sorted({(e['venue'],e['session']) for e in chosen}):
        raw=json.loads(gzip.decompress(Path(partitions[route]['path']).read_bytes()))['symbols'];features={}
        for event in [e for e in chosen if (e['venue'],e['session'])==route]:
            symbol=event['symbol'];rows=raw[symbol]
            if symbol not in features:features[symbol]=kernel.build_features(rows)
            i=event['entry_index']
            values={k:float(v[i]) if __import__('math').isfinite(v[i]) else None for k,v in features[symbol].items()}
            values.update({k:event[k] for k in kernel.INPUT_FEATURES[4:]})
            inputs.append(dict(event_id=event['event_id'],input=kernel.make_input(event,rows,values)))
            labels.append({k:event[k] for k in ['event_id','day','symbol','group','market','price_band','outcome']})
    write(out/'provider-inputs.json',inputs);write(out/'evaluation-labels-private.json',labels)
    write(out/'sample-selection.json',seal(dict(schema=SCHEMA,source_date=day,new_points=len(chosen),
        selection='date and cell then stable event hash, up to 24; outcome value never ranks',
        machine_report_sha256=machine['artifact_content_sha256'],**AUTH)))


def prepare_research(data_root, day, seed):
    """One-time explicit migration of frozen reviewed source, never decision rows."""
    out = directory(data_root, day)
    out.mkdir(parents=True, exist_ok=True)
    seed = Path(seed)
    source = json.loads((seed/'source-manifest.json').read_text())
    events = json.loads((seed/'reviewed-events-manifest.json').read_text())
    selected = json.loads((seed/'selected-sources.json').read_text())
    for record in source['partitions'] + events:
        if record['day'] > day or record['day'] < '2026-06-05' or file_hash(record['path']) != record['sha256']:
            raise ValueError('frozen_reversal_source_invalid')
        original=Path(record['path'])
        owned=out/'frozen-research-source'/original.name
        owned.parent.mkdir(parents=True,exist_ok=True)
        if not owned.exists():
            shutil.copy2(original,owned)
        if file_hash(owned)!=record['sha256']:
            raise ValueError('owned_reversal_source_hash_invalid')
        record['research_origin_path']=str(original)
        record['path']=str(owned.resolve())
    manifest = seal(dict(schema=SCHEMA, source_date=day, generated_at=datetime.now(KST).isoformat(),
                         normalized_sources=source, reviewed_events=events,
                         selected_routes=selected, code_sha256=file_hash(kernel.__file__),
                         machine_decisions_used=False, **AUTH))
    write(out/'source.json', manifest)
    auxiliary=seed.parent/'auxiliary-reversal-phase-repair-20261006'
    old=seed.parent/'auxiliary-reversal-zero-base-20261006'
    if auxiliary.is_dir():
        write(out/'provider-inputs.json',json.loads((auxiliary/'combined-inputs.json').read_text()))
        labels=json.loads((old/'evaluation-labels-private.json').read_text())+json.loads((auxiliary/'expansion-labels-private.json').read_text())
        write(out/'evaluation-labels-private.json',labels)
    return manifest


def machine_report(data_root, day, publication):
    from src.engine.scalping import continuous_reversal_registered_postclose as registered
    current=registered.active(data_root,publication)
    if current:return registered.machine_report(data_root,day,publication,current)
    from src.engine.scalping import continuous_reversal_branch_postclose as branch
    parent=branch.active_v2(data_root,publication)
    if parent:return branch.machine_report(data_root,day,publication,parent)
    out = directory(data_root, day)
    source = ensure_population(data_root,day)
    if source['artifact_content_sha256'] != digest({k:v for k,v in source.items() if k != 'artifact_content_sha256'}):
        raise ValueError('reversal_manifest_changed')
    agg = defaultdict(Counter)
    total = 0
    for record in source['reviewed_events']:
        if file_hash(record['path']) != record['sha256']:
            raise ValueError('reversal_events_changed')
        with gzip.open(record['path'], 'rt') as handle:
            for line in handle:
                event = json.loads(line)
                chosen = source['selected_routes']['|'.join((event['day'], event['symbol'], event['market']))]
                if (event['venue'], event['session']) != (chosen['venue'], chosen['session']):
                    continue
                total += 1
                key = kernel.cell_key(event['symbol'], event['market'], event['confirmation_price'])
                for rule, matched in kernel.conditions(event).items():
                    if matched:
                        agg[key,rule][event['outcome']['status']] += 1
    cells = []
    for key in expected_cells():
        candidates = {}
        for rule in kernel.RULES:
            c = agg[key,rule]
            n = c['WIN']+c['FAIL_STOP']+c['FAIL_TIMEOUT']
            candidates[rule] = dict(wins=c['WIN'], resolved=n, excluded=c['UNRESOLVED'], counts=dict(c))
        rules = [rule for rule in kernel.RULES if candidates[rule]['resolved']]
        selected = max(rules, key=lambda rule: (Fraction(candidates[rule]['wins'],candidates[rule]['resolved']),
                      -condition_count(rule), -kernel.RULES.index(rule))) if rules else None
        cells.append(dict(key=key, payload=dict(rule=selected) if selected else None,
                          local_metrics=candidates.get(selected), candidates=candidates, inherited_from=None))
    inherit(cells, previous_cells(data_root, day, 'machine'))
    report = seal(dict(schema=SCHEMA, report_scope='main_mechanistic_entry', source_date=day,
        target_date=day, publication_date=publication, generated_at=datetime.now(KST).isoformat(),
        status='completed', selection_basis='cumulative_raw_win_fraction', population='all_continuous_price_turns',
        input_turn_count=total, source_manifest_sha256=source['artifact_content_sha256'],
        kernel_sha256=file_hash(kernel.__file__), cells=cells,
        label_contract=dict(target_net_pct=.4, stop_net_pct=-3., cost_rate=.0023, horizon_seconds=1800), **AUTH))
    write(out/'machine.json',report)
    standard=Path(data_root)/'report'/'ai_decision_action_outcome_calibration'
    write(standard/f'winrate_policy_{day}.json',report)
    write(standard/f'winrate_policy_terminal_{day}.json',seal(dict(schema=SCHEMA,source_date=day,target_date=day,
        status='completed',selection_basis=report['selection_basis'],report_sha256=report['artifact_content_sha256'],
        disposition='continuous_reversal_selected',policy_sha256=digest(cells),
        staged=dict(status='machine_component_prepared'),**AUTH)))
    return report


def condition_count(rule):
    return 2 if rule in {'DROP_0_4_REBOUND_LE_0_3','DD5_0_8_REBOUND_LE_0_3','DROP_0_4_VOL_UP','DD5_0_8_VOL_UP'} else 0 if rule=='ALL' else 1


def expected_cells():
    return ['|'.join((g,m,b)) for g,bands in [('samsung',['ALL']),('other',['LT_20000','20000_TO_100000','GE_100000'])]
            for m in ['PRE','REGULAR','AFTER'] for b in bands]


def previous_cells(data_root, day, name):
    paths = sorted(directory(data_root,day).parent.glob('????-??-??/'+name+'.json'))
    for path in reversed(paths):
        if not '2026-06-05' <= path.parent.name < day:
            continue
        report = json.loads(path.read_text())
        if report.get('source_date') != path.parent.name or report.get('artifact_content_sha256') != digest(
                {k:v for k,v in report.items() if k != 'artifact_content_sha256'}):
            raise ValueError('previous_reversal_report_invalid')
        return {c['key']:{**c,'previous_report_sha256':report['artifact_content_sha256'],
                         'previous_report_path':str(path.resolve()),'previous_source_date':report['source_date']}
                for c in report['cells']}
    return {}


def inherit(cells, previous=None):
    index = {c['key']:c for c in cells}
    previous = previous or {}
    # Resolve REGULAR parents first; no undefined n=0 win rate is fabricated.
    for key in sorted(expected_cells(),key=lambda k: '|REGULAR|' not in k):
        cell = index[key]
        if cell['payload'] is not None:
            cell['payload_sha256'] = digest(cell['payload'])
            continue
        g,m,b = key.split('|')
        parent_key = '|'.join((g,'REGULAR',b))
        parent = index[parent_key] if m != 'REGULAR' else None
        if parent is not None and parent['payload'] is not None:
            cell.update(payload=parent['payload'].copy(), inherited_from=parent_key,
                        parent_payload_sha256=digest(parent['payload']))
        elif previous.get(parent_key,{}).get('payload'):
            cell.update(payload=previous[parent_key]['payload'].copy(), inherited_from='previous:'+parent_key,
                        parent_payload_sha256=digest(previous[parent_key]['payload']))
            for field in ('previous_report_sha256','previous_report_path','previous_source_date'):
                if field in previous[parent_key]:cell[field]=previous[parent_key][field]
        else:
            raise ValueError('verified_regular_parent_missing:'+parent_key)
        cell['local_metrics'] = None
        cell['payload_sha256'] = digest(cell['payload'])


def auxiliary_report(data_root,day,publication,*,publish_policy=True):
    from src.engine.scalping import continuous_reversal_registered_postclose as registered
    current=registered.active(data_root,publication)
    if current:return registered.auxiliary_report(data_root,day,publication,current,publish_policy=publish_policy)
    from src.engine.scalping import continuous_reversal_branch_postclose as branch
    parent=branch.active_v2(data_root,publication)
    if parent:return branch.auxiliary_report(data_root,day,publication,parent,publish_policy=publish_policy)
    out=directory(data_root,day)
    machine=json.loads((out/'machine.json').read_text())
    inputs=json.loads((out/'provider-inputs.json').read_text())
    labels={r['event_id']:r for r in json.loads((out/'evaluation-labels-private.json').read_text())}
    results={}
    for path in result_paths(data_root,day):
        for line in path.read_text().splitlines():
            record=json.loads(line)
            old=results.get(record['request_identity'])
            if old is not None and old!=record:raise ValueError('conflicting_cached_provider_response')
            results[record['request_identity']]=record
    index={};excluded=Counter();ids=set()
    for row in inputs:
        expected={arm:actual_request(row,arm) for arm in ARMS}
        records={arm:results.get(request['paired_replay_id']) for arm,request in expected.items()}
        if any(not r or not (r.get('result') or {}).get('provider_provenance',{}).get('response_id') for r in records.values()):
            excluded['incomplete_actual_five_arm_point']+=1
            continue
        label=labels[row['event_id']]
        if label['outcome']['status']=='UNRESOLVED':
            excluded['unresolved_outcome']+=1
            continue
        source=row['input'];f=source['entry_setup_evidence_v1']['facts']
        key='|'.join((source['symbol_group'],source['market'],'ALL' if source['symbol_group']=='samsung' else source['price_band']))
        rule=next(c['payload']['rule'] for c in machine['cells'] if c['key']==key)
        if not kernel.conditions(f)[rule]:
            excluded['outside_selected_machine_cell']+=1
            continue
        for arm,r in records.items():
            if r['request']!=expected[arm]:raise ValueError('actual_request_identity_binding_invalid')
            rid=r['result']['provider_provenance']['response_id']
            if rid in ids:raise ValueError('duplicate_actual_response_id')
            ids.add(rid)
            index[row['event_id'],arm]=dict(key=key,win=label['outcome']['status']=='WIN',
                verdict=r['result']['candidate_response'].get('risk_verdict'),errors=r['validation_errors'],response_id=rid)
    cells=[]
    for key in expected_cells():
        metrics={}
        for arm in ARMS:
            rs=[r for (event,a),r in index.items() if a==arm and r['key']==key]
            passed=[r for r in rs if r['verdict']=='PASS']
            metrics[arm]=dict(points=len(rs),pass_count=len(passed),pass_wins=sum(r['win'] for r in passed),
                invalid_count=sum(bool(r['errors']) for r in rs),invalid_pass_count=sum(bool(r['errors']) for r in passed),
                raw_verdicts=dict(Counter(r['verdict'] for r in rs)))
        candidates=[arm for arm in TIE_ORDER if metrics[arm]['pass_count']]
        selected=max(candidates,key=lambda arm:(Fraction(metrics[arm]['pass_wins'],metrics[arm]['pass_count']),
                                                 metrics[arm]['pass_wins'])) if candidates else None
        cells.append(dict(key=key,payload=dict(arm=selected) if selected else None,
                          local_metrics=metrics.get(selected),candidates=metrics,inherited_from=None))
    inherit(cells, previous_cells(data_root, day, 'auxiliary'))
    report=seal(dict(schema=SCHEMA,source_date=day,target_date=day,publication_date=publication,status='completed',
        generated_at=datetime.now(KST).isoformat(),version=PRODUCTION_VERSION,cells=cells,
        primary_metric='actual_raw_PASS_wins_over_all_actual_raw_PASS',
        points=len(inputs),machine_eligible_complete_points=len(index)//len(ARMS),excluded_points=dict(excluded),
        machine_report_sha256=machine['artifact_content_sha256'],results_sources=[dict(path=str(p.resolve()),sha256=file_hash(p)) for p in result_paths(data_root,day)],
        input_sha256=digest(inputs),call_freeze_sha256=json.loads((out/'call-freeze.json').read_text())['artifact_content_sha256'],
        validity_adjustment_in_rank=False,holdout_gate=False,ev_gate=False,call_limit=None,spend_limit=None,**AUTH))
    write(out/'auxiliary.json',report)
    if not publish_policy:
        return report
    from src.engine.scalping.continuous_reversal_policy import publish
    staged=publish(data_root,day,publication,machine,report)
    output={**report,'staged':staged}
    output=seal(output)
    # The paired report keeps the native auxiliary evidence hash, and exposes
    # staging separately. The family snapshot binds auxiliary.json itself.
    write(Path(data_root)/'report'/'ai_entry_setup_paired_replay_batch'/f'compact_auxiliary_paired_economic_{day}.json',output)
    return output


def actual_request(row, arm):
    from src.engine.scalping.ai_decision_quality import _sha256
    inp,prompt,schema = production_request(row['input'],arm)
    key = _sha256([PRODUCTION_VERSION,row['event_id'],inp,prompt,schema])
    return dict(paired_replay_id=key, paired_replay_parent_id=row['event_id'],
        micro_reversion_replay_arm=arm, offline_provider_attempt_number=1, stage='entry',
        candidate_input=inp,candidate_input_sha256=_sha256(inp),control=dict(provider='openai',model='gpt-5.4-nano'),
        candidate=dict(provider='openai',model='gpt-5.4-nano',prompt_version=PRODUCTION_VERSION+':'+arm,
            system_prompt=prompt,response_schema=schema,response_schema_sha256=_sha256(schema),
            schema_name='entry_setup_risk_adjudication_v1',max_output_tokens=512,reasoning_effort='none'),**AUTH)


def call(request):
    from src.engine.scalping.ai_decision_quality import execute_openai_prompt_v2_candidate
    try:
        result = execute_openai_prompt_v2_candidate(request,timeout_sec=30)
        errors = validate_response(result['candidate_response'],request['candidate_input'],
                                   complete_source_only=request['micro_reversion_replay_arm']==ARMS[-1])
        return dict(result=result,validation_errors=errors)
    except Exception as exc:
        return dict(error_type=type(exc).__name__,validation_errors=['provider_attempt_failed'])


def execute_calls(data_root, day, inputs):
    out = directory(data_root,day)
    out.mkdir(parents=True,exist_ok=True)
    rows=json.loads(Path(inputs).read_text())
    write(out/'provider-inputs.json',rows)
    requests=[(row,arm,actual_request(row,arm)) for row in rows for arm in ARMS]
    freeze=seal(dict(schema=SCHEMA,source_date=day,version=PRODUCTION_VERSION,inputs_sha256=digest(rows),
                     request_hashes=[digest(req) for _,_,req in requests],call_limit=None,spend_limit=None,
                     expires_at=None,concurrency=4,points=len(rows),planned_calls=len(requests),**AUTH))
    write(out/'call-freeze.json',freeze)
    with (out/'provider-worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        results=out/'provider-results.jsonl';attempts=out/'provider-attempts.jsonl'
        cached={json.loads(line)['request_identity'] for path in result_paths(data_root,day) for line in path.read_text().splitlines()}
        reserved={json.loads(line)['request_identity'] for path in result_paths(data_root,day,'provider-attempts.jsonl') for line in path.read_text().splitlines()}
        pending=[]
        for row,arm,req in requests:
            key=req['paired_replay_id']
            if key in cached: continue
            if key in reserved: raise ValueError('uncertain_provider_attempt_requires_reconciliation')
            pending.append((row,arm,req))
        print('Frozen',len(requests),'requests; new',len(pending),flush=True)
        completed=0
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            running={};iterator=iter(pending)
            def submit():
                item=next(iterator,None)
                if item is None:return
                row,arm,req=item
                record=dict(event_id=row['event_id'],arm=arm,request_identity=req['paired_replay_id'],request=req,
                            called_at=datetime.now(KST).isoformat(),freeze_sha256=freeze['artifact_content_sha256'],**AUTH)
                append(attempts,record)
                running[pool.submit(call,req)]=record
            for _ in range(4):submit()
            while running:
                done,_=concurrent.futures.wait(running,return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    record=running.pop(future);record.update(future.result());append(results,record)
                    completed+=1
                    if completed%40==0 or record.get('error_type'):
                        print('Completed',completed,'/',len(pending),'errors',record['validation_errors'],flush=True)
                    submit()
        write(out/'call-completion.json',seal(dict(schema=SCHEMA,source_date=day,status='completed',new_calls=completed,
              freeze_sha256=freeze['artifact_content_sha256'],results_sources=[dict(path=str(p.resolve()),sha256=file_hash(p)) for p in result_paths(data_root,day)],**AUTH)))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--date',required=True)
    parser.add_argument('--publication-date')
    parser.add_argument('--data-root',type=Path,default=Path('data'))
    parser.add_argument('--seed-research',type=Path)
    parser.add_argument('--actual-inputs',type=Path)
    parser.add_argument('--evaluate-only',action='store_true')
    parser.add_argument('--mode',choices=['machine','auxiliary','calls'],default='machine')
    args=parser.parse_args()
    if args.seed_research:prepare_research(args.data_root,args.date,args.seed_research)
    if args.mode=='calls':
        from src.engine.scalping import continuous_reversal_registered_postclose as registered
        if registered.active(args.data_root,args.publication_date or args.date):registered.calls(args.data_root,args.date)
        else:execute_calls(args.data_root,args.date,args.actual_inputs)
    elif args.mode=='machine':print(json.dumps(machine_report(args.data_root,args.date,args.publication_date or args.date)))
    else:
        from src.engine.scalping import continuous_reversal_registered_postclose as registered
        current=registered.active(args.data_root,args.publication_date or args.date)
        if current:
            machine=json.loads((registered.directory(args.data_root,args.date)/'machine-comparison.json').read_text())
            if not args.evaluate_only:
                registered.prepare_inputs(args.data_root,args.date,machine)
                deadline=__import__('os').environ.get('POSTCLOSE_STAGE_DEADLINE_EPOCH')
                registered.calls(args.data_root,args.date,stop_epoch=float(deadline)-120 if deadline else None)
            print(json.dumps(registered.auxiliary_report(args.data_root,args.date,args.publication_date or args.date,current,publish_policy=not args.evaluate_only)))
            return 0
        from src.engine.scalping import continuous_reversal_branch_postclose as branch
        parent=branch.active_v2(args.data_root,args.publication_date or args.date)
        if parent:
            machine=json.loads((directory(args.data_root,args.date)/'machine.json').read_text())
            if not args.evaluate_only:
                branch.prepare_daily_inputs(args.data_root,args.date,machine)
                branch.calls(args.data_root,args.date,inputs_path=branch.directory(args.data_root,args.date)/'daily-provider-inputs.json')
            print(json.dumps(branch.auxiliary_report(args.data_root,args.date,args.publication_date or args.date,parent,publish_policy=not args.evaluate_only)))
            return 0
        if not args.evaluate_only:
            prepare_auxiliary_points(args.data_root,args.date)
            execute_calls(args.data_root,args.date,directory(args.data_root,args.date)/'provider-inputs.json')
        print(json.dumps(auxiliary_report(args.data_root,args.date,args.publication_date or args.date,
                                         publish_policy=not args.evaluate_only)))
    return 0


if __name__=='__main__':raise SystemExit(main())
