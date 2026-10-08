"""Operating-list replay, contribution and shared incremental AI comparisons.

This successor never searches portfolios or clones a request database. Native
prefix objects and exact requests live in the shared offline store; reports are
small immutable memberships, masks and aggregates. Daily evaluation cannot
silently remove an operating policy.
"""
from __future__ import annotations
import copy
import gzip
import json
import os
import sys
import subprocess
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from src.engine.ai import offline_comparison_store as S
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_branches as B
from src.engine.scalping import reversal_path_catalog as C
from src.engine.scalping import reversal_path_runtime as R
from src.engine.scalping import reversal_auxiliary_contract as V1
from src.engine.scalping import reversal_operating_auxiliary as UNION
from src.engine.scalping import reversal_operating_evaluation as A
from src.engine.scalping import reversal_operating_runtime as LIVE
from src.engine.scalping import continuous_reversal_policy_v5 as V5
from src.engine.scalping import continuous_reversal_policy_v4 as V4
from src.engine.scalping import continuous_reversal_path_postclose as PC
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import continuous_reversal_shared_ledger as L

SCHEMA='continuous_reversal_operating_comparison_v1'


def directory(data_root,day):
    return Path(data_root)/'report/continuous_reversal_operating'/day


def enabled(data_root):
    path=Path(data_root)/'runtime/mechanistic_entry_policy/operating-transition.json'
    if not path.is_file():return False
    r=json.loads(path.read_text())
    if r.get('artifact_content_sha256')!=P.seal(r)['artifact_content_sha256'] or r.get('schema')!='main_operating_transition_authorization_v1':
        raise ValueError('operating_transition_receipt_invalid')
    return r.get('enabled') is True


def active(data_root,day):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    current=N.load_effective(data_root=Path(data_root),target_date=day)
    if (current or {}).get('continuous_reversal',{}).get('schema') in {V5.SCHEMA,'continuous_reversal_policy_v6'} or (enabled(data_root) and (current or {}).get('continuous_reversal',{}).get('schema')==V4.SCHEMA):
        return current
    return None


def proposals(parent, manifest, *, catalog=C):
    C=catalog
    f=parent['continuous_reversal']; result={}
    for key,route in V5.scopes():
        sid=V5.scope_id(key,route)
        ids=sorted(b['branch_id'] for b in f['machine_cells'][key]['routes'][route]['payload']['branches'])
        values=dict(incumbent_native=ids,successor_same=ids,add_all=manifest['scopes'][sid])
        for alias,bid in C.ALIASES.items():
            if C.applicable(bid,key,route):values['add_'+alias]=sorted(set(ids)|{bid})
        result[sid]=values
    return result


def request(snapshot, arm, *, incumbent=None):
    event,source=snapshot
    from src.engine.scalping import reversal_extended_catalog as EC
    from src.engine.scalping import reversal_extended_union as EA
    UNION = EA if event.get("registry_sha256")==EC.SHA256 else globals()["UNION"]
    if incumbent is not None:
        key=C.cell_key(event['symbol'],event['market'],event['confirmation_price']); route=event['venue']
        cell=incumbent['machine_cells'][key]['routes'][route]
        bid=V4.primary(cell,list(event['branch_signals']))
        return PC.request(dict(event_id=event['event_id'],canonical_id=event['canonical_opportunity_id'],
            input=source['branch_inputs'][bid],phase=C.branch(bid)['decision_phase'],event=event['branch_signals'][bid]),arm)
    inp,prompt,schema=UNION.production_request(source,arm,event=event)
    req=dict(paired_replay_parent_id=event['event_id'],micro_reversion_replay_arm=arm,
        offline_provider_attempt_number=1,stage='entry',candidate_input=inp,candidate_input_sha256=P.digest(inp),
        control=dict(provider='openai',model='gpt-5.4-nano'),
        candidate=dict(provider='openai',model='gpt-5.4-nano',prompt_version=UNION.binding(arm)['prompt_version'],
            system_prompt=prompt,response_schema=schema,response_schema_sha256=P.digest(schema),
            schema_name=UNION.VERSION,max_output_tokens=1024,reasoning_effort='none'),**P.AUTH)
    req['paired_replay_id']=P.digest([UNION.opportunity(event),'UNION',{k:req[k] for k in ('candidate_input','candidate','control','stage')}])
    return req


def subset(snapshot, ids):
    event,source=copy.deepcopy(snapshot)
    event['branch_signals']={b:s for b,s in event['branch_signals'].items() if b in ids}
    source['branch_inputs']={b:s for b,s in source['branch_inputs'].items() if b in ids}
    return event,source


def _counter_set(ids):
    return dict(counters={k:Counter() for k in ('union','baseline','common_union','common_baseline','excluded_baseline')},
        individual={b:Counter() for b in ids},exclusive={b:Counter() for b in ids},
        unproven={b:Counter() for b in ids},leave={b:Counter() for b in ids})


