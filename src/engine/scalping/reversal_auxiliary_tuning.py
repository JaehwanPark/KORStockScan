"""Bounded current/challenger comparisons in the shared offline ledger.

The machine population remains complete; only a sealed, outcome-independent
sample owns provider requests. This module cannot place orders.
"""
from __future__ import annotations

import argparse
import copy
import json
import time
from collections import Counter, defaultdict
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from src.engine.ai import offline_comparison_store as S
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_auxiliary_registry as G

SCHEMA = 'main_auxiliary_paired_tuning_v1'
LIMIT = 100


def root(data_root):
    return Path(data_root)/'runtime/mechanistic_entry_policy/auxiliary'


def directory(data_root, day):
    return Path(data_root)/'report/reversal_auxiliary_tuning'/day


def read(path):
    value = json.loads(Path(path).read_text())
    if value.get('artifact_content_sha256') != P.seal(value)['artifact_content_sha256']:
        raise ValueError('auxiliary_tuning_artifact_changed')
    return value


def config(data_root):
    path = root(data_root)/'tuning.json'
    if not path.exists():
        return None
    v = read(path)
    if (v.get('schema') != SCHEMA or v.get('enabled') is not True
            or not isinstance(v.get('scopes'), list) or not v['scopes']
            or len(set(v['scopes'])) != len(v['scopes'])
            or type(v.get('max_pairs')) is not int or not 1 <= v['max_pairs'] <= 100
            or not isinstance(v.get('seed'), str) or not v['seed']):
        raise ValueError('auxiliary_tuning_config_invalid')
    G.load(data_root, v['candidate_registry'])
    return v


