"""Bounded branch catalog, all-confirmation phase replay and native reports."""
from __future__ import annotations
import argparse
import concurrent.futures
import copy
import fcntl
import gzip
import json
from collections import Counter
from datetime import datetime
from fractions import Fraction
from pathlib import Path

from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_branches as B
from src.engine.scalping import reversal_auxiliary_phases as A
from src.engine.scalping import reversal_auxiliary_contract as V1
from src.engine.scalping import continuous_reversal_postclose as P

SCHEMA=P.SCHEMA


def directory(data_root,day):
    return Path(data_root)/"report/continuous_reversal_v2"/day


def prepare_initial(data_root,day,research):
    """Use the reviewed native normalized history plus the exact frozen prefix."""
    research=Path(research);out=directory(data_root,day);out.mkdir(parents=True,exist_ok=True)
    parent=json.loads((Path(data_root)/"report/continuous_reversal/2026-10-06/source.json").read_text())
    if parent["artifact_content_sha256"]!=P.digest({k:v for k,v in parent.items() if k!="artifact_content_sha256"}):
        raise ValueError("branch_research_parent_invalid")
    records=[r for r in parent["normalized_sources"]["partitions"] if r["venue"]=="SOR" and r["session"]=="SOR_REGULAR"]
    inputs=[];receipts=[];counts={};labels=Counter()
    for record in records+[dict(day=day,path=str(research/"today-frozen.json.gz"),sha256=P.file_hash(research/"today-frozen.json.gz"))]:
        if P.file_hash(record["path"])!=record["sha256"]:raise ValueError("branch_normalized_source_changed")
        value=json.loads(gzip.decompress(Path(record["path"]).read_bytes()))
        rows=value.get("rows") if record["day"]==day else value["symbols"].get("005930",[])
        if not rows:continue
        saved=research/f"bars-{record['day']}.json"
        if saved.is_file():
            bars=json.loads(saved.read_text())["rows"]
            bar_path=out/"frozen"/(saved.stem+'-'+P.digest(bars)+'.json');P.write(bar_path,dict(rows=bars))
            receipts.append(dict(path=str(bar_path.resolve()),sha256=P.file_hash(bar_path)))
        else:bars=[]
        if record["day"]==day:
            frozen=out/"frozen/today-frozen.json.gz";frozen.parent.mkdir(parents=True,exist_ok=True)
            if not frozen.exists():frozen.write_bytes(Path(record["path"]).read_bytes())
            if P.file_hash(frozen)!=record["sha256"]:raise ValueError("branch_today_prefix_changed")
            receipts.append(dict(path=str(frozen.resolve()),sha256=record["sha256"]))
        else:receipts.append(dict(path=record["path"],sha256=record["sha256"]))
        points,census=B.replay(rows,symbol="005930",venue="SOR",session="SOR_REGULAR",bars=K.Bars(bars) if bars else None)
        counts[record["day"]]=census
        for point in points:
            labels[point["outcome"]["status"]]+=1
            inputs.append(dict(event_id=point["event"]["event_id"],phase=B.CONFIRMED,**point))
        print(record["day"],len(points),census,flush=True)
    manifest=P.seal(dict(schema=SCHEMA,source_date=day,status="completed",points=len(inputs),
                        definition_sha256=B.DEFINITION_SHA256,code_sha256=P.file_hash(B.__file__),
                        source_receipts=receipts,census=counts,counts=dict(labels),input_sha256=P.digest(inputs),**P.AUTH))
    P.write(out/"provider-inputs.json",inputs);P.write(out/"source.json",manifest)
    return manifest


def request(row,arm):
    if row['phase']==B.FIRST:return P.actual_request(row,arm)
    inp,prompt,schema=A.production_request(row["input"],arm,phase=row["phase"],event=row["event"])
    from src.engine.scalping.ai_decision_quality import _sha256
    identity=_sha256([A.version(row["phase"],arm),row["event_id"],inp,prompt,schema])
    return dict(paired_replay_id=identity,paired_replay_parent_id=row["event_id"],
                micro_reversion_replay_arm=arm,offline_provider_attempt_number=1,stage="entry",
                candidate_input=inp,candidate_input_sha256=_sha256(inp),control=dict(provider="openai",model="gpt-5.4-nano"),
                candidate=dict(provider="openai",model="gpt-5.4-nano",prompt_version=A.version(row["phase"],arm),
                               system_prompt=prompt,response_schema=schema,response_schema_sha256=_sha256(schema),
                               schema_name="entry_setup_risk_adjudication_v1",max_output_tokens=512,reasoning_effort="none"),**P.AUTH)