def _totals(c):
    out={k:A.metric(v) for k,v in c['counters'].items()}
    out.update({name:{b:A.metric(v) for b,v in c[field].items()} for name,field in
        [('individual','individual'),('exclusive','exclusive'),('exclusive_unproven','unproven'),('leave_one_out','leave')]})
    out['recommendation']=A.recommendation(out['common_baseline'],out['common_union'])
    return out


def machine_report(data_root,day,publication,parent,*,source=None,publish_outputs=True):
    """All retained native ticks, unchanged causal roots and native labels."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    out=directory(data_root,day);(out/'frozen').mkdir(parents=True,exist_ok=True)
    source=source or P.ensure_population(data_root,day)
    if source['artifact_content_sha256']!=P.seal(source)['artifact_content_sha256']:
        raise ValueError('operating_source_manifest_invalid')
    from src.engine.scalping import reversal_extended_registration as ER
    from src.engine.scalping import reversal_extended_state as R
    change=ER.pending(data_root,parent,N.next_target(publication))
    if change or parent['continuous_reversal']['schema']=='continuous_reversal_policy_v6':
        from src.engine.scalping import reversal_extended_catalog as C
        from src.engine.scalping import continuous_reversal_policy_v6 as V5
    else:
        C=globals()['C'];V5=globals()['V5']
    manifest=V5.detector_manifest(parent,effective_date=N.next_target(publication),changes=change)
    configs=proposals(parent,manifest,catalog=C)
    code={Path(m.__file__).name:P.file_hash(m.__file__) for m in V5.contract_modules()}
    # Bind only detection/input execution code, not performance report bytes.
    execution_code=P.digest(code)
    totals={sid:_counter_set(ids) for sid,ids in manifest['scopes'].items()}
    today={sid:_counter_set(ids) for sid,ids in manifest['scopes'].items()}
    per_proposal=defaultdict(Counter)
    proposal_details={sid+'::'+name:_counter_set(ids) for sid,values in configs.items() for name,ids in values.items()}
    partitions=[]; all_masks=[]; source_receipts=[]
    bars={}; input_counts=Counter(); seen={}; canonical={}; conflicts=set(); coverage_counts=defaultdict(Counter)
    with S.Store(data_root) as store:
        store.activation()
        for rec in source['normalized_sources']['partitions']:
            if P.file_hash(rec['path'])!=rec['sha256']:
                raise ValueError('operating_normalized_source_changed')
            market=K.market_bucket(rec['session']);route=rec['venue']
            if route not in C.ROUTES.get(market,()):continue
            if rec['day'] not in bars:
                def sink(path, content):
                    dest=out/'frozen'/('bars-'+__import__('hashlib').sha256(content).hexdigest()+'.json')
                    if not dest.exists():dest.write_bytes(content)
                    return dest
                bars[rec['day']]=P.completed_bars(data_root,rec['day'],snapshot_sink=sink)
                source_receipts+=bars[rec['day']][1]
            fingerprint=P.digest([rec,manifest['detector_manifest_hash'],code,bars[rec['day']][1],C.LABEL,
                                  P.file_hash(__file__),P.file_hash(A.__file__),P.file_hash(R.__file__)])
            cache=store.checkpoint('operating-replay:'+fingerprint)
            if cache:
                records=cache['records'];masks=cache['masks'];local_coverage=cache['coverage']
            else:
                raw=json.loads(gzip.decompress(Path(rec['path']).read_bytes()))['symbols']
                records=[];masks=[];local_coverage=defaultdict(Counter)
                for symbol,rows_all in sorted(raw.items()):
                    from src.engine.scalping.micro_reversion.forward_collector import _explicit_item_venue
                    for item in sorted({r[9] for r in rows_all if isinstance(r[9],str) and r[9].split('_',1)[0]==symbol and _explicit_item_venue(r[9])==route}):
                        rows=[r[:] for r in rows_all]
                        for row in rows:
                            if row[9]!=item:row[8]=0
                        keys=[C.cell_key(symbol,market,1)] if C.group(symbol)=='samsung' else [f'{C.group(symbol)}|{market}|{b}' for b in C.BANDS]
                        ids=sorted({b for key in keys for b in manifest['scopes'][V5.scope_id(key,route)]})
                        state=R.State(branch_ids=ids,registry_sha256=C.SHA256,session_anchor=next((r for r in rows if r[8]),None),offline=True)
                        points=[];previous=None;run=None
                        for index,row in enumerate(rows):
                            ready=state.observe(row,symbol=symbol,venue=route,session=rec['session'])
                            hits=set(ready[0]['event']['branch_signals']) if ready else set()
                            key=C.cell_key(symbol,market,row[3] or 1);sid=V5.scope_id(key,route)
                            applicable=manifest['scopes'][sid]
                            truth=A.coverage(state,row,applicable,hits,previous=previous)
                            for bid,value in truth.items():local_coverage[sid+'|'+bid][value]+=1
                            mask=(sid,tuple(sorted(b for b,v in truth.items() if v=='UNKNOWN')))
                            # Run-length coverage masks, not per-tick JSON facts.
                            if run and (run['scope'],tuple(run['unknown']))==mask and run['end']+1==index:
                                run['end']=index
                            else:
                                run=dict(symbol=symbol,item=item,scope=sid,start=index,end=index,unknown=list(mask[1]));masks.append(run)
                            if ready:
                                snapshot=LIVE.snapshot(state,ready[0]);snapshot=subset(snapshot,applicable)
                                if snapshot[0]['branch_signals']:
                                    points.append(dict(index=index,snapshot=snapshot,truth=truth,scope=sid))
                            state.ready.clear();previous=row
                        times=[r[0] for r in rows];_,ends,valid=K.segments(rows);tree=K.Tree([r[3] if r[8] else None for r in rows])
                        for p in points:
                            event=p['snapshot'][0];label=K.label(rows,times,tree,ends,valid,p['index'],event['entry_ask'])
                            supplement=bars[rec['day']][0].get((rec['day'],item))
                            if supplement and rec.get('cutoff_epoch') is not None:
                                supplement=K.Bars([r for r in supplement.rows if r['t']+60<=rec['cutoff_epoch']])
                            if label['status']=='UNRESOLVED' and event['entry_ask'] is not None and supplement:
                                replacement=supplement.label(event['epoch'],event['entry_ask'],1800)
                                if replacement['status']!='UNRESOLVED':label=dict(replacement,source='same_item_completed_bar_backfill')
                            records.append(dict(opportunity_key=UNION.opportunity(event),native_alias=event['canonical_opportunity_id'],
                                scope=p['scope'],day=rec['day'],symbol=symbol,outcome=label,truth=p['truth'],
                                snapshot_obj=store.put(p['snapshot'])))
                cache=dict(records=records,masks=masks,coverage=local_coverage)
                store.checkpoint('operating-replay:'+fingerprint,cache);store.commit()
            for k,v in local_coverage.items():coverage_counts[k].update(v)
            all_masks.append(dict(normalized_source=rec,masks_object=store.put(masks),mask_count=len(masks)))
            retained=[]
            for p in records:
                identity=p['opportunity_key']; signature=P.digest(p)
                if identity in seen:
                    if seen[identity]!=signature:
                        conflicts.add(identity);canonical.pop(identity,None)
                    input_counts['duplicates']+=1;continue
                seen[identity]=signature;retained.append(p);canonical[identity]=p
            obj=store.put(retained)
            partitions.append(dict(normalized_source=rec,records_object=obj,records_sha256=P.digest(retained),points=len(retained)))
            store.commit()
    input_counts['quarantined_conflicts']=len(conflicts)
    for p in canonical.values():
        sid=p['scope'];ids=manifest['scopes'][sid];baseline=configs[sid]['successor_same'];status=p['outcome']['status']
        for counts in [totals[sid]]+([today[sid]] if p['day']==day else []):
            A.accumulate(counts['counters'],counts['individual'],counts['exclusive'],counts['unproven'],counts['leave'],p['truth'],status,ids,baseline)
        for name,selected in configs[sid].items():
            if any(p['truth'].get(b)=='TRUE' for b in selected):per_proposal[sid+'::'+name][status]+=1
            counts=proposal_details[sid+'::'+name]
            A.accumulate(counts['counters'],counts['individual'],counts['exclusive'],counts['unproven'],counts['leave'],
                p['truth'],status,selected,baseline)
        input_counts['all_confirmations']+=1
        input_counts['outcome_unresolved_no_comparison_request' if status=='UNRESOLVED' else 'resolved_confirmations']+=1
    with N.source_anchor(data_root):
        source_receipts += [dict(path=str(N.source_path(r['path']).absolute()),sha256=r['sha256'])
                            for r in source['normalized_sources']['partitions']]
    report=P.seal(dict(schema=SCHEMA,source_date=day,target_date=day,publication_date=publication,status='completed',
        parent_bundle_sha256=parent['bundle_sha256'],operating_manifest=manifest,execution_code_sha256=execution_code,
        cells=list(copy.deepcopy(parent['continuous_reversal']['machine_cells']).values()),
        membership_status='pending_exact_union_auxiliary_pair',
        source_manifest_sha256=source['artifact_content_sha256'],source_receipts=source_receipts,label_contract=C.LABEL,
        registration_change=change,policy_schema=V5.SCHEMA,
        population='all_retained_native_ticks',observation_mode='confirmation_replay',actual_trades_claimed=False,
        input_census=dict(input_counts),quarantined_conflicts=sorted(conflicts),partitions=partitions,compressed_coverage_masks=all_masks,
        detection_coverage={k:dict(v) for k,v in coverage_counts.items()},fixed_proposals=configs,
        scope_contribution={sid:dict(cumulative=_totals(c),today=_totals(today[sid])) for sid,c in totals.items()},
        proposal_metrics={k:A.metric(v) for k,v in per_proposal.items()},
        proposal_common_range={k:_totals(v) for k,v in proposal_details.items()},
        research_period='retained_clean_baseline_to_source_cutoff',post_registration_observation='replay_not_PID_consumption',
        applied_version_census=PC.applied_census_raw(data_root,day),call_limit=None,**P.AUTH))
    P.write(out/'machine-comparison.json',report)
    if publish_outputs:
        P.write(P.directory(data_root,day)/'machine.json',report)
        standard=Path(data_root)/'report/ai_decision_action_outcome_calibration'
        P.write(standard/f'winrate_policy_{day}.json',report)
        P.write(standard/f'winrate_policy_terminal_{day}.json',P.seal(dict(schema=SCHEMA,source_date=day,target_date=day,status='completed',
            report_sha256=report['artifact_content_sha256'],selection_basis='cumulative_raw_win_fraction',
            disposition='continuous_reversal_selected',policy_sha256=manifest['detector_manifest_hash'],
            staged=dict(status='machine_component_prepared'),**P.AUTH)))
    return report


def prepare_inputs(data_root,day,machine,parent=None):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import reversal_auxiliary_tuning as T
    if T.config(data_root) is not None:
        parent=parent or N.load_effective(data_root=Path(data_root),target_date=machine['publication_date'])
        if parent['continuous_reversal']['schema'] in {V5.SCHEMA,'continuous_reversal_policy_v6'}:
            return T.prepare(data_root,day,machine,parent)
    if machine['artifact_content_sha256']!=P.seal(machine)['artifact_content_sha256']:
        raise ValueError('operating_machine_changed')
    parent=parent or N._read(N.root(Path(data_root))/'generations'/(machine['parent_bundle_sha256']+'.json'))
    native=parent['continuous_reversal'].get('native_parent_bundle',parent)['continuous_reversal']
    out=directory(data_root,day)/'shared-ledger';(out/'frozen').mkdir(parents=True,exist_ok=True)
    gen=machine['artifact_content_sha256'];groups=defaultdict(list);declared=[];counts=Counter();invalid=[]
    path=out/'frozen'/('inputs-v2-'+gen+'.jsonl.gz');tmp=path.with_suffix('.partial')
    with S.Store(data_root) as store:
        store.activation()
        with tmp.open('wb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as handle:
            for part in machine['partitions']:
                points=store.get(part['records_object'])
                if P.digest(points)!=part['records_sha256']:raise ValueError('operating_partition_changed')
                for p in points:
                    if p['opportunity_key'] in set(machine.get('quarantined_conflicts',[])) or p['outcome']['status']=='UNRESOLVED':continue
                    snapshot=store.get(p['snapshot_obj']);sid=p['scope']
                    for name,ids in machine['fixed_proposals'][sid].items():
                        selected=subset(snapshot,ids)
                        if not selected[0]['branch_signals']:continue
                        comp=sid+'::'+name
                        counts['eligible_inputs']+=1
                        reqs={}
                        key,route=sid.rsplit('|',1)
                        parent_cell=parent['continuous_reversal']['machine_cells'][key]['routes'][route]
                        is_native=(name=='incumbent_native' and parent_cell.get('backend','registered_v4')=='registered_v4')
                        native_arm=None
                        if name=='incumbent_native':
                            ap=parent['continuous_reversal']['auxiliary_cells'][key]['routes'][route]['payload']
                            native_arm=ap['branch_policies'][V4.primary(native['machine_cells'][key]['routes'][route],list(selected[0]['branch_signals']))]['arm'] if is_native else ap['arm']
                        try:
                            for arm in V1.ARMS:
                                reqs[arm]=request(selected,arm,incumbent=native if is_native else None)
                        except (ValueError,KeyError,TypeError) as exc:
                            invalid.append(dict(comparison=comp,opportunity=p['opportunity_key'],reason=str(exc)))
                            continue
                        refs={}
                        for arm,req in reqs.items():
                            rid,_=store.add_request(req,priority=4 if name=='add_all' else 2)
                            mid=store.add_member(comp,p['opportunity_key'],arm,rid,p['outcome']['status'])
                            refs[arm]=rid
                            groups[json.dumps([comp,p['day'],p['symbol']],separators=(',',':'))].append(mid)
                        small=dict(comparison=comp,canonical_id=p['opportunity_key'],branch_id='operating_union',
                            owners=[name],outcome=p['outcome'],requests=refs,objects=dict(snapshot=p['snapshot_obj']),
                            native_selected_arm=native_arm)
                        declared.append(dict(comparison=comp,canonical_id=p['opportunity_key'],branch_id='operating_union',owners=[name],outcome=p['outcome']))
                        handle.write(S.encode(small)+b'\n');counts['prepared_inputs']+=1
                        if counts['prepared_inputs']%500==0:store.commit()
        expected=L.owner_census(declared)
        universe=P.seal(dict(schema=SCHEMA,machine_report_sha256=gen,**expected,**P.AUTH))
        P.write(out/'frozen'/('universe-'+gen+'.json'),universe)
        store.bind_generation(gen,groups,dict(machine_report_sha256=gen,expected=expected,universe_sha256=universe['artifact_content_sha256']),expected['expected_requests'])
        store.commit();states=store.states(gen)
        if path.exists() and P.file_hash(path)!=P.file_hash(tmp):raise ValueError('operating_prepared_inputs_changed')
        os.replace(tmp,path)
        manifest=P.seal(dict(schema=SCHEMA,machine_report_sha256=gen,input_sha256=P.file_hash(path),
            universe_sha256=universe['artifact_content_sha256'],**expected,**P.AUTH))
        P.write(out/'frozen'/('expected-'+gen+'.json'),manifest)
        result=P.seal(dict(schema=SCHEMA,source_date=day,machine_report_sha256=gen,input_refs_version=2,
            input_path=str(path.resolve()),input_sha256=P.file_hash(path),input_generation_sha256=P.digest([P.file_hash(UNION.__file__),P.file_hash(__file__)]),
            source_receipts=[],expected_manifest_sha256=manifest['artifact_content_sha256'],
            census=dict(expected_owner_requests=expected['expected_requests'],eligible_requests=expected['expected_requests'],**states),
            input_census=dict(counts,input_invalid=len(invalid)),input_exclusions=invalid,call_limit=None,status='prepared',**P.AUTH))
        P.write(out/'input-census.json',result)
        L.validate_membership(store,result)
    return result


def calls(data_root,day,*,stop_epoch=None,workers=4,transport=None):
    from src.engine.scalping import reversal_auxiliary_tuning as T
    if T.config(data_root) is not None:
        return T.calls(data_root,day,stop_epoch=stop_epoch,transport=transport)
    return L.calls(sys.modules[__name__],data_root,day,stop_epoch=stop_epoch,workers=workers,transport=transport)


def comparison_metrics(store,snapshot):
    metrics=defaultdict(lambda:{a:Counter() for a in V1.ARMS});gaps=Counter();expected=Counter();states=Counter();validation_refs=[]
    verdicts=defaultdict(dict)
    for _,obj in sorted(snapshot['partitions'].items()):
        owners=defaultdict(list)
        for mid,state,result in store.get(obj):
            row=store.db.execute('''SELECT c.value,o.value,a.value,m.outcome,m.request_id FROM members m
              JOIN strings c ON c.id=m.comparison JOIN strings o ON o.id=m.opportunity JOIN strings a ON a.id=m.arm WHERE m.id=?''',(mid,)).fetchone()
            owners[row[:2]].append((row[2],row[3],row[4],state,result));states[state]+=1
        for (comp,opportunity),records in owners.items():
            expected[comp]+=1
            if len(records)!=5 or {r[0] for r in records}!=set(V1.ARMS) or any(r[3]!='completed' or not r[4] for r in records):
                gaps[comp]+=1;continue
            validated=[]
            for arm,outcome,rid,_,result_obj in records:
                req=store.request(rid);result=store.get(result_obj)
                response=result.get('result',{}).get('candidate_response')
                try:errors=A.validate_response(response,req['candidate_input'],arm=arm,phase=req['candidate_input'].get('observation_phase',{}).get('stage',B.FIRST))
                except (ValueError,TypeError,KeyError):errors=['invalid_response']
                validation_refs.append(store.put(dict(request_id=rid,response_obj=result_obj,
                    validator_sha256=P.digest([P.file_hash(A.__file__),P.file_hash(UNION.__file__)]),errors=errors)))
                validated.append((arm,outcome,response,errors))
            # A failure on any fixed arm removes the point from ALL arm ranks.
            if any(v[3] for v in validated):gaps[comp]+=1;continue
            for arm,outcome,response,_ in validated:
                m=metrics[comp][arm];m['points']+=1;m['outcome_'+outcome]+=1
                verdicts[comp].setdefault(opportunity,dict(outcome=outcome,arms={}))['arms'][arm]=response['risk_verdict']
                if response['risk_verdict']=='PASS':m['pass_count']+=1;m['pass_wins']+=outcome=='WIN'
                else:m['excluded_'+outcome]+=1
    return metrics,gaps,expected,states,validation_refs,verdicts


def auxiliary_contribution(machine,census,verdicts,gaps):
    """Native incumbent binding vs changed exact union responses, no OR fiction."""
    actual={};result={}
    with gzip.open(census['input_path'],'rt') as handle:
        for line in handle:
            p=json.loads(line)
            if p.get('native_selected_arm'):
                actual[p['comparison'],p['canonical_id']]=p['native_selected_arm']
    for sid,configs in machine['fixed_proposals'].items():
        baseline=sid+'::incumbent_native'
        base_rows=verdicts.get(baseline,{})
        base_pass={key:row['outcome'] for key,row in base_rows.items() if row['arms'][actual[baseline,key]]=='PASS'}
        for name in configs:
            if name=='incumbent_native':continue
            comp=sid+'::'+name
            incomplete=bool(gaps[baseline] or gaps[comp] or any(x['comparison'] in {baseline,comp} for x in census['input_exclusions']))
            candidates={}
            for arm in V1.ARMS:
                points={key:row['outcome'] for key,row in verdicts.get(comp,{}).items() if row['arms'][arm]=='PASS'}
                gained=Counter(v for k,v in points.items() if k not in base_pass)
                lost=Counter(v for k,v in base_pass.items() if k not in points)
                old_metric=A.metric(Counter(base_pass.values()));new_metric=A.metric(Counter(points.values()))
                ai_recommendation='incomplete' if incomplete else A.recommendation(old_metric,new_metric)
                machine_recommendation=machine['proposal_common_range'][comp]['recommendation']
                candidates[arm]=dict(status='incomplete' if incomplete else 'completed',
                    actual_incumbent_pass=old_metric,union_pass=new_metric,
                    added_pass=None if incomplete else A.metric(gained),excluded_pass=None if incomplete else A.metric(lost),
                    recommendation=ai_recommendation,
                    machine_auxiliary_tradeoff=(not incomplete and machine_recommendation not in {'keep_current','not_comparable'} and ai_recommendation=='keep_current'))
            result[comp]=candidates
    return result


def initial_registration(data_root, day, publication, parent, machine):
    """Apply the designated first list; comparison is subsequent diagnostics."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    path=Path(data_root)/'runtime/mechanistic_entry_policy/operating-transition.json'
    if not path.exists():return None
    authorization=json.loads(path.read_text())
    if (authorization.get('schema')!='main_operating_transition_authorization_v1'
            or authorization.get('artifact_content_sha256')!=P.seal(authorization)['artifact_content_sha256']):
        raise ValueError('initial_registration_authorization_invalid')
    if authorization.get('enabled') is not True or authorization.get('source_date')!=day:return None
    if (authorization.get('target_date')!=N.next_target(publication)
            or authorization.get('parent_bundle_sha256')!=parent['bundle_sha256']
            or authorization.get('approved_by')!='user_operating_policy_implementation_resume_postclose_prepare_next_start'
            or machine['operating_manifest']['scopes']!=V5.wanted(parent)):
        raise ValueError('initial_registration_scope_or_parent_invalid')
    bindings={}
    family=parent['continuous_reversal']
    for key,route in V5.scopes():
        source_key=key.replace('|PRE|','|REGULAR|').replace('|AFTER|','|REGULAR|')
        cell=family['machine_cells'][source_key]['routes'][route]
        auxiliary=family['auxiliary_cells'][source_key]['routes'][route]['payload']
        if cell.get('backend')=='union_v5':arm=auxiliary['arm']
        else:
            bid=V4.primary(cell,[b['branch_id'] for b in cell['payload']['branches']])
            arm=auxiliary['branch_policies'][bid]['arm']
        UNION.binding(arm)
        bindings[V5.scope_id(key,route)]=dict(arm=arm,source_scope=V5.scope_id(source_key,route))
    frozen=L.freeze_receipt(directory(data_root,day)/'shared-ledger',path)
    if json.loads(Path(frozen['path']).read_text())!=authorization:
        raise ValueError('initial_registration_authorization_changed')
    return dict(authorization_source=frozen,
        parent_bundle_sha256=parent['bundle_sha256'],bindings=bindings,
        adoption_basis='operator_designated_initial_registration',comparison_result_required=False)


