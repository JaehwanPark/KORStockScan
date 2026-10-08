"""Explicit operator-funded auxiliary research in the shared comparison store.

Owns research configuration and a single durable allowance, not live policy or
orders. Experiments share request objects but never the postclose latest pointer.
"""
from __future__ import annotations

import re
from pathlib import Path
from src.engine.ai import offline_comparison_store as S
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_auxiliary_registry as G

SCHEMA = 'main_auxiliary_research_v1'
RESEARCH_ID = 'aux_prompt_research_20261008_01'
AUTHORITY = 'USER_APPROVED_ADDITIONAL_200_RESEARCH_CALLS_20261008'
LIMIT = 200
TOPUP_LIMIT = 400
TOPUP_AUTHORITY = 'USER_APPROVED_ADDITIONAL_200_TOTAL_400_RESEARCH_CALLS_20261008'
CONTINUATION_LIMIT = 600
CONTINUATION_AUTHORITY = 'USER_APPROVED_COMPLETE_RESEARCH_TOTAL_600_CALLS_20261008'
FOLLOWUP_LIMIT = 800
FOLLOWUP_AUTHORITY = 'USER_APPROVED_COMPLETE_RESEARCH_TOTAL_800_CALLS_20261008'


def root(data_root):
    return Path(data_root) / 'report/reversal_auxiliary_tuning/research' / RESEARCH_ID


def directory(data_root, experiment):
    if not isinstance(experiment, str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}', experiment):
        raise ValueError('auxiliary_research_experiment_invalid')
    return root(data_root) / 'experiments' / experiment


def read(path):
    import json
    v = json.loads(Path(path).read_text())
    if v.get('artifact_content_sha256') != P.seal(v)['artifact_content_sha256']:
        raise ValueError('auxiliary_research_artifact_changed')
    return v


def grant(data_root):
    v = read(root(data_root) / 'allowance.json')
    if (v.get('schema') != SCHEMA or v.get('research_id') != RESEARCH_ID
            or v.get('authority') != AUTHORITY or v.get('call_limit') != LIMIT
            or v.get('budget_key') != 'research_auxiliary:' + RESEARCH_ID
            or not v.get('source_dates') or not v.get('approval_reference')):
        raise ValueError('auxiliary_research_allowance_invalid')
    return v


def budget(data_root):
    base = grant(data_root)
    path = root(data_root) / 'allowance-topup-400.json'
    if not path.exists():
        if any((root(data_root)/f'allowance-topup-{n}.json').exists() for n in (600,800)):
            raise ValueError('auxiliary_research_previous_funding_required')
        return base
    topup = read(path)
    if (topup.get('research_id') != RESEARCH_ID
            or topup.get('authority') != TOPUP_AUTHORITY
            or topup.get('base_allowance_sha256') != base['artifact_content_sha256']
            or topup.get('from_limit') != LIMIT or topup.get('call_limit') != TOPUP_LIMIT
            or topup.get('budget_key') != base['budget_key'] or not topup.get('approval_reference')):
        raise ValueError('auxiliary_research_topup_invalid')
    result = dict(base, call_limit=TOPUP_LIMIT, funding_sha256=topup['artifact_content_sha256'])
    continuation = root(data_root) / 'allowance-topup-600.json'
    if continuation.exists():
        value = read(continuation)
        if (value.get('schema') != SCHEMA or value.get('research_id') != RESEARCH_ID
                or value.get('authority') != CONTINUATION_AUTHORITY
                or value.get('previous_funding_sha256') != topup['artifact_content_sha256']
                or value.get('from_limit') != TOPUP_LIMIT or value.get('call_limit') != CONTINUATION_LIMIT
                or value.get('budget_key') != base['budget_key'] or not value.get('approval_reference')):
            raise ValueError('auxiliary_research_continuation_invalid')
        result.update(call_limit=CONTINUATION_LIMIT, funding_sha256=value['artifact_content_sha256'])
    followup = root(data_root) / 'allowance-topup-800.json'
    if followup.exists():
        value = read(followup)
        if (result['call_limit'] != CONTINUATION_LIMIT or value.get('schema') != SCHEMA
                or value.get('research_id') != RESEARCH_ID or value.get('authority') != FOLLOWUP_AUTHORITY
                or value.get('previous_funding_sha256') != result['funding_sha256']
                or value.get('from_limit') != CONTINUATION_LIMIT or value.get('call_limit') != FOLLOWUP_LIMIT
                or value.get('budget_key') != base['budget_key'] or not value.get('approval_reference')):
            raise ValueError('auxiliary_research_followup_invalid')
        result.update(call_limit=FOLLOWUP_LIMIT, funding_sha256=value['artifact_content_sha256'])
    return result


