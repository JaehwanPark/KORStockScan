"""Dated continuous-reversal machine/auxiliary component and runtime adapter."""
from __future__ import annotations
import copy
import fcntl
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from src.engine.scalping import continuous_reversal as kernel
from src.engine.scalping.continuous_reversal_postclose import digest, expected_cells, file_hash, directory
from src.engine.scalping.reversal_auxiliary_contract import production_request, validate_response, ARMS, PRODUCTION_VERSION

SCHEMA='continuous_reversal_policy_v1'
KST=ZoneInfo('Asia/Seoul')


def validate_family(family):
    if family.get("schema")=="continuous_reversal_policy_v6":
        from src.engine.scalping.continuous_reversal_policy_v6 import validate_family as v6
        return v6(family)
    if family.get('schema')=='continuous_reversal_policy_v5':
        from src.engine.scalping.continuous_reversal_policy_v5 import validate_family as v5
        return v5(family)
    if family.get('schema')=='continuous_reversal_policy_v4':
        from src.engine.scalping.continuous_reversal_policy_v4 import validate_family as v4
        return v4(family)
    if isinstance(family,dict) and family.get('schema')=='continuous_reversal_policy_v3':
        from src.engine.scalping.continuous_reversal_policy_v3 import validate_family as v3
        return v3(family)
    if isinstance(family,dict) and family.get('schema')=='continuous_reversal_policy_v2':
        from src.engine.scalping.continuous_reversal_policy_v2 import validate_family as validate_v2
        return validate_v2(family)
    if (not isinstance(family,dict) or family.get('schema')!=SCHEMA
        or family.get('kernel_version')!=kernel.VERSION
        or family.get('auxiliary_version')!=PRODUCTION_VERSION
        or family.get('selection_metric')!='cumulative_raw_win_fraction'
        or family.get('label_contract')!=dict(target_net_pct=.4,stop_net_pct=-3.,cost_rate=.0023,horizon_seconds=1800)):
        raise ValueError('reversal_family_contract_invalid')
    for name in ['machine_cells','auxiliary_cells']:
        cells=family.get(name)
        if not isinstance(cells,dict) or set(cells)!=set(expected_cells()):
            raise ValueError('reversal_twelve_cell_coverage_invalid')
        for key,cell in cells.items():
            payload=cell.get('payload')
            if not isinstance(payload,dict) or cell.get('payload_sha256')!=digest(payload):
                raise ValueError('reversal_cell_hash_invalid')
            field,allowed=('rule',kernel.RULES) if name=='machine_cells' else ('arm',ARMS)
            if set(payload)!={field} or payload[field] not in allowed:
                raise ValueError('reversal_cell_payload_invalid')
            inherited=cell.get('inherited_from')
            if inherited:
                if cell.get('local_metrics') is not None or cell.get('parent_payload_sha256')!=digest(payload):
                    raise ValueError('reversal_inheritance_invalid')
                g,_,b=key.split('|');parent='|'.join((g,'REGULAR',b))
                if inherited.startswith('previous:'):
                    if inherited!='previous:'+parent:
                        raise ValueError('reversal_previous_regular_scope_invalid')
                else:
                    if inherited!=parent or cells[parent]['payload']!=payload:
                        raise ValueError('reversal_regular_parent_mismatch')
            else:
                metrics=cell.get('local_metrics') or {}
                numerator,denominator=(('wins','resolved') if name=='machine_cells'
                                       else ('pass_wins','pass_count'))
                wins,n=metrics.get(numerator),metrics.get(denominator)
                if type(wins) is not int or type(n) is not int or not 0 <= wins <= n or n <= 0:
                    raise ValueError('reversal_cell_metrics_invalid')
    if family.get('family_sha256')!=digest({k:v for k,v in family.items() if k!='family_sha256'}):
        raise ValueError('reversal_family_hash_invalid')