def initial_protocol_evidence(store, snapshot, required):
    """Check each binding's real response independently of labels/other arms."""
    evidence={};seen=set()
    for _,obj in sorted(snapshot['partitions'].items()):
        for mid,state,result_obj in store.get(obj):
            if state!='completed' or not result_obj:continue
            rid=store.db.execute('SELECT request_id FROM members WHERE id=?',(mid,)).fetchone()[0]
            if rid in seen:continue
            seen.add(rid);req=store.request(rid);arm=req['micro_reversion_replay_arm']
            if arm not in required or arm in evidence:continue
            if req['candidate_input'].get('schema')!=UNION.VERSION:continue
            if req['candidate'].get('prompt_version')!=UNION.binding(arm)['prompt_version']:continue
            result=store.get(result_obj).get('result',{})
            response_id=result.get('provider_provenance',{}).get('response_id')
            try:errors=A.validate_response(result.get('candidate_response'),req['candidate_input'],arm=arm)
            except (ValueError,KeyError,TypeError):continue
            if errors or not response_id:continue
            evidence[arm]=dict(request_identity=req['paired_replay_id'],response_id=response_id,
                request_id=rid,response_object=result_obj,
                validation_role='protocol_only_not_performance',binding=UNION.binding(arm))
            if set(evidence)==required:return evidence
    raise ValueError('initial_union_protocol_response_evidence_missing')