def authorize_followup(data_root, *, confirm, approval_reference):
    if confirm != FOLLOWUP_AUTHORITY or not approval_reference:
        raise ValueError('auxiliary_research_followup_authority_required')
    with S.Store(data_root):
        previous = budget(data_root)
        if previous['call_limit'] not in {CONTINUATION_LIMIT, FOLLOWUP_LIMIT}:
            raise ValueError('auxiliary_research_previous_funding_required')
        topup = read(root(data_root) / 'allowance-topup-600.json')
        value = P.seal(dict(schema=SCHEMA, research_id=RESEARCH_ID, authority=FOLLOWUP_AUTHORITY,
            previous_funding_sha256=topup['artifact_content_sha256'], from_limit=CONTINUATION_LIMIT,
            call_limit=FOLLOWUP_LIMIT, budget_key=previous['budget_key'],
            approval_reference=approval_reference, **P.AUTH))
        immutable(root(data_root) / 'allowance-topup-800.json', value)
    return budget(data_root)


def authorize_continuation(data_root, *, confirm, approval_reference):
    if confirm != CONTINUATION_AUTHORITY or not approval_reference:
        raise ValueError('auxiliary_research_continuation_authority_required')
    with S.Store(data_root):
        previous = budget(data_root)
        if previous['call_limit'] not in {TOPUP_LIMIT, CONTINUATION_LIMIT}:
            raise ValueError('auxiliary_research_previous_funding_required')
        topup = read(root(data_root) / 'allowance-topup-400.json')
        value = P.seal(dict(schema=SCHEMA, research_id=RESEARCH_ID, authority=CONTINUATION_AUTHORITY,
            previous_funding_sha256=topup['artifact_content_sha256'], from_limit=TOPUP_LIMIT,
            call_limit=CONTINUATION_LIMIT, budget_key=previous['budget_key'],
            approval_reference=approval_reference, **P.AUTH))
        immutable(root(data_root) / 'allowance-topup-600.json', value)
    return budget(data_root)


def authorize_topup(data_root, *, confirm, approval_reference):
    if confirm != TOPUP_AUTHORITY or not approval_reference:
        raise ValueError('auxiliary_research_topup_authority_required')
    base=grant(data_root)
    value=P.seal(dict(schema=SCHEMA,research_id=RESEARCH_ID,authority=TOPUP_AUTHORITY,
        base_allowance_sha256=base['artifact_content_sha256'],from_limit=LIMIT,call_limit=TOPUP_LIMIT,
        budget_key=base['budget_key'],approval_reference=approval_reference,**P.AUTH))
    with S.Store(data_root):
        immutable(root(data_root)/'allowance-topup-400.json',value)
    return budget(data_root)


def current_bindings(data_root, parent):
    """Use an actual reader capture when research code has a different hash.

    This is an offline baseline, never a substitute for the publisher's live
    parent and reader validation. The immutable release validates inheritance
    before producing the capture.
    """
    from src.engine.scalping import reversal_auxiliary_intraday as I
    path=root(data_root)/'current-bindings'/(parent['bundle_sha256']+'.json')
    if not path.exists():return I.effective_bindings(data_root,parent)
    value=read(path)
    if (value.get('parent_bundle_sha256')!=parent['bundle_sha256']
            or value.get('family_sha256')!=parent['continuous_reversal']['family_sha256']
            or value.get('reader_validated') is not True or not value.get('source_receipts')):
        raise ValueError('auxiliary_research_binding_capture_invalid')
    for receipt in value['source_receipts']:
        if P.file_hash(receipt['path'])!=receipt['sha256']:
            raise ValueError('auxiliary_research_binding_capture_source_changed')
    from src.engine.scalping import continuous_reversal_policy_v5 as V
    family=parent['continuous_reversal']
    expected={V.scope_id(key,route) for key,route in V.scopes()
              if family['machine_cells'][key]['routes'][route]['backend'] in {'union_v5','union_v6'}}
    if set(value.get('bindings',{}))!=expected:
        raise ValueError('auxiliary_research_binding_capture_scope_changed')
    for sid,ident in value['bindings'].items():
        key,route=sid.rsplit('|',1)
        if G.load(data_root,ident)['input_version']!=parent['continuous_reversal']['auxiliary_cells'][key]['routes'][route]['payload']['binding']['input_version']:
            raise ValueError('auxiliary_research_binding_capture_version_changed')
    return value['bindings']