def configure(data_root, *, candidate, scopes, seed, max_pairs=50):
    from src.engine.scalping import continuous_reversal_policy_v5 as V
    valid = {V.scope_id(k,r) for k,r in V.scopes()}
    if not set(scopes) <= valid:
        raise ValueError('auxiliary_tuning_scope_invalid')
    G.load(data_root, candidate)
    body = P.seal(dict(schema=SCHEMA, enabled=True, candidate_registry=candidate,
                       scopes=sorted(set(scopes)), seed=seed, max_pairs=max_pairs))
    if type(max_pairs) is not int or not 1 <= max_pairs <= 100 or not scopes or not seed:
        raise ValueError('auxiliary_tuning_config_invalid')
    import fcntl
    folder = root(data_root)
    folder.mkdir(parents=True, exist_ok=True)
    with (folder/'tuning-config.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        P.write(folder/'tuning.json', body)
    return body


def rebind_candidate_input(data_root, *, input_version, expected_config_sha256):
    """Explicit source-only repair of an unchanged prompt's typed binding.

    Never translate wording, reset budgets, change scope or select a live arm.
    A different shared prompt contract requires a separately reviewed candidate.
    """
    import fcntl
    folder = root(data_root)
    folder.mkdir(parents=True, exist_ok=True)
    with (folder/'tuning-config.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        previous = config(data_root)
        if previous is None or previous['artifact_content_sha256'] != expected_config_sha256:
            raise ValueError('auxiliary_tuning_config_parent_changed')
        value = G.load(data_root, previous['candidate_registry'])
        old, new = G.projector(value['input_version']), G.projector(input_version)
        if (value['schema'] != G.SCHEMA or old.VERSION == new.VERSION
                or old.PROMPT != new.PROMPT or old.ARM_SUFFIXES != new.ARM_SUFFIXES
                or not value['prompt'].startswith(old.PROMPT)
                or old.VERSION in value['prompt']):
            raise ValueError('auxiliary_candidate_prompt_contract_rebind_unsupported')
        replacement = G.definition(value['base_arm'], prompt=value['prompt'],
            hypothesis=value['hypothesis'], development_keys=value['development_keys'],
            input_version=input_version)
        G.register(data_root, replacement)
        updated = P.seal(dict(previous, candidate_registry=replacement['registry_sha256']))
        receipt = P.seal(dict(schema='main_auxiliary_input_rebinding_v1',
            previous_config=previous, successor_config=updated,
            unchanged_fields=['prompt','base_arm','hypothesis','development_keys','scopes','seed','max_pairs'],
            previous_registry=value['registry_sha256'], successor_registry=replacement['registry_sha256'],
            previous_input_version=old.VERSION, successor_input_version=new.VERSION,
            budget_reset=False, live_policy_changed=False, **P.AUTH))
        path = folder/'input-rebindings'/(receipt['artifact_content_sha256']+'.json')
        if path.exists() and read(path) != receipt:
            raise ValueError('auxiliary_input_rebinding_receipt_conflict')
        P.write(path, receipt)
        P.write(folder/'tuning.json', updated)
        return receipt


def prepare(data_root, day, machine, parent, *, research=None):
    from src.engine.scalping import reversal_auxiliary_intraday as I
    context = None
    out = directory(data_root, day)
    if research is not None:
        from src.engine.scalping import reversal_auxiliary_research as R
        context = R.context(data_root, research)
        cfg = context['config']
        out = R.directory(data_root, research)
    else:
        cfg = config(data_root)
    if cfg is None:
        raise ValueError('auxiliary_tuning_not_configured')
    if machine.get('artifact_content_sha256') != P.seal(machine)['artifact_content_sha256'] or machine.get('source_date')!=day:
        raise ValueError('auxiliary_machine_report_changed')
    if machine['operating_manifest']['scopes'] != parent['continuous_reversal']['operating_manifest']['scopes'] and not machine.get('registration_change'):
        raise ValueError('auxiliary_tuning_machine_membership_changed')
    # Current identities are frozen before looking at outcomes or responses.
    current = R.current_bindings(data_root,parent) if context else I.effective_bindings(data_root,parent,day=day)
    candidate = G.load(data_root, cfg['candidate_registry'])
    excluded = set(candidate['development_keys']) | set(machine.get('quarantined_conflicts', []))
    choices = defaultdict(list); census = Counter(); seen = {}; conflicting = set()
    with S.Store(data_root) as store:
        store.activation()
        prep_key='auxiliary-prepare:'+P.digest([day,machine['artifact_content_sha256'],parent['bundle_sha256'],current,cfg,context,P.file_hash(__file__)])
        cached=store.checkpoint(prep_key)
        if cached:
            validate_campaign(store,cached)
            P.write(out/'latest-campaign.json',cached)
            return cached
        for part in machine['partitions']:
            points = store.get(part['records_object'])
            if P.digest(points) != part['records_sha256']:
                raise ValueError('auxiliary_tuning_partition_changed')
            for p in points:
                ident = p['opportunity_key']
                if ident in seen:
                    if P.digest(seen[ident]) != P.digest(p):
                        conflicting.add(ident)
                    continue
                seen[ident] = p
        for ident, p in seen.items():
            census['eligible_universe'] += 1
            census['outcome_'+p['outcome']['status']] += 1
            if ident in excluded or ident in conflicting:
                census['development_or_source_excluded'] += 1
                continue
            if context and cfg.get('resolved_only') and p['outcome']['status'] not in {'WIN','FAIL_STOP','FAIL_TIMEOUT'}:
                census['outcome_not_evaluable'] += 1
                continue
            if context and context['include_keys'] and ident not in context['include_keys']:
                continue
            if p['scope'] in cfg['scopes'] and p['scope'] in current:
                version=G.load(data_root,current[p['scope']])['input_version']
                if machine.get('policy_schema')=='continuous_reversal_policy_v6':
                    from src.engine.scalping import reversal_extended_union as EA
                    if version!=EA.VERSION or candidate['input_version']!=EA.VERSION:
                        census['typed_candidate_incompatible']+=1;continue
                choices[p['scope']].append((P.digest([cfg['seed'], ident]), p))
        for values in choices.values():
            values.sort(key=lambda v:v[0])
        # Source-day rotation; scope and within-scope selection ignore labels.
        scopes = sorted(choices, key=lambda s:P.digest([cfg['seed'],day,s]))
        selected = []
        for index in range(cfg['max_pairs']):
            for sid in scopes:
                if index < len(choices[sid]):
                    selected.append(choices[sid][index][1])
                    if len(selected) == cfg['max_pairs']:
                        break
            if len(selected) == cfg['max_pairs']:
                break
        selector = dict(seed=cfg['seed'], scope_order=scopes, method='scope_round_robin_sha256',
                        scope_population={s:len(v) for s,v in choices.items()},
                        selected_keys=[p['opportunity_key'] for p in selected])
        cumulative_keys={sid:'auxiliary-membership:'+P.digest([sid,cfg['candidate_registry'],current[sid],cfg['seed'],'confirmation_replay']+([context] if context else [])) for sid in scopes}
        previous=[ident for key in cumulative_keys.values() for ident in (store.checkpoint(key) or [])]
        retained={p['opportunity_key']:p for p in selected}
        eligible_keys={p['opportunity_key'] for values in choices.values() for _,p in values}
        for ident in previous:
            if ident in eligible_keys:
                retained[ident]=seen[ident]
            elif ident not in seen:census['previous_source_unavailable']+=1
        selected_all=sorted(retained.values(),key=lambda p:(p['day'],p['scope'],p['opportunity_key']))
        selector['cumulative_selected_keys']=[p['opportunity_key'] for p in selected_all]
        pairs = []; groups = defaultdict(list)
        for p in selected_all:
            sid = p['scope']; old = current[sid]
            snap = store.get(p['snapshot_obj'])
            pair = dict(scope=sid, opportunity_key=p['opportunity_key'], day=p['day'], symbol=p['symbol'],
                        snapshot_obj=p['snapshot_obj'], outcome=p['outcome'],
                        current_registry=old, candidate_registry=cfg['candidate_registry'], requests={})
            comp = 'aux-pair:'+P.digest([sid,old,cfg['candidate_registry'],'confirmation_replay'])
            for role, registry in [('current',old),('candidate',cfg['candidate_registry'])]:
                definition = G.load(data_root, registry)
                req = (R.request(snap, definition, cfg.get('native_current_contract'),
                                 output_tokens_override=cfg.get('native_output_tokens_override'))
                       if context and role == 'current' and definition['schema']!=G.SCHEMA_V2 else G.request(snap, definition))
                if context and definition['schema']!=G.SCHEMA_V2 and cfg.get('compact_wire_contract') and (role == 'candidate' or not cfg.get('compact_candidate_only')):
                    from src.engine.scalping import reversal_auxiliary_research_wire as W
                    req=W.request(req,G.production_request(snap,definition)[0],cfg['compact_wire_contract'])
                rid,_ = store.add_request(req)
                mid = store.add_member(comp,p['opportunity_key'],role,rid,p['outcome']['status'])
                pair['requests'][role] = rid
                groups[json.dumps([comp,p['day'],p['symbol']],separators=(',',':'))].append(mid)
            pairs.append(pair)
        body = dict(schema=SCHEMA, source_date=day, parent_bundle_sha256=parent['bundle_sha256'],
                    machine_report_sha256=machine['artifact_content_sha256'],
                    detector_manifest_hash=machine['operating_manifest']['detector_manifest_hash'],
                    config_sha256=cfg['artifact_content_sha256'], selector=selector,
                    eligible_census=dict(census), not_sampled_budget=sum(map(len,choices.values()))-len(selected_all),
                    pairs=pairs, expected_pairs=len(pairs), expected_owner_requests=2*len(pairs),
                    observation_mode='confirmation_replay', call_limit=LIMIT, **P.AUTH)
        if context:
            body['research'] = {k:context[k] for k in ('research_id','experiment','purpose','allowance_sha256')}
            body['call_limit'] = R.budget(data_root)['call_limit']
            R.validate_campaign(data_root, body)
        campaign = P.seal(body); gen = campaign['artifact_content_sha256']
        store.bind_generation(gen,groups,body,2*len(pairs)); store.commit()
        for sid,key in cumulative_keys.items():
            store.checkpoint(key,[p['opportunity_key'] for p in selected_all if p['scope']==sid])
        store.checkpoint(prep_key,campaign);store.commit()
    P.write(out/'campaigns'/(gen+'.json'), campaign)
    P.write(out/'latest-campaign.json', campaign)
    return campaign


def validate_campaign(store, campaign):
    if campaign.get('artifact_content_sha256') != P.seal(campaign)['artifact_content_sha256'] or campaign.get('schema') != SCHEMA:
        raise ValueError('auxiliary_campaign_changed')
    rows = list(store.owners(campaign['artifact_content_sha256']))
    expected = {(p['opportunity_key'],role,rid,p['outcome']['status']) for p in campaign['pairs'] for role,rid in p['requests'].items()}
    actual = {(r[1],r[2],r[6],r[3]) for r in rows}
    if len(rows) != campaign['expected_owner_requests'] or actual != expected:
        raise ValueError('auxiliary_pair_membership_changed')
    return rows


def load_campaign(data_root, day, campaign_path=None):
    c = read(campaign_path or directory(data_root,day)/'latest-campaign.json')
    if c.get('source_date') != day:
        raise ValueError('auxiliary_campaign_source_date_changed')
    out = directory(data_root,day)
    if c.get('research'):
        from src.engine.scalping import reversal_auxiliary_research as R
        R.validate_campaign(data_root,c)
        out = R.directory(data_root,c['research']['experiment'])
    canonical = out/'campaigns'/(c['artifact_content_sha256']+'.json')
    if read(canonical) != c:
        raise ValueError('auxiliary_campaign_canonical_changed')
    return c, out, canonical


def expected_request(data_root, campaign, pair, role, snapshot, registry):
    req = G.request(snapshot,registry)
    if campaign.get('research') and registry['schema']!=G.SCHEMA_V2:
        from src.engine.scalping import reversal_auxiliary_research as R
        cfg = R.context(data_root,campaign['research']['experiment'])['config']
        if role == 'current':
            req = R.request(snapshot,registry,cfg.get('native_current_contract'),
                             output_tokens_override=cfg.get('native_output_tokens_override'))
        if cfg.get('compact_wire_contract') and (role == 'candidate' or not cfg.get('compact_candidate_only')):
            from src.engine.scalping import reversal_auxiliary_research_wire as W
            req = W.request(req,G.production_request(snapshot,registry)[0],cfg['compact_wire_contract'])
    return req


def response_projection(result, req, logical_input, registry):
    from src.engine.scalping import reversal_auxiliary_research_wire as W
    try:
        if registry['schema']==G.SCHEMA_V2:
            from src.engine.scalping import reversal_auxiliary_wire as W
        response=W.response(result,req,logical_input,registry['base_arm'])
    except ValueError as exc:
        return None,[str(exc)]
    errors=G.projector(registry['input_version']).validate_response(response,logical_input,arm=registry['base_arm'])
    return response,errors


def calls(data_root, day, *, stop_epoch=None, transport=None, campaign_path=None, max_new_calls=None):
    from src.engine.scalping import continuous_reversal as K
    c, out, _ = load_campaign(data_root,day,campaign_path); sent=0
    if max_new_calls is not None and (type(max_new_calls) is not int or max_new_calls < 0):
        raise ValueError('auxiliary_batch_limit_invalid')
    research_grant = None
    if c.get('research'):
        from src.engine.scalping import reversal_auxiliary_research as R
        research_grant = R.validate_campaign(data_root,c)
    limit = research_grant['call_limit'] if research_grant else LIMIT
    if transport is None:
        from src.engine.scalping.ai_decision_quality import execute_openai_prompt_v2_candidate
        transport = execute_openai_prompt_v2_candidate
    with S.Store(data_root) as store:
        validate_campaign(store,c); store.reconcile()
        fence = store.activation()['writer_epoch']; key='postclose_auxiliary:'+day
        if research_grant:
            key = research_grant['budget_key']
        else:
            store.seed_call_budget(c['artifact_content_sha256'],key,
                since_epoch=datetime.fromisoformat(day).replace(tzinfo=K.KST).timestamp(),
                exclude_assigned_prefix='postclose_auxiliary:')
        before = store.budget_used(key); origin_keys=set()
        pairs=c['pairs']
        if research_grant:
            # Preserve the pre-outcome scope rotation when the budget ends
            # early. Canonical storage order is chronological, not call order.
            order={ident:index for index,ident in enumerate(c['selector']['selected_keys'])}
            pairs=sorted(pairs,key=lambda p:(order.get(p['opportunity_key'],len(order)),p['opportunity_key']))
        for pair in pairs:
            if pair['outcome']['status'] not in {'WIN','FAIL_STOP','FAIL_TIMEOUT'}:
                continue
            origin='postclose_auxiliary:'+pair['day']
            origin_keys.add(origin)
            if not research_grant:
                store.db.execute('''INSERT OR IGNORE INTO attempt_budgets
                    SELECT attempt,? FROM attempts WHERE request_id IN (?,?) AND source='provider' ''',
                    (origin,pair['requests']['current'],pair['requests']['candidate']))
                store.commit()
            for role in ('current','candidate'):
                rid=pair['requests'][role]
                state=store.db.execute('SELECT state FROM requests WHERE id=?',(rid,)).fetchone()[0]
                if state != 'planned':
                    continue
                if (store.budget_used(key)>=limit
                        or (not research_grant and store.budget_used(origin)>=LIMIT)
                        or (max_new_calls is not None and sent>=max_new_calls)
                        or (stop_epoch is not None and time.time()>=stop_epoch)):
                    break
                req=store.request(rid)
                registry=G.load(data_root,pair[role+'_registry'])
                snapshot=store.get(pair['snapshot_obj'])
                wanted=expected_request(data_root,c,pair,role,snapshot,registry)
                if any(req.get(k)!=wanted.get(k) for k in ('paired_replay_id','candidate_input','candidate','control','stage')):
                    raise ValueError('auxiliary_pair_request_changed')
                logical_input=G.production_request(snapshot,registry)[0]
                attempt=store.reserve(rid,fence,budget_key=key,call_limit=limit,additional_budget_keys=[] if research_grant else [origin])
                result=None
                try:
                    result=transport(req,timeout_sec=30)
                    decoded,errors=response_projection(result,req,logical_input,registry)
                    record=dict(result=result,validation_errors=errors,transport_invoked=True)
                except Exception as exc:
                    import traceback
                    record=dict(error_type=type(exc).__name__,
                                error_frames=[dict(file=Path(f.filename).name,line=f.lineno,function=f.name)
                                              for f in traceback.extract_tb(exc.__traceback__)],
                                validation_errors=['provider_attempt_uncertain' if result is None else 'response_validation_exception'],
                                transport_invoked=True)
                    if result is not None:
                        record['result']=result
                store.land_response(attempt,record); store.finish(attempt,record); sent+=1
                if record.get('error_type'):
                    # Keep the reservation, and stop this batch rather than
                    # charging every remaining request for the same failure.
                    stop_epoch=0
        result=P.seal(dict(schema=SCHEMA,source_date=day,new_calls=sent,call_limit=limit,
                           campaign_sha256=c['artifact_content_sha256'],research=c.get('research'),
                           research_funding_sha256=(research_grant.get('funding_sha256',research_grant['artifact_content_sha256']) if research_grant else None),
                           call_budget=dict(key=key,used_before=before,used_after=store.budget_used(key)),
                           observation_date_budgets={k:store.budget_used(k) for k in sorted(origin_keys)},
                           census=store.states(c['artifact_content_sha256']),**P.AUTH))
    P.write(out/'calls'/(result['artifact_content_sha256']+'.json'),result)
    P.write(out/'call-completion.json',result)
    return result


def matrix(rows):
    c=Counter()
    for outcome,verdict in rows:
        c['TP' if outcome=='WIN' and verdict=='PASS' else 'FN' if outcome=='WIN' else 'FP' if verdict=='PASS' else 'TN']+=1
        c[verdict+'_'+outcome]+=1
    for key in ('TP','FP','FN','TN'): c[key]+=0
    return dict(c,pass_win_rate=c['TP']/(c['TP']+c['FP']) if c['TP']+c['FP'] else None,
                winner_retention=c['TP']/(c['TP']+c['FN']) if c['TP']+c['FN'] else None,
                failure_blocking=c['TN']/(c['TN']+c['FP']) if c['TN']+c['FP'] else None)


def improves(current, candidate):
    if not (current['TP']+current['FP']) or not (candidate['TP']+candidate['FP']):return False
    a=Fraction(current['TP'],current['TP']+current['FP']); b=Fraction(candidate['TP'],candidate['TP']+candidate['FP'])
    return b>a or (b==a and candidate['TP']>current['TP'])


def evaluate(data_root, day, *, campaign_path=None):
    c, out, canonical = load_campaign(data_root,day,campaign_path)
    per=defaultdict(lambda:dict(current=[],candidate=[],excluded=Counter(),changes=Counter()))
    pairs=[]
    with S.Store(data_root) as store:
        rows=validate_campaign(store,c)
        owner={(r[1],r[2]):r for r in rows}
        for pair in c['pairs']:
            sid=pair['scope']; value=per[sid]; verdicts={}; reasons=[]
            outcome=pair['outcome']['status']
            if outcome not in {'WIN','FAIL_STOP','FAIL_TIMEOUT'}:reasons.append('label_unresolved')
            for role in ('current','candidate'):
                r=owner[pair['opportunity_key'],role]; registry=G.load(data_root,pair[role+'_registry'])
                req=store.request(r[6]); snapshot=store.get(pair['snapshot_obj'])
                expected=expected_request(data_root,c,pair,role,snapshot,registry)
                if any(req.get(k)!=expected.get(k) for k in ('paired_replay_id','candidate_input','candidate','control','stage')):
                    raise ValueError('auxiliary_pair_request_changed')
                if r[4]!='completed' or not r[5]:reasons.append(role+':'+r[4]);continue
                record=store.get(r[5]); result=record.get('result',{})
                response,errors=response_projection(result,req,G.production_request(snapshot,registry)[0],registry)
                if errors or not (result.get('provider_provenance') or {}).get('response_id'):
                    reasons.append(role+':invalid_response');continue
                verdicts[role]=response['risk_verdict']
            if reasons:
                value['excluded'].update(reasons)
            else:
                for role in verdicts:value[role].append((outcome,verdicts[role]))
                if (verdicts['current']=='PASS') != (verdicts['candidate']=='PASS'):
                    value['changes'][('added_' if verdicts['candidate']=='PASS' else 'removed_')+outcome]+=1
            pairs.append(dict(pair,verdicts=verdicts,excluded=reasons))
        states=store.states(c['artifact_content_sha256'])
    scopes={}
    for sid,v in per.items():
        current=matrix(v['current']); challenger=matrix(v['candidate'])
        chosen=next(p for p in c['pairs'] if p['scope']==sid)
        scopes[sid]=dict(current=current,candidate=challenger,current_registry=chosen['current_registry'],
                        candidate_registry=chosen['candidate_registry'],paired_points=len(v['current']),
                        expected_pairs=sum(p['scope']==sid for p in c['pairs']), exclusions=dict(v['excluded']),
                        pass_changes=dict(v['changes']),improved=improves(current,challenger),
                        machine_win_rate=sum(o=='WIN' for o,_ in v['current'])/len(v['current']) if v['current'] else None)
    result=P.seal(dict(schema=SCHEMA,source_date=day,campaign_sha256=c['artifact_content_sha256'],
        parent_bundle_sha256=c['parent_bundle_sha256'],detector_manifest_hash=c['detector_manifest_hash'],
        scopes=scopes,pairs=pairs,request_completion=not c['eligible_census'].get('typed_candidate_incompatible') and not any(states.get(k) for k in ('planned','reserved','failed')),
        paired_metrics_ready=any(v['paired_points'] for v in scopes.values()),
        observation_mode='confirmation_replay',population_claim='completed_common_pairs_only',
        eligible_census=c['eligible_census'],not_sampled_budget=c['not_sampled_budget'],
        state='evaluated',call_limit=c['call_limit'],
        **(dict(research=c['research'],campaign_path=str(canonical.resolve())) if c.get('research') else {}),**P.AUTH))
    P.write(out/'evaluations'/(result['artifact_content_sha256']+'.json'),result)
    P.write(out/'evaluation.json',result)
    return result


def auxiliary_report(data_root,day,publication,parent,*,publish_policy=True):
    """Seal a bounded comparison, carrying the actual effective auxiliary view."""
    import fcntl
    import gzip
    import subprocess
    from src.engine.scalping import reversal_auxiliary_intraday as I
    from src.engine.scalping import continuous_reversal_operating_postclose as O
    from src.engine.scalping import continuous_reversal_shared_ledger as L
    from src.engine.scalping import continuous_reversal_policy_v5 as V
    if parent['continuous_reversal']['schema']=='continuous_reversal_policy_v6':
        from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    machine=read(O.directory(data_root,day)/'machine-comparison.json')
    campaign=read(directory(data_root,day)/'latest-campaign.json')
    if campaign['machine_report_sha256']!=machine['artifact_content_sha256'] or campaign['parent_bundle_sha256']!=parent['bundle_sha256']:
        raise ValueError('auxiliary_tuning_generation_changed')
    evaluated=evaluate(data_root,day)
    evalpath=directory(data_root,day)/'evaluations'/(evaluated['artifact_content_sha256']+'.json')
    folder=I.root(data_root);folder.mkdir(parents=True,exist_ok=True)
    with (folder/'publisher.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        bindings=I.effective_bindings(data_root,parent,day=day)
        overlay=I.current(data_root,parent,day=day)
        measured=I.independent_scopes(data_root,parent,overlay)
        measured.update(s for s,v in evaluated['scopes'].items() if v['paired_points']>0)
        promoted=[]
        for sid,metrics in evaluated['scopes'].items():
            if bindings.get(sid)==metrics['current_registry'] and metrics['improved']:
                bindings[sid]=metrics['candidate_registry']
                promoted.append(sid)
        # Inheritance retains independent measured PRE/AFTER policies.
        f=parent['continuous_reversal']
        for sid in list(bindings):
            regular=sid.replace('|PRE|','|REGULAR|').replace('|AFTER|','|REGULAR|')
            key,route=sid.rsplit('|',1)
            if sid!=regular and sid not in measured and f['auxiliary_cells'][key]['routes'][route].get('inherited_from'):
                bindings[sid]=bindings[regular]
        receipts=[dict(path=str(evalpath.resolve()),sha256=P.file_hash(evalpath))]+I.lineage_sources(data_root,parent,overlay)
        for ident in sorted(set(bindings.values())):
            path=G.directory(data_root)/(ident+'.json')
            receipts.append(dict(path=str(path.resolve()),sha256=P.file_hash(path)))
        if overlay:
            path=folder/'generations'/(overlay['artifact_content_sha256']+'.json')
            receipts.append(dict(path=str(path.resolve()),sha256=P.file_hash(path)))
        with S.Store(data_root) as store:
            validate_campaign(store,campaign)
            snapshot=store.snapshot(campaign['artifact_content_sha256'])
            out=directory(data_root,day);(out/'frozen').mkdir(parents=True,exist_ok=True)
            evidence=L.response_evidence(store,out,snapshot)
            ownerstates=Counter(r[4] for r in store.owners(campaign['artifact_content_sha256']))
        mc=copy.deepcopy(f['machine_cells']);ac=copy.deepcopy(f['auxiliary_cells']);pending=[]
        for key,route in V.scopes():
            cell=mc[key]['routes'][route]
            ids=[b['branch_id'] for b in cell['payload']['branches']]
            cell['scope_execution_hash']=V.scope_hash(ids,ac[key]['routes'][route]['payload'],cell['backend'],machine['execution_code_sha256'])
            if cell['backend'] not in {'union_v5','union_v6'}:pending.append(dict(scope=V.scope_id(key,route),reason='native_pair_carried'))
        issued=P.seal(dict(machine,cells=list(mc.values()),status='completed_with_scope_carry' if pending else 'completed',
            membership_status='registered',registration_state='registered',adoption_basis='carried',
            source_receipts=machine['source_receipts']+receipts,scope_pending=pending))
        auxiliary=P.seal(dict(schema=O.SCHEMA,source_date=day,target_date=day,publication_date=publication,
            status=issued['status'],cells=list(ac.values()),machine_report_sha256=issued['artifact_content_sha256'],
            registration_state='registered',
            adoption_basis='comparison_selected' if promoted else 'carried',
            comparison_promoted_scopes=sorted(promoted),
            results_sources=[dict(path=str(evidence.resolve()),sha256=P.file_hash(evidence))],source_receipts=receipts,
            comparison_complete=evaluated['request_completion'],paired_metrics_ready=evaluated['paired_metrics_ready'],
            comparison_contract=SCHEMA,comparison_metrics=evaluated['scopes'],auxiliary_registry_bindings=bindings,
            auxiliary_independent_scopes=sorted(measured),auxiliary_reader_code_hashes=I.code_hashes(),operating_day=day,generated_at=datetime.now(I.K.KST).isoformat(),
            evaluated_overlay_parent=(overlay or {}).get('artifact_content_sha256'),evaluated_base_bundle=parent['bundle_sha256'],
            auxiliary_rollback_bindings=I.rollback_bindings(data_root,parent,overlay),scope_pending=pending,
            scope_census=dict(planned=len(V.scopes()),new_ready=len(V.scopes())-len(pending),new_actual_pid_consumed=0,native_carried=len(pending),contract_gaps=0),
            owner_request_census=dict(expected=campaign['expected_owner_requests'],missing=0,**ownerstates),
            observation_mode='confirmation_replay',call_limit=LIMIT,**P.AUTH))
        O.directory(data_root,day).mkdir(parents=True,exist_ok=True)
        P.write(O.directory(data_root,day)/'machine.json',issued)
        P.write(O.directory(data_root,day)/'auxiliary.json',auxiliary)
        if publish_policy:
            P.write(P.directory(data_root,day)/'auxiliary.json',auxiliary)
            P.write(P.directory(data_root,day)/'call-freeze.json',P.seal(dict(schema=O.SCHEMA,source_date=day,status='frozen',
                comparison_contract=SCHEMA,machine_report_sha256=machine['artifact_content_sha256'],
                campaign_sha256=campaign['artifact_content_sha256'],call_limit=LIMIT,census=dict(ownerstates),**P.AUTH)))
            with gzip.open(evidence,'rt') as src,(P.directory(data_root,day)/'provider-results.jsonl').open('w') as dest:
                for line in src:dest.write(line)
            commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
            bundle=V.stage(data_root,day,publication,issued,auxiliary,target_date=N.next_target(publication),release_commit=commit)
            P.write(Path(data_root)/'report/ai_entry_setup_paired_replay_batch'/f'compact_auxiliary_paired_economic_{day}.json',
                P.seal(dict(auxiliary,staged=dict(status='prepared',bundle_sha256=bundle['bundle_sha256'],target_date=bundle['target_date']))))
        return auxiliary


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--date')
    parser.add_argument('--mode',choices=['configure','rebind-input','prepare','calls','evaluate'],required=True)
    parser.add_argument('--input-version')
    parser.add_argument('--expected-config-sha256')
    parser.add_argument('--candidate')
    parser.add_argument('--scope',action='append',default=[])
    parser.add_argument('--seed')
    parser.add_argument('--max-pairs',type=int,default=50)
    args=parser.parse_args(argv)
    if args.mode=='configure':
        result=configure(args.data_root,candidate=args.candidate,scopes=args.scope,seed=args.seed,max_pairs=args.max_pairs)
    elif args.mode=='rebind-input':
        result=rebind_candidate_input(args.data_root,input_version=args.input_version,
                                      expected_config_sha256=args.expected_config_sha256)
    elif not args.date:parser.error('--date required for comparison')
    elif args.mode=='prepare':
        from src.engine.scalping import continuous_reversal_operating_postclose as O
        from src.engine.scalping import mechanistic_entry_runtime_policy as N
        from src.engine.scalping.continuous_reversal import KST
        parent=N.load_effective(data_root=args.data_root,target_date=datetime.now(KST).date().isoformat())
        machine=read(O.directory(args.data_root,args.date)/'machine-comparison.json')
        result=prepare(args.data_root,args.date,machine,parent)
    else:result=globals()[args.mode](args.data_root,args.date)
    print(json.dumps({k:result[k] for k in ('schema','source_date','artifact_content_sha256') if k in result},sort_keys=True))


if __name__=='__main__':main()