def publish(data_root,day,publication,machine,auxiliary):
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    target=native.next_target(publication)
    policy_root=native.root(Path(data_root));policy_root.mkdir(parents=True,exist_ok=True)
    with (policy_root/'publisher.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        parent=native.load_effective(data_root=Path(data_root),target_date=publication)
        if parent is None:raise ValueError('reversal_incumbent_parent_missing')
        snapshots={}
        for name,report in [('machine',machine),('auxiliary',auxiliary)]:
            native._atomic_write_json(policy_root/'sources'/f"reversal-{report['artifact_content_sha256']}.json",report)
            snapshots[name]=file_hash(policy_root/'sources'/f"reversal-{report['artifact_content_sha256']}.json")
        family=dict(schema=SCHEMA,kernel_version=kernel.VERSION,auxiliary_version=PRODUCTION_VERSION,
            source_date=day,publication_date=publication,effective_date=target,
            selection_metric='cumulative_raw_win_fraction',label_contract=machine['label_contract'],
            machine_report_sha256=machine['artifact_content_sha256'],auxiliary_report_sha256=auxiliary['artifact_content_sha256'],
            report_file_sha256=snapshots, kernel_sha256=file_hash(kernel.__file__),
            source_manifest_sha256=machine['source_manifest_sha256'],
            machine_cells={c['key']:c for c in machine['cells']},auxiliary_cells={c['key']:c for c in auxiliary['cells']},
            parent_bundle_sha256=parent['bundle_sha256'],
            hard_guards_unchanged=True,actual_order_submitted=False)
        from src.engine.scalping import reversal_auxiliary_contract
        family['contract_file_sha256']={
            'continuous_reversal.py':file_hash(kernel.__file__),
            'reversal_auxiliary_contract.py':file_hash(reversal_auxiliary_contract.__file__)}
        family['family_sha256']=digest(family);validate_family(family)
        bundle=copy.deepcopy(parent)
        carrier_version=PRODUCTION_VERSION+':reversal_citation_v6'
        from src.engine.scalping.reversal_auxiliary_contract import production_prompt
        carrier_prompt=production_prompt('reversal_citation_v6')
        carrier=dict(prompt_version=carrier_version,variant='continuous_reversal:reversal_citation_v6',
                     system_prompt=carrier_prompt,system_prompt_sha256=digest(carrier_prompt))
        bundle['ai_policy']=carrier
        for scoped in (bundle.get('scope_policies') or {}).values():
            scoped['ai_policy']=copy.deepcopy(carrier)
        for key in ['strategy_activation','winrate_selection','machine_evaluation_source','compact_evaluation_source']:
            bundle.pop(key,None)
        bundle.update(source_date=day,publication_date=publication,target_date=target,
                      generated_at=datetime.now(KST).isoformat(),continuous_reversal=family,
                      previous_bundle_sha256=parent['bundle_sha256'],machine_disposition='continuous_reversal_selected',
                      compact_prompt_disposition='continuous_reversal_selected')
        bundle['legacy_machine_policy_role']='compatibility_only_not_entry_selection'
        source=dict(schema=SCHEMA,source_date=day,target_date=target,continuous_reversal=family,
                    artifact_content_sha256=digest(family))
        source_bytes=json.dumps(source,ensure_ascii=True,allow_nan=False,indent=2).encode()
        source_hash=__import__('hashlib').sha256(source_bytes).hexdigest()
        source_path=policy_root/'sources'/f'{source_hash}.json'
        if not source_path.exists():
            source_path.parent.mkdir(parents=True,exist_ok=True)
            with source_path.open('xb') as handle:handle.write(source_bytes);handle.flush();__import__('os').fsync(handle.fileno())
        if file_hash(source_path)!=source_hash:raise ValueError('reversal_source_snapshot_invalid')
        bundle.update(source_file_sha256=source_hash,source_artifact_sha256=digest(family))
        bundle.pop('bundle_sha256',None);bundle['bundle_sha256']=digest(bundle)
        native.validate(bundle,target_date=target)
        dated=policy_root/f'policy_{target}.json'
        if dated.exists():
            previous=json.loads(dated.read_text())
            native._atomic_write_json(policy_root/'generations'/f"{previous['bundle_sha256']}.json",previous)
        native._atomic_write_json(policy_root/'generations'/f"{bundle['bundle_sha256']}.json",bundle)
        native._atomic_write_json(dated,bundle)
        loaded=native.load(data_root=Path(data_root),target_date=target)
        if loaded['bundle_sha256']!=bundle['bundle_sha256']:raise ValueError('reversal_publish_readback_failed')
        return dict(status='staged',target_date=target,bundle_sha256=bundle['bundle_sha256'],
                    family_sha256=family['family_sha256'],parent_bundle_sha256=parent['bundle_sha256'])


def validate_sources(bundle,data_root):
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    with native.source_anchor(data_root):
        return _validate_sources(bundle,Path(data_root).absolute())


def _validate_sources(bundle,data_root):
    if (bundle.get("continuous_reversal") or {}).get("schema")=="continuous_reversal_policy_v6":
        from src.engine.scalping.continuous_reversal_policy_v6 import validate_sources as v6
        return v6(bundle,data_root)
    if (bundle.get('continuous_reversal') or {}).get('schema')=='continuous_reversal_policy_v5':
        from src.engine.scalping.continuous_reversal_policy_v5 import validate_sources as v5
        return v5(bundle,data_root)
    if (bundle.get('continuous_reversal') or {}).get('schema')=='continuous_reversal_policy_v4':
        from src.engine.scalping.continuous_reversal_policy_v4 import validate_sources as v4
        return v4(bundle,data_root)
    if (bundle.get('continuous_reversal') or {}).get('schema')=='continuous_reversal_policy_v3':
        from src.engine.scalping.continuous_reversal_policy_v3 import validate_sources as v3
        return v3(bundle,data_root)
    if bundle.get('continuous_reversal',{}).get('schema')=='continuous_reversal_policy_v2':
        from src.engine.scalping.continuous_reversal_policy_v2 import validate_sources as validate_v2
        return validate_v2(bundle,data_root)
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    family=bundle['continuous_reversal'];validate_family(family)
    native._signature(Path(kernel.__file__))
    if family['kernel_sha256']!=file_hash(kernel.__file__):
        raise ValueError('reversal_kernel_code_changed')
    from src.engine.scalping import reversal_auxiliary_contract
    for module in (kernel,reversal_auxiliary_contract):
        path=Path(module.__file__)
        native._signature(path)
        if family['contract_file_sha256'].get(path.name)!=file_hash(path):
            raise ValueError('reversal_issued_contract_code_changed')
    for name in ['machine','auxiliary']:
        path=native.root(data_root)/'sources'/f"reversal-{family[name+'_report_sha256']}.json"
        if native._source_hash(str(path),native._signature(path))!=family['report_file_sha256'][name]:
            raise ValueError('reversal_report_snapshot_changed')
        report=native._read(path)
        if report.get('source_date')!=family['source_date'] or report.get('status')!='completed':
            raise ValueError('reversal_report_source_date_invalid')
        if report['artifact_content_sha256']!=digest({k:v for k,v in report.items() if k!='artifact_content_sha256'}):
            raise ValueError('reversal_report_content_hash_invalid')
        if report['cells']!=list(family[name+'_cells'].values()):
            # Object serialization can sort cell keys; compare by native key.
            if {c['key']:c for c in report['cells']}!=family[name+'_cells']:
                raise ValueError('reversal_report_policy_cells_mismatch')
        if name=='auxiliary':
            for record in report.get('results_sources',[]):
                response_path=Path(record['path'])
                if native._source_hash(str(response_path),native._signature(response_path))!=record['sha256']:
                    raise ValueError('reversal_actual_provider_source_changed')
        for key,cell in family[name+'_cells'].items():
            if str(cell.get('inherited_from') or '').startswith('previous:'):
                parent_path=Path(cell['previous_report_path'])
                native._signature(parent_path)
                parent=native._read(parent_path)
                if (parent.get('artifact_content_sha256')!=cell['previous_report_sha256']
                    or digest({k:v for k,v in parent.items() if k!='artifact_content_sha256'})!=cell['previous_report_sha256']
                    or parent.get('source_date')!=cell['previous_source_date']
                    or not '2026-06-05' <= cell['previous_source_date'] < family['source_date']):
                    raise ValueError('reversal_previous_report_invalid')
                matched=[c for c in parent['cells'] if 'previous:'+c['key']==cell['inherited_from']]
                if len(matched)!=1 or matched[0]['payload']!=cell['payload']:
                    raise ValueError('reversal_previous_regular_payload_mismatch')
    return bundle


def assess(family,snapshot,*,symbol,session):
    result=_assess(family,snapshot,symbol=symbol,session=session)
    # Observability cannot turn a valid decision into runtime permission or denial.
    try:
        from src.engine.scalping.reversal_policy_status import record_decision
        record_decision(family,result)
    except (OSError,ValueError,KeyError,TypeError):
        pass
    return result


def _assess(family,snapshot,*,symbol,session):
    if family.get("schema")=="continuous_reversal_policy_v6":
        from src.engine.scalping.continuous_reversal_policy_v6 import assess as v6
        return v6(family,snapshot,symbol=symbol,session=session)
    if family.get('schema')=='continuous_reversal_policy_v5':
        from src.engine.scalping.continuous_reversal_policy_v5 import assess as v5
        return v5(family,snapshot,symbol=symbol,session=session)
    if family.get('schema')=='continuous_reversal_policy_v4':
        from src.engine.scalping.continuous_reversal_policy_v4 import assess as v4
        return v4(family,snapshot,symbol=symbol,session=session)
    if family.get('schema')=='continuous_reversal_policy_v3':
        from src.engine.scalping.continuous_reversal_policy_v3 import assess as v3
        return v3(family,snapshot,symbol=symbol,session=session)
    if family.get('schema')=='continuous_reversal_policy_v2':
        from src.engine.scalping.continuous_reversal_policy_v2 import assess as assess_v2
        return assess_v2(family,snapshot,symbol=symbol,session=session)
    validate_family(family)
    result=dict(schema='mechanistic_entry_policy_decision_v1',action='BLOCK',reason='no_current_first_uptick',
        policy_version=kernel.VERSION,primary_decision_owner='mechanistic_entry_adjudicator',
        ai_role='auxiliary_risk_screen_pass_veto_no_promotion',price_reversal_confirmed=False,
        runtime_effect=False,allowed_runtime_apply=False,actual_order_submitted=False,broker_order_forbidden=True)
    if snapshot is None:return result,None,None,None
    event,source=snapshot
    if event['symbol']!=symbol or event['market']!=kernel.market_bucket(session):
        raise ValueError('reversal_snapshot_scope_conflict')
    key=kernel.cell_key(symbol,session,event['confirmation_price'])
    cell=family['machine_cells'][key];rule=cell['payload']['rule']
    result.update(cell_key=key,rule=rule,event_id=event['event_id'],event=event,
                  price_reversal_confirmed=True,machine_component_sha256=digest(family['machine_cells']))
    if event['entry_ask'] is None:
        result.update(action='RECHECK',reason='entry_quote_source_missing');return result,None,None,None
    if not kernel.conditions(event)[rule]:
        missing=('VOL' in rule and event['volume_ratio_60s'] is None) or (rule.startswith('DD5') and event['drawdown_5m_pct'] is None)
        result.update(action='RECHECK' if missing else 'BLOCK',reason='required_reversal_feature_missing' if missing else 'selected_reversal_condition_not_met')
        return result,None,None,None
    result.update(action='ENTER_NOW',reason='continuous_reversal_cell_pass')
    arm=family['auxiliary_cells'][key]['payload']['arm']
    inp,prompt,schema=production_request(source,arm)
    return result,inp,prompt,schema


def compose(response,policy):
    from src.engine.scalping.entry_setup_evidence import MECHANISTIC_PRIMARY_ROLE_CONTRACT
    assessment=policy['continuous_reversal_assessment']
    action=assessment['action'];inp=policy.get('continuous_reversal_input')
    arm=policy.get('continuous_reversal_arm')
    phase=assessment.get('decision_phase','FIRST_UPTICK')
    if assessment.get('policy_version') in {'continuous_reversal_policy_v2','continuous_reversal_policy_v3','continuous_reversal_policy_v4','continuous_reversal_policy_v5','continuous_reversal_policy_v6'} and action=='ENTER_NOW':
        from src.engine.scalping.reversal_auxiliary_phases import validate_response as validate_phase
        if assessment.get('policy_version')=='continuous_reversal_policy_v4':
            from src.engine.scalping.reversal_path_auxiliary import validate_response as validate_phase
        if assessment.get('policy_version')=='continuous_reversal_policy_v5':
            from src.engine.scalping.reversal_operating_auxiliary import validate_response as validate_phase
        if assessment.get('policy_version')=='continuous_reversal_policy_v6':
            from src.engine.scalping.reversal_extended_union import validate_response as validate_phase
        errors=validate_phase(response,inp,arm=arm,phase=phase)
        from src.engine.scalping.reversal_current_backend import validate_any_claim as validate_claim
        try:
            from src.engine.scalping.mechanistic_entry_runtime_policy import load_effective
            from src.utils.constants import DATA_DIR
            active=load_effective(data_root=DATA_DIR,target_date=datetime.now(KST).date().isoformat())
            if assessment.get('policy_version')=='continuous_reversal_policy_v6':
                from src.engine.scalping.continuous_reversal_policy_v6 import validate_active_claim
                from src.engine.scalping.reversal_auxiliary_intraday import validate_decision
                validate_decision(DATA_DIR,policy,active,now=__import__('time').time())
                assessment['still_valid_policy_refs']=validate_active_claim(policy,active,now=__import__('time').time())
            elif assessment.get('policy_version')=='continuous_reversal_policy_v5':
                from src.engine.scalping.continuous_reversal_policy_v5 import validate_active_claim
                from src.engine.scalping.reversal_auxiliary_intraday import validate_decision
                validate_decision(DATA_DIR, policy, active, now=__import__('time').time())
                assessment['still_valid_policy_refs']=validate_active_claim(policy,active,now=__import__('time').time())
            else:
                if not active or active['bundle_sha256']!=policy['machine_bundle_sha256']:
                    raise ValueError('reversal_policy_changed_after_provider')
                validate_claim(policy.get('continuous_reversal_claim'),assessment['family_sha256'],now=__import__('time').time())
        except (ValueError,OSError,KeyError,TypeError) as exc:
            errors.append(str(exc))
    else:
        errors=validate_response(response,inp,complete_source_only=arm==ARMS[-1]) if action=='ENTER_NOW' else []
    verdict=response.get('risk_verdict') if isinstance(response,dict) else None
    passed=action=='ENTER_NOW' and not errors and verdict=='PASS'
    final='BUY' if passed else 'DROP' if action=='BLOCK' or (not errors and verdict=='VETO') else 'WAIT'
    return dict(action=final,action_v2=final,score=0,reason=assessment['reason'] if action!='ENTER_NOW' else 'continuous_reversal_ai_'+str(verdict or 'invalid').lower(),
        entry_primary_decision_owner='mechanistic_entry_adjudicator',entry_ai_role='auxiliary_risk_screen_pass_veto_no_promotion',
        entry_decision_role_contract=dict(MECHANISTIC_PRIMARY_ROLE_CONTRACT),entry_mechanistic_action=action,
        entry_mechanistic_policy_decision=assessment,entry_mechanistic_policy_version=assessment.get('policy_version',kernel.VERSION),
        entry_mechanistic_policy_sha256=assessment.get('machine_component_sha256'),
        entry_ai_raw_risk_verdict=verdict,entry_ai_risk_verdict=verdict,entry_ai_advisory_verdict=verdict,
        entry_ai_risk_codes=response.get('risk_codes',[]) if isinstance(response,dict) else [],
        entry_ai_advisory_contract_valid=not errors,entry_ai_advisory_contract_errors=errors,
        entry_ai_contract_valid=not errors,entry_ai_contract_errors=errors,
        entry_ai_screen_required=action=='ENTER_NOW',entry_ai_screen_pass=passed,
        entry_ai_screen_status='pass' if passed else 'response_invalid' if errors else str(verdict or 'not_requested_machine_nonentry').lower(),
        entry_ai_followup_disposition='ai_pass_existing_submit_guard' if passed else 'no_entry_authority',
        entry_ai_followup_authority='existing_runtime_submit_and_order_guards' if passed else 'existing_scanner_loop_observation_only',
        entry_machine_pass_submit_candidate=passed,entry_probe_intent=False,entry_recheck_intent=final=='WAIT',
        machine_bundle_sha256=policy['machine_bundle_sha256'],continuous_reversal_event_id=assessment.get('event_id'),
        continuous_reversal_cell_key=assessment.get('cell_key'),continuous_reversal_arm=arm,
        continuous_reversal_signal_id=assessment.get('signal_id'),
        continuous_reversal_primary_branch=assessment.get('primary_branch'),
        continuous_reversal_matched_branches=assessment.get('matched_branches'),
        continuous_reversal_matched_policy_refs=assessment.get('matched_policy_refs'),
        continuous_reversal_still_valid_policy_refs=assessment.get('still_valid_policy_refs'),
        continuous_reversal_signal_set_hash=assessment.get('signal_set_hash'),
        continuous_reversal_opportunity_key=assessment.get('opportunity_key'),
        continuous_reversal_phase=phase,
        entry_setup_source_quality='price_and_entry_quote_valid' if inp else 'not_evaluated',
        provider_called=action=='ENTER_NOW',entry_composed_action=final,continuous_reversal_applied=True,
        decision_quality_contract_status='pass' if not errors else 'rejected',
        decision_quality_runtime_action_mapping='continuous_reversal_machine_auxiliary',
        entry_final_execution_authority='existing_runtime_submit_and_order_guards')


def direct_handoff(data_root,day,*,effective_date=None,publication_date=None):
    """Revalidate producer -> dated loader -> consumer without an EV gate."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    publication=publication_date or day
    effective=effective_date or native.next_target(publication)
    bundle=native.load(data_root=Path(data_root),target_date=effective)
    if not bundle or not bundle.get('continuous_reversal'):
        raise ValueError('continuous_reversal_dated_policy_missing')
    family=bundle['continuous_reversal']
    if family['source_date']!=day or family['publication_date']!=publication:
        raise ValueError('continuous_reversal_source_date_mismatch')
    out=directory(data_root,day)
    if family.get('schema') in {'continuous_reversal_policy_v2','continuous_reversal_policy_v3','continuous_reversal_policy_v4','continuous_reversal_policy_v5','continuous_reversal_policy_v6'}:
        # Initial intraday research and daily reports have independent owners.
        # Handoff reads the issued native immutable component snapshots.
        out=native.root(Path(data_root))/'sources'
    for name in ['machine','auxiliary']:
        path=out/(f"reversal-{family[name+'_report_sha256']}.json" if family.get('schema') in {'continuous_reversal_policy_v2','continuous_reversal_policy_v3','continuous_reversal_policy_v4','continuous_reversal_policy_v5','continuous_reversal_policy_v6'} else name+'.json')
        report=json.loads(path.read_text())
        if report['artifact_content_sha256']!=family[name+'_report_sha256'] or digest(
            {k:v for k,v in report.items() if k!='artifact_content_sha256'})!=report['artifact_content_sha256']:
            raise ValueError('continuous_reversal_latest_source_mismatch')
    handoff=dict(schema='continuous_reversal_consumer_v1',source_date=day,publication_date=publication,
        effective_date=effective,policy_bundle_sha256=bundle['bundle_sha256'],family_sha256=family['family_sha256'],
        machine_report_sha256=family['machine_report_sha256'],auxiliary_report_sha256=family['auxiliary_report_sha256'],
        machine_cells_sha256=digest(family['machine_cells']),auxiliary_cells_sha256=digest(family['auxiliary_cells']),
        machine_cell_count=len(family['machine_cells']),auxiliary_cell_count=len(family['auxiliary_cells']),selection_metric=family['selection_metric'],
        current_pid_consumption_claimed=False,runtime_effect=False,allowed_runtime_apply=False,actual_order_submitted=False)
    if family.get('schema') in {'continuous_reversal_policy_v5','continuous_reversal_policy_v6'}:
        scopes={key+'|'+route:dict(backend=cell['backend'],status=cell['status'],
                    scope_execution_hash=cell['scope_execution_hash'])
                for key,parent_cell in family['machine_cells'].items()
                for route,cell in parent_cell['routes'].items()}
        ready=sum(cell['backend'] in {'union_v5','union_v6'} for cell in scopes.values())
        census=dict(planned=len(scopes),new_ready=ready,new_actual_pid_consumed=0,
                    native_carried=len(scopes)-ready,contract_gaps=0)
        # `report` is the sealed auxiliary component read above. Never label
        # a native carry as successful application of the new operating list.
        if report.get('scope_census')!=census:
            raise ValueError('operating_handoff_scope_census_mismatch')
        pending=report.get('scope_pending',[])
        carried={sid for sid,cell in scopes.items() if cell['backend']=='registered_v4'}
        if len(pending)!=len(carried) or {p['scope'] for p in pending}!=carried:
            raise ValueError('operating_handoff_scope_pending_mismatch')
        handoff.update(scope_census=census,scope_dispositions=scopes,scope_pending=pending,
                       comparison_complete=report.get('comparison_complete') is True,
                       operating_disposition=report['status'],
                       machine_list_policy='explicit_operating_registration',
                       new_policy_application_claimed=False)
    from src.engine.scalping.reversal_policy_status import report_state, operating_scope
    handoff.update(policy_states=report_state(report),contract_scope_count=sum(len(c['routes']) for c in family['machine_cells'].values()),
        operating_scope_count=sum(operating_scope(k+'|'+r) for k,c in family['machine_cells'].items() for r in c['routes']))
    return handoff


def scoped_verification(data_root,day,*,effective_date=None,publication_date=None,require_consumer=False):
    issues=[];handoff={}
    try:
        handoff=direct_handoff(data_root,day,effective_date=effective_date,publication_date=publication_date)
        if require_consumer:
            path=Path(data_root)/'report'/'main_ai_prompt_consumer'/f"main_ai_prompt_consumer_{handoff['publication_date']}.json"
            consumer=json.loads(path.read_text())
            if consumer.get('compact_auxiliary')!=handoff or consumer.get('artifact_content_sha256')!=digest(
                {k:v for k,v in consumer.items() if k!='artifact_content_sha256'}):
                issues.append('continuous_reversal_last_consumer_stale')
    except (ValueError,KeyError,TypeError,OSError) as exc:
        issues.append('continuous_reversal_handoff_invalid:'+type(exc).__name__)
    return dict(scope='continuous_reversal',issues=issues,handoff=handoff,
                status='fail' if issues else 'pass',runtime_effect=False,actual_order_submitted=False)


def activate(data_root,target_date,*,now=None):
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    with native.source_anchor(data_root):
        return _activate(Path(data_root).absolute(),target_date,now=now)


def _activate(data_root,target_date,*,now=None):
    candidate=Path(data_root)/'runtime/mechanistic_entry_policy/candidates'/f'policy_{target_date}.json'
    if candidate.is_file():
        from src.engine.scalping.continuous_reversal_policy_v2 import activate as activate_v2
        if json.loads(candidate.read_text())['continuous_reversal']['schema']=='continuous_reversal_policy_v3':
            from src.engine.scalping.continuous_reversal_policy_v3 import activate as activate_v2
        if json.loads(candidate.read_text())['continuous_reversal']['schema']=='continuous_reversal_policy_v4':
            from src.engine.scalping.continuous_reversal_policy_v4 import activate as activate_v2
        if json.loads(candidate.read_text())['continuous_reversal']['schema']=='continuous_reversal_policy_v5':
            from src.engine.scalping.continuous_reversal_policy_v5 import activate as activate_v2
        if json.loads(candidate.read_text())['continuous_reversal']['schema']=='continuous_reversal_policy_v6':
            from src.engine.scalping.continuous_reversal_policy_v6 import activate as activate_v2
        return activate_v2(data_root,target_date,now=now)
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    current=(now or datetime.now(KST)).astimezone(KST)
    if current.date().isoformat()!=target_date:
        raise ValueError('continuous_reversal_activation_not_today')
    root=native.root(data_root)
    with (root/'publisher.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        bundle=native.load(data_root=data_root,target_date=target_date)
        family=bundle['continuous_reversal'];validate_family(family)
        previous=native._load_current(data_root,target_date)
        if previous and previous['bundle_sha256']==bundle['bundle_sha256']:
            return dict(status='already_active',bundle_sha256=bundle['bundle_sha256'])
        if not previous or previous['bundle_sha256']!=family['parent_bundle_sha256']:
            raise ValueError('continuous_reversal_activation_parent_cas_failed')
        receipt=dict(schema='continuous_reversal_current_v1',bundle_sha256=bundle['bundle_sha256'],
            previous_bundle_sha256=previous['bundle_sha256'],effective_from=current.isoformat(),
            effective_date=target_date,family_sha256=family['family_sha256'])
        receipt['receipt_sha256']=digest(receipt)
        native._atomic_write_json(root/'current.json',receipt)
        if native._load_current(data_root,target_date)['bundle_sha256']!=bundle['bundle_sha256']:
            raise ValueError('continuous_reversal_activation_readback_failed')
        return dict(status='activated',**receipt)