def immutable(path, value):
    if Path(path).exists():
        if read(path) != value:
            raise ValueError('auxiliary_research_immutable_conflict')
    else:
        S.atomic_json(path, value)


def authorize(data_root, *, confirm, source_dates, approval_reference):
    from datetime import date
    if confirm != AUTHORITY or not approval_reference or not source_dates:
        raise ValueError('auxiliary_research_authority_required')
    dates = sorted(set(source_dates))
    for day in dates:
        if date.fromisoformat(day).isoformat() != day or not '2026-06-05' <= day <= '2026-10-08':
            raise ValueError('auxiliary_research_source_date_invalid')
    v = P.seal(dict(schema=SCHEMA, research_id=RESEARCH_ID, authority=AUTHORITY,
                    call_limit=LIMIT, budget_key='research_auxiliary:' + RESEARCH_ID,
                    source_dates=dates, approval_reference=approval_reference, **P.AUTH))
    with S.Store(data_root):
        immutable(root(data_root) / 'allowance.json', v)
    return v


def configure(data_root, *, experiment, candidate, scopes, seed, max_pairs,
              purpose='evaluation', include_keys=(), native_current=False, resolved_only=False,
              native_output_tokens_override=None, compact_wire=False, compact_candidate_only=False):
    from src.engine.scalping import reversal_auxiliary_tuning as T
    from src.engine.scalping import continuous_reversal_policy_v5 as V
    allowance = grant(data_root)
    valid = {V.scope_id(k, r) for k, r in V.scopes()}
    if (purpose not in {'development', 'evaluation'} or not scopes or not set(scopes) <= valid
            or type(max_pairs) is not int or not 1 <= max_pairs <= 100
            or not isinstance(seed, str) or not seed
            or (include_keys and purpose != 'development')
            or (compact_candidate_only and not compact_wire)
            or (compact_wire and (native_current or native_output_tokens_override is not None))
            or (native_output_tokens_override is not None and
                (not native_current or native_output_tokens_override != 1024))):
        raise ValueError('auxiliary_research_config_invalid')
    G.load(data_root, candidate)
    cfg = dict(schema=T.SCHEMA, enabled=True, candidate_registry=candidate,
               scopes=sorted(set(scopes)), seed=seed, max_pairs=max_pairs)
    if native_current:
        cfg['native_current_contract'] = native_contract()
    if native_output_tokens_override is not None:
        cfg['native_output_tokens_override'] = native_output_tokens_override
    if resolved_only:
        cfg['resolved_only'] = True
    if compact_wire:
        from src.engine.scalping import reversal_auxiliary_research_wire as W
        cfg['compact_wire_contract'] = W.contract()
        if compact_candidate_only:
            cfg['compact_candidate_only'] = True
    v = P.seal(dict(schema=SCHEMA, research_id=RESEARCH_ID, experiment=experiment,
                    allowance_sha256=allowance['artifact_content_sha256'], purpose=purpose,
                    include_keys=sorted(set(include_keys)), config=P.seal(cfg), **P.AUTH))
    with S.Store(data_root):
        immutable(directory(data_root, experiment) / 'configuration.json', v)
    return v


def context(data_root, experiment):
    v = read(directory(data_root, experiment) / 'configuration.json')
    a = budget(data_root)
    if (v.get('schema') != SCHEMA or v.get('research_id') != RESEARCH_ID
            or v.get('experiment') != experiment or v.get('allowance_sha256') != a['artifact_content_sha256']
            or v.get('purpose') not in {'development', 'evaluation'}):
        raise ValueError('auxiliary_research_context_invalid')
    return v


def validate_campaign(data_root, campaign):
    ref = campaign['research']
    v = context(data_root, ref['experiment'])
    a = budget(data_root)
    if (ref != {k: v[k] for k in ('research_id', 'experiment', 'purpose', 'allowance_sha256')}
            or campaign['config_sha256'] != v['config']['artifact_content_sha256']
            or campaign['call_limit'] not in {LIMIT, TOPUP_LIMIT, CONTINUATION_LIMIT, FOLLOWUP_LIMIT}
            or campaign['call_limit'] > a['call_limit']
            or campaign['source_date'] not in a['source_dates']
            or any(p['day'] not in a['source_dates'] for p in campaign['pairs'])
            or any(p['candidate_registry'] != v['config']['candidate_registry'] for p in campaign['pairs'])):
        raise ValueError('auxiliary_research_campaign_invalid')
    return a