def auxiliary_report(data_root,day,publication,parent,*,publish_policy=True):
    machine=json.loads((directory(data_root,day)/'machine-comparison.json').read_text())
    if machine.get('registration_change'):
        from src.engine.scalping.reversal_extended_registration import initial_reports
        return initial_reports(data_root,day,publication,parent,machine,publish_policy=publish_policy)
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import reversal_auxiliary_tuning as T
    if parent['continuous_reversal']['schema']=='continuous_reversal_policy_v6' or (T.config(data_root) is not None and parent['continuous_reversal']['schema']==V5.SCHEMA):
        return T.auxiliary_report(data_root,day,publication,parent,publish_policy=publish_policy)
    out=directory(data_root,day);ledger=out/'shared-ledger'
    machine=json.loads((out/'machine-comparison.json').read_text());gen=machine['artifact_content_sha256']
    initial=initial_registration(data_root,day,publication,parent,machine)
    with S.Store(data_root) as store:
        census,declared,_=L.validate_census(ledger);L.validate_membership(store,census)
        if census['machine_report_sha256']!=gen:raise ValueError('operating_comparison_generation_changed')
        store.activation();store.reconcile();snap=store.snapshot(gen)
        metrics,gaps,expected,states,validations,verdicts=comparison_metrics(store,snap)
        if initial:
            initial['binding_contract_evidence']=initial_protocol_evidence(
                store,snap,{b['arm'] for b in initial['bindings'].values()})
        contribution=auxiliary_contribution(machine,census,verdicts,gaps)
        evidence=L.response_evidence(store,ledger,snap)
        revision=P.seal(dict(snapshot=snap,validation_objects=validations,metrics=metrics,gaps=gaps,expected=expected,states=states,
            verdicts_object=store.put(verdicts),auxiliary_contribution=contribution))
        revision_path=ledger/'frozen'/('comparison-'+revision['artifact_content_sha256']+'.json');P.write(revision_path,revision)
        receipts=[L.freeze_receipt(ledger,p) for p in (ledger/'input-census.json',ledger/'frozen'/('expected-'+gen+'.json'),ledger/'frozen'/('universe-'+gen+'.json'),revision_path)]
    native=parent['continuous_reversal'].get('native_parent_bundle',parent)['continuous_reversal']
    machine_cells=copy.deepcopy(native['machine_cells']);aux_cells=copy.deepcopy(native['auxiliary_cells'])
    proof=dict(path=str(evidence.resolve()),sha256=P.file_hash(evidence));pending=[];new=0;regular={}
    invalid=Counter(r['comparison'] for r in census['input_exclusions'])
    for key,route in sorted(V5.scopes(),key=lambda v:('|REGULAR|' not in v[0],v)):
        sid=V5.scope_id(key,route);comp=sid+'::add_all';count=declared['comparisons'].get(comp,0)
        old_family=parent['continuous_reversal'];old_cell=old_family['machine_cells'][key]['routes'][route]
        old_aux=old_family['auxiliary_cells'][key]['routes'][route]
        eligible=[a for a in V1.TIE_ORDER if metrics[comp][a]['pass_count']]
        arm=None;inherit=None
        if initial:
            binding=initial['bindings'][sid];arm=binding['arm']
            inherit=binding['source_scope'].rsplit('|',1)[0] if binding['source_scope']!=sid else None
        elif count and not gaps[comp] and not invalid[comp] and eligible:
            prior_arm=old_aux['payload'].get('arm')
            arm=max(eligible,key=lambda a:(Fraction(metrics[comp][a]['pass_wins'],metrics[comp][a]['pass_count']),
                metrics[comp][a]['pass_count'] if metrics[comp][a]['pass_wins'] else 0,a==prior_arm,-V1.TIE_ORDER.index(a)))
        elif not count and not invalid[comp]:
            regular_key=key.replace('|PRE|','|REGULAR|').replace('|AFTER|','|REGULAR|')
            entry=regular.get((regular_key,route))
            # The common-opportunity binding supports every registered typed
            # signal; PRE/AFTER retain their own manifest, never REGULAR's IDs.
            if entry:arm=entry['arm'];inherit=regular_key
        if arm:
            ids=machine['operating_manifest']['scopes'][sid];payload=B.payload([C.branch(b) for b in ids])
            mc=dict(payload=payload,payload_sha256=P.digest(payload),backend='union_v5',
                    status='operator_initial_registered' if initial else 'operating_registered')
            ap=dict(arm=arm,binding=UNION.binding(arm))
            ac=dict(payload=ap,payload_sha256=P.digest(ap),actual_response_evidence=[proof],
                    comparison_key=comp,local_metrics=dict(metrics[comp][arm]) if not inherit and not initial else None,inherited_from=inherit)
            if initial:ac['initial_binding']=dict(initial['bindings'][sid],
                adoption_basis=initial['adoption_basis'],comparison_result_required=False,
                response_evidence_role='shared_union_protocol_validation_not_scope_performance')
            new+=1
            if '|REGULAR|' in key:regular[key,route]=dict(ids=ids,arm=arm)
        elif old_family['schema']==V5.SCHEMA and old_cell['backend']=='union_v5':
            mc=copy.deepcopy(old_cell);ac=copy.deepcopy(old_aux);mc['status']='verified_union_pair_carried'
            new+=1
        else:
            mc=copy.deepcopy(machine_cells[key]['routes'][route]);ac=copy.deepcopy(aux_cells[key]['routes'][route])
            mc.update(backend='registered_v4',status='native_pair_carried')
            pending.append(dict(scope=sid,reason='input_invalid' if invalid[comp] else 'evaluation_incomplete' if gaps[comp] else 'completed_no_pass' if count else 'no_compatible_union_binding',
                expected=count,missing_or_invalid=gaps[comp],pending_ids=machine['operating_manifest']['scopes'][sid]))
        ids=[b['branch_id'] for b in mc['payload']['branches']]
        mc['scope_execution_hash']=V5.scope_hash(ids,ac['payload'],mc['backend'],machine['execution_code_sha256'])
        machine_cells[key]['routes'][route]=mc;aux_cells[key]['routes'][route]=ac
    comparison_path=out/'frozen'/('machine-'+gen+'.json');P.write(comparison_path,machine)
    issued=P.seal(dict(machine,cells=list(machine_cells.values()),comparison_report_sha256=gen,
        membership_status='registered',registration_state='registered',
        adoption_basis='operator_designated' if initial else 'carried' if pending else 'comparison_selected',
        source_receipts=machine['source_receipts']+receipts+[dict(path=str(comparison_path.resolve()),sha256=P.file_hash(comparison_path))]
            +([initial['authorization_source']] if initial else []),
        initial_registration=initial,
        status='completed_with_scope_carry' if pending else 'completed',scope_pending=pending))
    statuses={}
    for sid,configs in machine['fixed_proposals'].items():
        for name in configs:
            comp=sid+'::'+name
            if invalid[comp]:status='input_invalid'
            elif gaps[comp]:status='incomplete'
            elif declared['comparisons'].get(comp):status='completed' if any(metrics[comp][a]['pass_count'] for a in V1.ARMS) else 'completed_no_pass'
            elif machine['proposal_metrics'].get(comp,{}).get('unresolved'):status='completed_unresolved'
            else:status='valid_empty' if any(k.startswith(sid+'|') for k in machine['detection_coverage']) else 'source_gap'
            statuses[comp]=status
    auxiliary=P.seal(dict(schema=SCHEMA,source_date=day,target_date=day,publication_date=publication,
        status=issued['status'],cells=list(aux_cells.values()),machine_report_sha256=issued['artifact_content_sha256'],
        results_sources=[proof],source_receipts=receipts,comparison_complete=not gaps and not invalid,
        scope_pending=pending,scope_census=dict(planned=len(V5.scopes()),new_ready=new,new_actual_pid_consumed=0,native_carried=len(pending),contract_gaps=0),
        comparison_metrics=metrics,comparison_statuses=statuses,
        initial_registration=initial,
        auxiliary_contribution=contribution,
        owner_request_census=dict(expected=declared['expected_requests'],missing=declared['expected_requests']-sum(states.values()),**states),
        incomplete_comparisons=dict(gaps),observation_mode='confirmation_replay',
        call_limit=L.POSTCLOSE_DAILY_CALL_LIMIT,
        **P.AUTH))
    P.write(out/'machine.json',issued);P.write(out/'auxiliary.json',auxiliary)
    if publish_policy:
        P.write(P.directory(data_root,day)/'auxiliary.json',auxiliary)
        P.write(P.directory(data_root,day)/'call-freeze.json',P.seal(dict(schema=SCHEMA,source_date=day,status='frozen',
            machine_report_sha256=gen,call_limit=L.POSTCLOSE_DAILY_CALL_LIMIT,census=census['census'],input_sha256=census['input_sha256'],**P.AUTH)))
        # Compatibility consumer gets only actual chosen responses; no request DB copy.
        with gzip.open(evidence,'rt') as src,(P.directory(data_root,day)/'provider-results.jsonl').open('w') as dst:
            for line in src:dst.write(line)
        commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        bundle=V5.stage(data_root,day,publication,issued,auxiliary,target_date=N.next_target(publication),release_commit=commit)
        P.write(Path(data_root)/'report/ai_entry_setup_paired_replay_batch'/f'compact_auxiliary_paired_economic_{day}.json',
            P.seal(dict(auxiliary,staged=dict(status='prepared',bundle_sha256=bundle['bundle_sha256'],target_date=bundle['target_date']))))
    return auxiliary