def calls(data_root,day,*,inputs_path=None):
    from src.engine.scalping.ai_decision_quality import execute_openai_prompt_v2_candidate
    out=directory(data_root,day);out.mkdir(parents=True,exist_ok=True)
    rows=json.loads(Path(inputs_path or out/"provider-inputs.json").read_text())
    requests=[(row,arm,request(row,arm)) for row in rows for arm in V1.ARMS]
    freeze=P.seal(dict(schema=SCHEMA,source_date=day,status="frozen",points=len(rows),planned_calls=len(requests),
                       request_sha256=P.digest([r for _,_,r in requests]),call_limit=None,**P.AUTH))
    P.write(out/"call-freezes"/(freeze['artifact_content_sha256']+'.json'),freeze)
    P.write(out/"call-freeze.json",freeze)
    with (out/"provider-worker.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        results=out/"provider-results.jsonl";attempts=out/"provider-attempts.jsonl"
        history=P.result_paths(data_root,day)+[p for p in sorted(out.parent.glob('????-??-??/provider-results.jsonl')) if '2026-06-05'<=p.parent.name<=day]
        cached={json.loads(l)['request_identity'] for path in history for l in path.read_text().splitlines()}
        attempt_history=P.result_paths(data_root,day,'provider-attempts.jsonl')+[p for p in sorted(out.parent.glob('????-??-??/provider-attempts.jsonl')) if '2026-06-05'<=p.parent.name<=day]
        reserved={json.loads(l)['request_identity'] for path in attempt_history for l in path.read_text().splitlines()}
        if (reserved-cached):raise ValueError("branch_uncertain_provider_attempt_requires_reconciliation")
        def call(item):
            row,arm,req=item
            record=dict(event_id=row["event_id"],phase=row["phase"],arm=arm,request_identity=req["paired_replay_id"],
                        request=req,called_at=datetime.now(K.KST).isoformat(),freeze_sha256=freeze["artifact_content_sha256"],**P.AUTH)
            # Reserve and fsync before a provider side effect, single writer below.
            try:
                result=execute_openai_prompt_v2_candidate(req,timeout_sec=30)
                record.update(result=result,validation_errors=A.validate_response(result["candidate_response"],req["candidate_input"],arm=arm,phase=row["phase"]))
            except Exception as exc:record.update(error_type=type(exc).__name__,validation_errors=["provider_attempt_failed"])
            return record
        pending=[item for item in requests if item[2]["paired_replay_id"] not in cached]
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            running={};iterator=iter(pending);done_count=0
            def submit():
                item=next(iterator,None)
                if item is None:return
                P.append(attempts,dict(event_id=item[0]["event_id"],request_identity=item[2]["paired_replay_id"],request=item[2]))
                running[pool.submit(call,item)]=item
            for _ in range(4):submit()
            while running:
                done,_=concurrent.futures.wait(running,return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    running.pop(future);P.append(results,future.result());done_count+=1
                    if done_count%25==0:print("confirmed actual calls",done_count,"/",len(pending),flush=True)
                    submit()
        P.write(out/"call-completion.json",P.seal(dict(schema=SCHEMA,source_date=day,status="completed",new_calls=done_count,**P.AUTH)))


def reports(data_root,day,parent_bundle):
    """Designated initial union; observed phase metrics never reuse FIRST bytes."""
    out=directory(data_root,day);source=json.loads((out/"source.json").read_text())
    points=json.loads((out/"provider-inputs.json").read_text())
    if P.digest(points)!=source["input_sha256"] or P.file_hash(B.__file__)!=source["code_sha256"]:
        raise ValueError("branch_report_input_or_code_changed")
    parent=parent_bundle["continuous_reversal"]
    machine_cells=[];auxiliary_cells=[]
    statuses=Counter(p["outcome"]["status"] for p in points)
    resolved=statuses["WIN"]+statuses["FAIL_STOP"]+statuses["FAIL_TIMEOUT"]
    branch_metric=dict(wins=statuses["WIN"],resolved=resolved,excluded=statuses["UNRESOLVED"]) if resolved else None
    records={json.loads(l)["request_identity"]:json.loads(l) for l in (out/"provider-results.jsonl").read_text().splitlines()}
    metrics={a:Counter() for a in V1.ARMS};complete=0;excluded=Counter()
    response_ids=set()
    for point in points:
        expected={a:request(point,a) for a in V1.ARMS}
        results={a:records.get(req["paired_replay_id"]) for a,req in expected.items()}
        good={}
        for arm,r in results.items():
            if not r or not (r.get("result") or {}).get("provider_provenance",{}).get("response_id"):
                excluded["missing_actual_response"]+=1;continue
            if r["request"]!=expected[arm]:raise ValueError("branch_actual_request_binding_invalid")
            rid=r["result"]["provider_provenance"]["response_id"]
            if rid in response_ids:raise ValueError("branch_duplicate_response_id")
            response_ids.add(rid);good[arm]=r
            metrics[arm]["observed_points"]+=1
        if len(good)!=len(V1.ARMS):continue
        complete+=1
        if point["outcome"]["status"]=="UNRESOLVED":
            excluded["unresolved_outcome"]+=1;continue
        for arm,r in good.items():
            m=metrics[arm];m["resolved_points"]+=1;m["invalid_responses"]+=bool(r["validation_errors"])
            if r["result"]["candidate_response"].get("risk_verdict")=="PASS":
                m["pass_count"]+=1;m["pass_wins"]+=point["outcome"]["status"]=="WIN"
    eligible=[a for a in V1.TIE_ORDER if metrics[a]["pass_count"]]
    selected=max(eligible,key=lambda a:Fraction(metrics[a]["pass_wins"],metrics[a]["pass_count"])) if eligible else None
    if not selected:raise ValueError("confirmed_phase_comparable_PASS_missing")
    frozen_result=out/'frozen'/('provider-results-'+P.file_hash(out/'provider-results.jsonl')+'.jsonl')
    if not frozen_result.exists():frozen_result.write_bytes((out/'provider-results.jsonl').read_bytes())
    result_evidence=dict(path=str(frozen_result.resolve()),sha256=P.file_hash(frozen_result))
    frozen_inputs=out/'frozen'/('provider-inputs-'+P.digest(points)+'.json')
    P.write(frozen_inputs,points)
    for key in P.expected_cells():
        old=parent["machine_cells"][key];rule=old["payload"]["rule"]
        branches=[B.legacy_branch(rule)]
        first_metrics=old.get("local_metrics")
        if first_metrics is None:
            parent_key=old.get("inherited_from")
            if parent_key in parent["machine_cells"]:first_metrics=parent["machine_cells"][parent_key].get("local_metrics")
        bm={branches[0]["branch_id"]:({k:first_metrics[k] for k in ("wins","resolved")} if first_metrics else None)}
        p=B.payload(branches)
        if key=="samsung|REGULAR|ALL":
            branches.append(B.pattern_branch());bm[B.BRANCH]=branch_metric;p=B.payload(branches)
        mc=dict(key=key,payload=p,payload_sha256=P.digest(p),local_metrics=old.get("local_metrics"),
                inherited_from=old.get("inherited_from"),branch_metrics=bm,carry_source=parent["family_sha256"])
        if mc["inherited_from"]:mc["parent_payload_sha256"]=P.digest(p)
        machine_cells.append(mc)
        arm=parent["auxiliary_cells"][key]["payload"]["arm"]
        first=dict(arm=arm,binding=A.binding(B.FIRST,arm),local_metrics=None,
                   carry_source=dict(family_sha256=parent["family_sha256"],cell_key=key,phase=B.FIRST,
                                     reason="unchanged_incumbent_rule_and_production_bytes"))
        phases={B.FIRST:first}
        if key=="samsung|REGULAR|ALL":
            phases[B.CONFIRMED]=dict(arm=selected,binding=A.binding(B.CONFIRMED,selected),local_metrics=dict(metrics[selected]),
                                    candidates={a:dict(m) for a,m in metrics.items()},actual_response_evidence=result_evidence,
                                    complete_five_arm_points=complete,excluded=dict(excluded))
        ap=dict(phase_policies=phases)
        auxiliary_cells.append(dict(key=key,payload=ap,payload_sha256=P.digest(ap),local_metrics=None,
                                    inherited_from=None,carry_source=parent["family_sha256"]))
    common=dict(schema=SCHEMA,source_date=day,target_date=day,publication_date=day,status="completed",**P.AUTH)
    machine=P.seal(dict(common,report_scope="main_mechanistic_entry",cells=machine_cells,
                       parent_bundle_sha256=parent_bundle['bundle_sha256'],
                       source_manifest_sha256=source["artifact_content_sha256"],source_receipts=source["source_receipts"],
                       label_contract=dict(target_net_pct=.4,stop_net_pct=-3.,cost_rate=.0023,horizon_seconds=1800),
                       designated_initial_union=True,new_branch_metrics=branch_metric))
    auxiliary=P.seal(dict(common,cells=auxiliary_cells,machine_report_sha256=machine["artifact_content_sha256"],
                         results_sources=[result_evidence],source_receipts=[dict(path=str(frozen_inputs.resolve()),sha256=P.file_hash(frozen_inputs))],
                         phase_metrics={a:dict(m) for a,m in metrics.items()},complete_five_arm_points=complete,excluded=dict(excluded)))
    P.write(out/"machine.json",machine);P.write(out/"auxiliary.json",auxiliary)
    return machine,auxiliary


def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument("--date",required=True);p.add_argument("--data-root",type=Path,default=Path("data"))
    p.add_argument("--research",type=Path);p.add_argument("--calls",action="store_true")
    args=p.parse_args(argv)
    if args.research:prepare_initial(args.data_root,args.date,args.research)
    if args.calls:calls(args.data_root,args.date)


def active_v2(data_root,day):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    bundle=N.load_effective(data_root=Path(data_root),target_date=day)
    return bundle if (bundle or {}).get('continuous_reversal',{}).get('schema')=='continuous_reversal_policy_v2' else None


def catalog(key):
    singles=[B.payload([B.legacy_branch(r)]) for r in K.RULES]
    if key!='samsung|REGULAR|ALL':return singles
    return singles+[B.payload([B.pattern_branch()])]+[B.payload([B.legacy_branch(r),B.pattern_branch()]) for r in K.RULES]


def _matches(point,branch):
    e=point['event']
    if branch['kind']=='legacy_rule':
        first=e if point['phase']==B.FIRST else e.get('coincident_first')
        return first is not None and K.conditions(first)[branch['rule']]
    return (point['phase']==B.CONFIRMED and (e['symbol'],e['market'],e['venue'],e['source_item'])==('005930','REGULAR','SOR','005930_AL')
            and e.get('branch_definition_sha256')==B.DEFINITION_SHA256)


def _metrics(points,branches):
    matched={}
    for p in points:
        if any(_matches(p,b) for b in branches):
            identity=p['event_id'];old=matched.get(identity)
            if old and old['outcome']['status']!=p['outcome']['status']:
                raise ValueError('branch_same_confirmation_outcome_conflict')
            matched[identity]=p
    c=Counter(p['outcome']['status'] for p in matched.values())
    return dict(wins=c['WIN'],resolved=c['WIN']+c['FAIL_STOP']+c['FAIL_TIMEOUT'],excluded=c['UNRESOLVED'],counts=dict(c))


def _parent_cell(family,key):
    old=family['machine_cells'][key]
    if family['schema']=='continuous_reversal_policy_v2':return copy.deepcopy(old)
    rule=old['payload']['rule'];p=B.payload([B.legacy_branch(rule)])
    m=old.get('local_metrics')
    if m is None and old.get('inherited_from') in family['machine_cells']:
        m=family['machine_cells'][old['inherited_from']].get('local_metrics')
    return dict(key=key,payload=p,payload_sha256=P.digest(p),local_metrics=old.get('local_metrics'),
                branch_metrics={p['branches'][0]['branch_id']:m},carry_source=family['family_sha256'])


def select_machine(points,parent_family,*,regular_parents=None):
    """Finite frozen catalog, exact raw fractions, incumbent on equal fraction."""
    pools={k:[] for k in P.expected_cells()}
    for p in points:pools[K.cell_key(p['event']['symbol'],p['event']['market'],p['event']['confirmation_price'])].append(p)
    cells={}
    for key in sorted(P.expected_cells(),key=lambda k:'|REGULAR|' not in k):
        old=_parent_cell(parent_family,key);candidates=[]
        for payload in catalog(key):
            m=_metrics(pools[key],payload['branches'])
            # The registered pattern has only one exact item/route. A B-only
            # list cannot cover the legacy REGULAR KRX/NXT observation scopes.
            applicable=any(b['kind']=='legacy_rule' for b in payload['branches'])
            candidates.append(dict(payload=payload,payload_sha256=P.digest(payload),metrics=m,
                                   status='eligible' if applicable and m['resolved'] else 'scope_gap' if not applicable else 'no_resolved_sample'))
        eligible=[c for c in candidates if c['status']=='eligible']
        if eligible:
            chosen=max(eligible,key=lambda c:(Fraction(c['metrics']['wins'],c['metrics']['resolved']),
                       c['payload_sha256']==old['payload_sha256'],-len(c['payload']['branches']),-candidates.index(c)))
            payload=chosen['payload'];m=chosen['metrics'];inherit=None;carry=None
        else:
            g,market,band=key.split('|');pk='|'.join((g,'REGULAR',band))
            regular=cells.get(pk) if market!='REGULAR' else None
            choices=[regular]+list((regular_parents or {}).get(pk,[]))+[_parent_cell(parent_family,pk)]
            chosen_parent=next((c for c in choices if c and all(b['kind']=='legacy_rule' for b in c['payload']['branches'])),None)
            if chosen_parent is None:raise ValueError('applicable_regular_parent_missing:'+pk)
            payload=copy.deepcopy(chosen_parent['payload']);m=None;inherit=pk if chosen_parent is regular else 'previous:'+pk
            carry=chosen_parent.get('carry_source') or parent_family['family_sha256']
        bm={b['branch_id']:(_metrics(pools[key],[b]) if _metrics(pools[key],[b])['resolved'] else None) for b in payload['branches']}
        cell=dict(key=key,payload=payload,payload_sha256=P.digest(payload),local_metrics=m,inherited_from=inherit,
                  branch_metrics=bm,candidates=candidates,carry_source=carry or parent_family['family_sha256'])
        if inherit:cell['parent_payload_sha256']=P.digest(payload)
        cells[key]=cell
    return [cells[k] for k in P.expected_cells()]


def daily_population(data_root,day):
    """Same native history for first turns and confirmed turns, no AI trace filter."""
    source=P.ensure_population(data_root,day);out=directory(data_root,day)
    bar_sources={d:P.completed_bars(data_root,d) for d in sorted({r['day'] for r in source['normalized_sources']['partitions']})}
    fingerprint=P.digest([source['artifact_content_sha256'],P.file_hash(B.__file__),P.file_hash(K.__file__),B.DEFINITION_SHA256,
                          dict(target_net_pct=.4,stop_net_pct=-3.,cost_rate=.0023,horizon_seconds=1800),
                          {d:receipts for d,(_,receipts) in bar_sources.items()}])
    cache=out/'frozen'/('daily-population-'+fingerprint+'.json')
    if cache.exists():
        value=json.loads(cache.read_text())
        if value!=P.seal(value):raise ValueError('branch_daily_cache_changed')
        return value,cache
    points=[];receipts=[];partitions={(r['day'],r['venue'],r['session']):r for r in source['normalized_sources']['partitions']}
    from src.engine.scalping.micro_reversion.forward_collector import _explicit_item_venue
    routes={};quality=Counter()
    for rec in partitions.values():
        if P.file_hash(rec['path'])!=rec['sha256']:raise ValueError('branch_daily_normalized_changed')
        receipts.append(dict(path=rec['path'],sha256=rec['sha256']))
        raw=json.loads(gzip.decompress(Path(rec['path']).read_bytes()))['symbols']
        bars,bar_receipts=bar_sources[rec['day']]
        for receipt in bar_receipts:
            dst=out/'frozen'/('bars-'+receipt['sha256']+'.json');dst.parent.mkdir(parents=True,exist_ok=True)
            if not dst.exists():dst.write_bytes(Path(receipt['path']).read_bytes())
            if P.file_hash(dst)!=receipt['sha256']:raise ValueError('branch_bar_snapshot_changed')
            receipts.append(dict(path=str(dst.resolve()),sha256=receipt['sha256']))
        for code,rows in raw.items():
            items={r[9] for r in rows if isinstance(r[9],str) and r[9].split('_',1)[0]==code and _explicit_item_venue(r[9])==rec['venue']}
            quality['identity_missing_or_conflicting_rows']+=sum(r[9] not in items for r in rows)
            events=[];valid_count=0
            for item in sorted(items):
                strict=[r[:] for r in rows]
                for r in strict:
                    if r[9]!=item:r[8]=0
                turns,coverage=K.analyze_symbol(strict,rec['day'],rec['venue'],rec['session'],code)
                valid_count+=coverage['valid_price_rows']
                for e in turns:
                    supplement=bars.get((rec['day'],item))
                    if e['entry_ask'] is not None and e['outcome']['status']=='UNRESOLVED' and supplement:
                        outcome=supplement.label(e['epoch'],e['entry_ask'],1800)
                        if outcome['status']!='UNRESOLVED':e['outcome']={**outcome,'source':'same_item_completed_bar_backfill'}
                    events.append(dict(event_id=e['event_id'],phase=B.FIRST,event=e,outcome=e['outcome']))
            key=(rec['day'],code,K.market_bucket(rec['session']))
            rank=(valid_count,{'SOR':2,'NXT':1,'KRX':0}[rec['venue']])
            if key not in routes or rank>routes[key][0]:routes[key]=(rank,events)
    for _,events in routes.values():points.extend(events)
    for rec in partitions.values():
        if (rec['venue'],K.market_bucket(rec['session']))!=('SOR','REGULAR'):continue
        if P.file_hash(rec['path'])!=rec['sha256']:raise ValueError('branch_daily_normalized_changed')
        receipts.append(dict(path=rec['path'],sha256=rec['sha256']))
        raw=json.loads(gzip.decompress(Path(rec['path']).read_bytes()));rows=raw['symbols'].get('005930',[])
        if not rows:continue
        bars,bar_receipts=bar_sources[rec['day']]
        # Seal completed bars; runtime caches are mutable and cannot be issued
        # policy dependencies. Replay only this exact item, never next quote.
        bar=bars.get((rec['day'],'005930_AL'))
        events,census=B.replay(rows,symbol='005930',venue=rec['venue'],session=rec['session'],bars=bar)
        points.extend(dict(event_id=p['event']['event_id'],phase=B.CONFIRMED,**p) for p in events)
        if bar_receipts:
            # Labels are frozen in this cache; retain the input snapshot too.
            for receipt in bar_receipts:
                src=Path(receipt['path']);dst=out/'frozen'/('bars-'+receipt['sha256']+'.json')
                if not dst.exists():dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
                if P.file_hash(dst)!=receipt['sha256']:raise ValueError('branch_bar_snapshot_changed')
                receipts.append(dict(path=str(dst.resolve()),sha256=receipt['sha256']))
    value=P.seal(dict(schema=SCHEMA,source_date=day,status='completed',population_fingerprint=fingerprint,
                      source_manifest_sha256=source['artifact_content_sha256'],points=points,source_receipts=receipts,source_quality_exclusions=dict(quality),**P.AUTH))
    P.write(cache,value)
    return value,cache


def machine_report(data_root,day,publication,parent_bundle):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    value,cache=daily_population(data_root,day);regular_parents={}
    prior=parent_bundle;seen=set()
    while prior and prior['bundle_sha256'] not in seen:
        seen.add(prior['bundle_sha256']);family=prior.get('continuous_reversal')
        if family:
            for key in P.expected_cells():
                if '|REGULAR|' in key:regular_parents.setdefault(key,[]).append(_parent_cell(family,key))
        parent=(family or {}).get('parent_bundle_sha256')
        if not parent:break
        prior=N._read(N.root(Path(data_root))/'generations'/(parent+'.json'))
        N.validate(prior,target_date=prior['target_date'])
    cells=select_machine(value['points'],parent_bundle['continuous_reversal'],regular_parents=regular_parents)
    report=P.seal(dict(schema=SCHEMA,source_date=day,target_date=day,publication_date=publication,status='completed',
                       report_scope='main_mechanistic_entry',branch_registry_version=B.VERSION,designated_initial_union=False,
                       parent_bundle_sha256=parent_bundle['bundle_sha256'],
                       cells=cells,selection_basis='cumulative_raw_win_fraction',population='all_continuous_price_turns_and_registered_confirmations',
                       source_manifest_sha256=value['source_manifest_sha256'],population_path=str(cache.resolve()),
                       source_receipts=value['source_receipts']+[dict(path=str(cache.resolve()),sha256=P.file_hash(cache))],
                       label_contract=dict(target_net_pct=.4,stop_net_pct=-3.,cost_rate=.0023,horizon_seconds=1800),**P.AUTH))
    P.write(directory(data_root,day)/'daily-machine.json',report)
    P.write(P.directory(data_root,day)/'machine.json',report)
    standard=Path(data_root)/'report/ai_decision_action_outcome_calibration'
    P.write(standard/f'winrate_policy_{day}.json',report)
    P.write(standard/f'winrate_policy_terminal_{day}.json',P.seal(dict(schema=SCHEMA,source_date=day,target_date=day,status='completed',
            selection_basis=report['selection_basis'],report_sha256=report['artifact_content_sha256'],disposition='continuous_reversal_selected',
            policy_sha256=P.digest(cells),staged=dict(status='machine_component_prepared'),**P.AUTH)))
    return report


def prepare_daily_inputs(data_root,day,machine):
    population=json.loads(Path(machine['population_path']).read_text());cells={c['key']:c for c in machine['cells']}
    pools={};fractions={}
    for p in population['points']:
        e=p['event'];key=K.cell_key(e['symbol'],e['market'],e['confirmation_price']);cell=cells[key]
        matches=[b for b in cell['payload']['branches'] if _matches(p,b)]
        if not matches or p['outcome']['status']=='UNRESOLVED':continue
        def rank(b):
            m=cell['branch_metrics'][b['branch_id']]
            return (m is not None,Fraction(m['wins'],m['resolved']) if m else Fraction(0),-cell['payload']['branches'].index(b))
        primary=max(matches,key=rank)
        if primary['decision_phase']!=p['phase']:continue
        identity=(key,p['phase'],e['event_id'].split(':',1)[0]);pools.setdefault(identity,{})[p['event_id']]=p
    chosen=[p for pool in pools.values() for p in sorted(pool.values(),key=lambda p:P.digest(p['event_id']))[:24]]
    normalized=json.loads((P.directory(data_root,day)/'source.json').read_text())['normalized_sources']['partitions']
    for rec in normalized:
        group=[p for p in chosen if p['phase']==B.FIRST and p['event']['venue']==rec['venue'] and p['event']['session']==rec['session'] and p['event_id'].startswith(rec['day']+':')]
        if not group:continue
        if P.file_hash(rec['path'])!=rec['sha256']:raise ValueError('branch_phase_source_changed')
        raw=json.loads(gzip.decompress(Path(rec['path']).read_bytes()))['symbols'];features={}
        for point in group:
            e=point['event'];rows=[r[:] for r in raw[e['symbol']]]
            for r in rows:
                if r[9]!=e['source_item']:r[8]=0
            feature_key=(e['symbol'],e['source_item'])
            if feature_key not in features:features[feature_key]=K.build_features(rows)
            i=e['entry_index'];values={k:float(v[i]) if __import__('math').isfinite(v[i]) else None for k,v in features[feature_key].items()}
            values.update({k:e[k] for k in K.INPUT_FEATURES[4:]});point['input']=K.make_input(e,rows,values)
    if any(p.get('input') is None for p in chosen):raise ValueError('branch_phase_input_missing')
    out=directory(data_root,day);P.write(out/'daily-provider-inputs.json',chosen)
    return chosen


def auxiliary_report(data_root,day,publication,parent_bundle,*,publish_policy=True):
    from src.engine.scalping import continuous_reversal_policy_v2 as V2
    out=directory(data_root,day);machine=json.loads((out/'daily-machine.json').read_text())
    points=json.loads((out/'daily-provider-inputs.json').read_text());records={};paths=[]
    for path in P.result_paths(data_root,day)+sorted(out.parent.glob('????-??-??/provider-results.jsonl')):
        if not '2026-06-05'<=path.parent.name<=day:continue
        frozen=out/'frozen'/('results-'+P.file_hash(path)+'.jsonl');frozen.parent.mkdir(parents=True,exist_ok=True)
        if not frozen.exists():frozen.write_bytes(path.read_bytes())
        paths.append(dict(path=str(frozen.resolve()),sha256=P.file_hash(frozen)))
        for line in frozen.read_text().splitlines():
            r=json.loads(line);old=records.get(r['request_identity'])
            if old and old.get('result')!=r.get('result'):raise ValueError('branch_duplicate_actual_request_conflict')
            records[r['request_identity']]=r
    metrics={};ids=set();excluded=Counter()
    for p in points:
        key=K.cell_key(p['event']['symbol'],p['event']['market'],p['event']['confirmation_price']);expected={a:request(p,a) for a in V1.ARMS}
        rs={a:records.get(req['paired_replay_id']) for a,req in expected.items()}
        if any(not r or not (r.get('result') or {}).get('provider_provenance',{}).get('response_id') for r in rs.values()):
            excluded['missing_complete_five_arm_point']+=1;continue
        for arm,r in rs.items():
            if r['request']!=expected[arm]:raise ValueError('branch_phase_actual_bytes_changed')
            rid=r['result']['provider_provenance']['response_id']
            if rid in ids:raise ValueError('branch_phase_duplicate_response_id')
            ids.add(rid);m=metrics.setdefault((key,p['phase'],arm),Counter());m['points']+=1
            m['invalid_count']+=bool(r['validation_errors'])
            if r['result']['candidate_response'].get('risk_verdict')=='PASS':
                m['pass_count']+=1;m['pass_wins']+=p['outcome']['status']=='WIN'
    parent=parent_bundle['continuous_reversal'];cells=[]
    for mc in sorted(machine['cells'],key=lambda c:'|REGULAR|' not in c['key']):
        key=mc['key'];policies={}
        for phase in {b['decision_phase'] for b in mc['payload']['branches']}:
            old=parent['auxiliary_cells'][key]['payload']['phase_policies'].get(phase)
            candidates={a:dict(metrics.get((key,phase,a),Counter())) for a in V1.ARMS}
            eligible=[a for a in V1.TIE_ORDER if candidates[a].get('pass_count')]
            if eligible:
                selected=max(eligible,key=lambda a:(Fraction(candidates[a]['pass_wins'],candidates[a]['pass_count']),bool(old and old['arm']==a)))
                policies[phase]=dict(arm=selected,binding=A.binding(phase,selected),local_metrics=candidates[selected],candidates=candidates,
                                     actual_response_evidence=paths,complete_five_arm_points=sum(candidates[a].get('points',0) for a in V1.ARMS)//5)
            else:
                pk=key.replace('|PRE|','|REGULAR|').replace('|AFTER|','|REGULAR|')
                regular=next((c for c in cells if c['key']==pk),None)
                inherited=(regular or {}).get('payload',{}).get('phase_policies',{}).get(phase) or parent['auxiliary_cells'][pk]['payload']['phase_policies'].get(phase) or old
                if not inherited:raise ValueError('branch_auxiliary_applicable_regular_parent_missing:'+key+':'+phase)
                policies[phase]=copy.deepcopy(inherited);policies[phase]['local_metrics']=None
                policies[phase]['carry_source']=dict(family_sha256=parent['family_sha256'],cell_key=pk,phase=phase,reason='no_resolved_actual_PASS_sample')
        payload=dict(phase_policies=policies)
        cells.append(dict(key=key,payload=payload,payload_sha256=P.digest(payload),local_metrics=None,inherited_from=None))
    index={c['key']:c for c in cells};cells=[index[k] for k in P.expected_cells()]
    inp=out/'frozen'/('daily-inputs-'+P.digest(points)+'.json');P.write(inp,points)
    report=P.seal(dict(schema=SCHEMA,source_date=day,target_date=day,publication_date=publication,status='completed',cells=cells,
                      machine_report_sha256=machine['artifact_content_sha256'],results_sources=paths,source_receipts=[dict(path=str(inp.resolve()),sha256=P.file_hash(inp))],
                      excluded_points=dict(excluded),primary_metric='actual_raw_PASS_wins_over_all_actual_raw_PASS',call_limit=None,validity_adjustment_in_rank=False,**P.AUTH))
    P.write(out/'daily-auxiliary.json',report);P.write(P.directory(data_root,day)/'auxiliary.json',report)
    P.write(P.directory(data_root,day)/'call-freeze.json',json.loads((out/'call-freeze.json').read_text()))
    canonical_results=P.directory(data_root,day)/'provider-results.jsonl'
    canonical_results.write_text(''.join(json.dumps(records[k],ensure_ascii=True,allow_nan=False)+'\n' for k in sorted(records)))
    output=report
    if publish_policy:
        import subprocess
        commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        bundle=V2.stage(data_root,day,publication,machine,report,target_date=__import__('src.engine.scalping.mechanistic_entry_runtime_policy',fromlist=['next_target']).next_target(publication),release_commit=commit)
        output=P.seal(dict(report,staged=dict(status='prepared',bundle_sha256=bundle['bundle_sha256'],target_date=bundle['target_date'])))
        P.write(Path(data_root)/'report/ai_entry_setup_paired_replay_batch'/f'compact_auxiliary_paired_economic_{day}.json',output)
    return output


if __name__=="__main__":main()