def native_contract():
    """Capture pure runtime request configuration, without a client or secrets."""
    from src.engine import ai_engine_openai as E
    engine = E.GPTSniperEngine.__new__(E.GPTSniperEngine)
    return dict(engine_sha256=P.file_hash(E.__file__), schema_name=E.ENTRY_RISK_ADJUDICATION_SCHEMA,
                max_output_tokens=engine._resolve_openai_max_output_tokens(require_json=True),
                reasoning_effort=engine._resolve_openai_reasoning_effort(model_name='gpt-5.4-nano'),
                temperature=engine._resolve_openai_temperature(require_json=True,temperature_override=None,model_name='gpt-5.4-nano'))


def request(snapshot, registry, contract=None, *, output_tokens_override=None):
    """Native-current wire replay; registry identity still names the live parent."""
    import json
    req = G.request(snapshot, registry)
    if output_tokens_override is not None and (contract is None or output_tokens_override != 1024):
        raise ValueError('auxiliary_research_output_override_invalid')
    if contract is None:
        return req
    if contract != native_contract():
        raise ValueError('auxiliary_native_wire_contract_changed')
    default=G.definition(registry['base_arm'],input_version=registry['input_version'])
    if registry['registry_sha256'] != default['registry_sha256']:
        # The actual registered-prompt path already transmits the registry's
        # exact raw prompt, typed schema and 1024-token contract. Do not wrap it
        # as a historical non-registry request or charge a duplicate replay.
        return req
    from src.engine import ai_engine_openai as E
    from src.engine.ai_prompt_contracts import CONTINUOUS_REVERSAL_AUXILIARY_PROMPT_VERSIONS
    engine = E.GPTSniperEngine.__new__(E.GPTSniperEngine)
    candidate = req['candidate']
    prompt_version = candidate['prompt_version']
    user = json.dumps(req['candidate_input'],ensure_ascii=True,sort_keys=True,separators=(',',':'))
    candidate['system_prompt'] = engine._wrap_openai_prompt_contract(candidate['system_prompt'],
        require_json=True,schema_name=contract['schema_name'],endpoint_name='analyze_target')
    req['candidate_input'] = user + ('\n\nReturn JSON only.' if 'json' not in user.lower() else '')
    candidate.update(schema_name=contract['schema_name'],max_output_tokens=contract['max_output_tokens'],
                     reasoning_effort=contract['reasoning_effort'],temperature=contract['temperature'],
                     native_wire_contract=contract)
    if prompt_version in CONTINUOUS_REVERSAL_AUXILIARY_PROMPT_VERSIONS:
        candidate.update(max_output_tokens=512,reasoning_effort='none')
    if output_tokens_override is not None:
        candidate['max_output_tokens'] = output_tokens_override
    req['candidate_input_sha256'] = P.digest(req['candidate_input'])
    req['paired_replay_id'] = P.digest([G.A.opportunity(snapshot[0]),'NATIVE_CURRENT_WIRE',
        {k:req[k] for k in ('candidate_input','candidate','control','stage')}])
    return req


def main(argv=None):
    import argparse
    import json
    import time
    from src.engine.scalping import reversal_auxiliary_tuning as T
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--experiment',required=True)
    parser.add_argument('--mode',choices=['calls','evaluate'],default='evaluate')
    parser.add_argument('--max-new-calls',type=int,default=20)
    args=parser.parse_args(argv)
    c=T.read(directory(args.data_root,args.experiment)/'latest-campaign.json')
    path=directory(args.data_root,args.experiment)/'campaigns'/(c['artifact_content_sha256']+'.json')
    calls=None
    if args.mode=='calls':
        from src.engine.scalping.ai_decision_quality import _offline_openai_api_keys
        if not _offline_openai_api_keys():
            raise ValueError('auxiliary_research_credential_unavailable')
        calls=T.calls(args.data_root,c['source_date'],campaign_path=path,
                      max_new_calls=args.max_new_calls,stop_epoch=time.time()+600)
    evaluated=T.evaluate(args.data_root,c['source_date'],campaign_path=path)
    print(json.dumps(dict(new_calls=calls['new_calls'] if calls else 0,
        call_budget=calls['call_budget'] if calls else None,
        evaluation_sha256=evaluated['artifact_content_sha256'],
        paired_points=sum(v['paired_points'] for v in evaluated['scopes'].values()),
        improved_scopes=[s for s,v in evaluated['scopes'].items() if v['improved']],
        runtime_effect=False)))


if __name__=='__main__':
    main()
