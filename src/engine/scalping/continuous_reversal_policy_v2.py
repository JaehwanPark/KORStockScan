"""Native multi-branch policy: candidate publication, CAS activation and evaluation."""
from __future__ import annotations

import copy
import fcntl
import json
import re
from datetime import datetime
from fractions import Fraction
from pathlib import Path

from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_branches as B
from src.engine.scalping import reversal_auxiliary_phases as A
from src.engine.scalping import reversal_auxiliary_contract as V1
from src.engine.scalping.continuous_reversal_postclose import digest, file_hash, expected_cells

SCHEMA = "continuous_reversal_policy_v2"


def validate_family(family):
    if (family.get("schema") != SCHEMA or family.get("kernel_version") != K.VERSION
            or family.get("branch_registry_version") != B.VERSION
            or family.get("branch_definition_sha256") != B.DEFINITION_SHA256
            or family.get("auxiliary_version") != A.VERSION
            or family.get("selection_metric") != "cumulative_raw_win_fraction"
            or family.get("label_contract") != dict(target_net_pct=.4,stop_net_pct=-3.,cost_rate=.0023,horizon_seconds=1800)
            or family.get("family_sha256") != digest({k:v for k,v in family.items() if k!="family_sha256"})):
        raise ValueError("reversal_v2_family_contract_invalid")
    if (family.get('effective_mode') not in {'intraday','next_session'}
            or re.fullmatch(r'[0-9a-f]{40}',str(family.get('release_commit') or '')) is None
            or re.fullmatch(r'[0-9a-f]{64}',str(family.get('parent_bundle_sha256') or '')) is None):
        raise ValueError('reversal_v2_release_parent_invalid')
    for name in ("machine_cells", "auxiliary_cells"):
        cells = family.get(name)
        if not isinstance(cells,dict) or set(cells)!=set(expected_cells()):
            raise ValueError("reversal_v2_twelve_cell_coverage_invalid")
        for key,cell in cells.items():
            p=cell.get("payload")
            if cell.get("payload_sha256") != digest(p):
                raise ValueError("reversal_v2_cell_hash_invalid")
            if name=="machine_cells":
                B.validate_payload(p,key)
                fractions = cell.get("branch_metrics",{})
                if set(fractions)!={b["branch_id"] for b in p["branches"]}:
                    raise ValueError("reversal_v2_branch_metrics_coverage_invalid")
                for m in fractions.values():
                    if m is not None and (type(m.get("wins")) is not int or type(m.get("resolved")) is not int
                                          or not 0<=m["wins"]<=m["resolved"] or m["resolved"]<=0):
                        raise ValueError("reversal_v2_fraction_invalid")
            else:
                if set(p)!={"phase_policies"}:
                    raise ValueError("reversal_v2_phase_payload_invalid")
                required={b["decision_phase"] for b in family["machine_cells"][key]["payload"]["branches"]}
                if set(p["phase_policies"])!=required:
                    raise ValueError("reversal_v2_phase_coverage_invalid")
                for phase, policy in p["phase_policies"].items():
                    arm=policy.get("arm")
                    if arm not in V1.ARMS or policy.get("binding") != A.binding(phase,arm):
                        raise ValueError("reversal_v2_phase_binding_invalid")
                    if policy.get("local_metrics") is None and not policy.get("carry_source"):
                        raise ValueError("reversal_v2_phase_carry_missing")
                    metric=policy.get('local_metrics')
                    if metric is not None and (type(metric.get('pass_count')) is not int or type(metric.get('pass_wins')) is not int
                            or not 0<=metric['pass_wins']<=metric['pass_count'] or metric['pass_count']<=0):
                        raise ValueError('reversal_v2_auxiliary_fraction_invalid')
                    if phase==B.CONFIRMED and not policy.get("actual_response_evidence"):
                        raise ValueError("reversal_v2_confirmed_actual_response_missing")
            if cell.get("inherited_from") and (cell.get("local_metrics") is not None
                    or cell.get("parent_payload_sha256") != digest(p)):
                raise ValueError("reversal_v2_inheritance_invalid")


def validate_sources(bundle,data_root):
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    f=bundle["continuous_reversal"];validate_family(f)
    modules=(K,B,A,V1)
    for module in modules:
        path=Path(module.__file__)
        native._signature(path)
        if f["contract_file_sha256"].get(path.name)!=file_hash(path):
            raise ValueError("reversal_v2_issued_contract_code_changed:"+path.name)
    for name in ("machine","auxiliary"):
        path=native.root(data_root)/"sources"/f"reversal-{f[name+'_report_sha256']}.json"
        if native._source_hash(str(path),native._signature(path))!=f["report_file_sha256"][name]:
            raise ValueError("reversal_v2_report_snapshot_changed")
        report=native._read(path)
        if (report.get("source_date")!=f["source_date"] or report.get("status")!="completed"
                or report.get("artifact_content_sha256")!=digest({k:v for k,v in report.items() if k!="artifact_content_sha256"})
                or {c['key']:c for c in report['cells']}!=f[name+"_cells"]):
            raise ValueError("reversal_v2_report_binding_invalid")
        for record in report.get("results_sources",[])+report.get("source_receipts",[]):
            path=Path(record["path"])
            if native._source_hash(str(path),native._signature(path))!=record["sha256"]:
                raise ValueError("reversal_v2_frozen_source_changed")
    for cell in f['auxiliary_cells'].values():
        for policy in cell['payload']['phase_policies'].values():
            records=policy.get('actual_response_evidence') or []
            if isinstance(records,dict):records=[records]
            for record in records:
                path=Path(record['path'])
                if native._source_hash(str(path),native._signature(path))!=record['sha256']:
                    raise ValueError('reversal_v2_phase_actual_evidence_changed')
    return bundle


def assess(family,snapshot,*,symbol,session,build_request=True):
    validate_family(family)
    result=dict(schema="mechanistic_entry_policy_decision_v1",action="BLOCK",reason="no_current_reversal_signal",
                policy_version=SCHEMA,primary_decision_owner="mechanistic_entry_adjudicator",
                ai_role="auxiliary_risk_screen_pass_veto_no_promotion",price_reversal_confirmed=False,
                runtime_effect=False,allowed_runtime_apply=False,actual_order_submitted=False,broker_order_forbidden=True)
    if snapshot is None:return result,None,None,None
    event,source=snapshot
    if event["symbol"]!=symbol or event["market"]!=K.market_bucket(session):
        raise ValueError("reversal_v2_snapshot_scope_conflict")
    key=K.cell_key(symbol,session,event["confirmation_price"])
    cell=family["machine_cells"][key];matched=[];states=[]
    phase=event.get("decision_phase",B.FIRST)
    for branch in cell["payload"]["branches"]:
        if branch["kind"]=="legacy_rule":
            first=event if phase==B.FIRST else event.get("coincident_first")
            if first is None:
                states.append(dict(branch_id=branch["branch_id"],status="not_applicable_phase"));continue
            rule=branch["rule"]
            missing=("VOL" in rule and first.get("volume_ratio_60s") is None) or (rule.startswith("DD5") and first.get("drawdown_5m_pct") is None)
            passed=K.conditions(first)[rule]
        else:
            applicable=(symbol,event["market"],event["venue"],event["source_item"])==("005930","REGULAR","SOR","005930_AL")
            if not applicable:
                states.append(dict(branch_id=branch["branch_id"],status="not_applicable_scope"));continue
            missing=phase!=B.CONFIRMED and event.get('registered_branch_state') in {'pending_confirmation','required_feature_missing'}
            passed=phase==B.CONFIRMED and event.get("branch_definition_sha256")==B.DEFINITION_SHA256
        states.append(dict(branch_id=branch["branch_id"],status="matched" if passed else "condition_missing" if missing else "condition_not_met"))
        if passed:matched.append(branch)
    result.update(cell_key=key,event_id=event["event_id"],signal_id=event.get("signal_id",event["event_id"]),event=event,
                  matched_branches=[b["branch_id"] for b in matched],branch_states=states,
                  branch_definition_sha256=B.DEFINITION_SHA256,machine_component_sha256=digest(family["machine_cells"]),
                  family_sha256=family["family_sha256"],price_reversal_confirmed=True)
    if event["entry_ask"] is None:
        result.update(action="RECHECK",reason="entry_quote_source_missing");return result,None,None,None
    if not matched:
        result.update(action="RECHECK" if any(s["status"]=="condition_missing" for s in states) else "BLOCK",
                      reason="registered_reversal_condition_pending_or_missing" if any(s["status"]=="condition_missing" for s in states) else "selected_reversal_condition_not_met")
        return result,None,None,None
    order={b["branch_id"]:i for i,b in enumerate(cell["payload"]["branches"])}
    def rank(branch):
        m=cell["branch_metrics"].get(branch["branch_id"])
        return (m is not None,Fraction(m["wins"],m["resolved"]) if m else Fraction(0),-order[branch["branch_id"]])
    primary=max(matched,key=rank);phase=primary["decision_phase"]
    policy=family["auxiliary_cells"][key]["payload"]["phase_policies"][phase]
    result.update(action="ENTER_NOW",reason="continuous_reversal_branch_union_pass",primary_branch=primary["branch_id"],
                  decision_phase=phase,auxiliary_arm=policy["arm"],auxiliary_binding=policy["binding"],
                  primary_rank_reason="raw_fraction_then_frozen_order" if cell["branch_metrics"][primary["branch_id"]] else "frozen_order_without_fraction")
    if phase==B.FIRST and event.get('decision_phase')==B.CONFIRMED:
        result['auxiliary_event']=event['coincident_first']
        source=event.get('coincident_first_input')
        if build_request and source is None:raise ValueError('reversal_coincident_first_input_missing')
    else:result['auxiliary_event']=event
    if not build_request:return result,None,None,None
    inp,prompt,schema=A.production_request(source,policy["arm"],phase=phase,event=event)
    return result,inp,prompt,schema


def stage(data_root,day,publication,machine,auxiliary,*,target_date,release_commit,effective_mode="next_session"):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    root=N.root(Path(data_root));root.mkdir(parents=True,exist_ok=True)
    if effective_mode not in {"next_session","intraday"} or (effective_mode=="next_session" and target_date!=N.next_target(publication)):
        raise ValueError("reversal_v2_target_mode_invalid")
    if effective_mode=="intraday" and target_date!=publication:
        raise ValueError("reversal_v2_intraday_date_invalid")
    if not re.fullmatch(r"[0-9a-f]{40}",release_commit):raise ValueError("reversal_v2_release_commit_missing")
    for report in (machine,auxiliary):
        if (report.get('artifact_content_sha256')!=digest({k:v for k,v in report.items() if k!='artifact_content_sha256'})
                or report.get('status')!='completed' or report.get('source_date')!=day
                or report.get('publication_date')!=publication):raise ValueError('reversal_v2_report_preflight_invalid')
    if auxiliary.get('machine_report_sha256')!=machine['artifact_content_sha256']:
        raise ValueError('reversal_v2_auxiliary_machine_parent_invalid')
    if (effective_mode not in {'intraday','next_session'} or day>publication
            or target_date!=(publication if effective_mode=='intraday' else N.next_target(publication))):
        raise ValueError('reversal_v2_effective_date_invalid')
    with (root/"publisher.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        parent=N.load_effective(data_root=Path(data_root),target_date=publication)
        if not parent:raise ValueError("reversal_v2_parent_missing")
        if machine.get('parent_bundle_sha256')!=parent['bundle_sha256']:
            raise ValueError('reversal_v2_report_incumbent_parent_changed')
        hashes={}
        for name,report in (("machine",machine),("auxiliary",auxiliary)):
            path=root/"sources"/f"reversal-{report['artifact_content_sha256']}.json"
            N._atomic_write_json(path,report);hashes[name]=file_hash(path)
        f=dict(schema=SCHEMA,kernel_version=K.VERSION,branch_registry_version=B.VERSION,
               branch_definition_sha256=B.DEFINITION_SHA256,auxiliary_version=A.VERSION,
               source_date=day,publication_date=publication,effective_date=target_date,effective_mode=effective_mode,
               selection_metric="cumulative_raw_win_fraction",label_contract=machine["label_contract"],
               machine_report_sha256=machine["artifact_content_sha256"],auxiliary_report_sha256=auxiliary["artifact_content_sha256"],
               report_file_sha256=hashes,kernel_sha256=file_hash(K.__file__),
               contract_file_sha256={Path(m.__file__).name:file_hash(m.__file__) for m in (K,B,A,V1)},
               source_manifest_sha256=machine["source_manifest_sha256"],
               machine_cells={c['key']:c for c in machine['cells']},auxiliary_cells={c['key']:c for c in auxiliary['cells']},
               parent_bundle_sha256=parent['bundle_sha256'],release_commit=release_commit,
               hard_guards_unchanged=True,actual_order_submitted=False)
        f["family_sha256"]=digest(f);validate_family(f)
        bundle=copy.deepcopy(parent)
        for name in ("strategy_activation","winrate_selection","machine_evaluation_source","compact_evaluation_source"):
            bundle.pop(name,None)
        bundle.update(source_date=day,publication_date=publication,target_date=target_date,
                      generated_at=datetime.now(K.KST).isoformat(),continuous_reversal=f,
                      previous_bundle_sha256=parent["bundle_sha256"],machine_disposition="continuous_reversal_selected",
                      compact_prompt_disposition="continuous_reversal_selected")
        source=dict(schema=SCHEMA,source_date=day,target_date=target_date,continuous_reversal=f,artifact_content_sha256=digest(f))
        source_path=root/"sources"/(digest(source)+".json")
        N._atomic_write_json(source_path,source)
        # The native source filename is the physical file digest.
        real=root/"sources"/(file_hash(source_path)+".json")
        if real!=source_path:N._atomic_write_json(real,source)
        bundle.update(source_file_sha256=file_hash(real),source_artifact_sha256=digest(f))
        bundle.pop("bundle_sha256",None);bundle["bundle_sha256"]=digest(bundle)
        N.validate(bundle,target_date=target_date);N._validate_bundle_sources(bundle,Path(data_root))
        N._atomic_write_json(root/"generations"/(bundle['bundle_sha256']+".json"),bundle)
        N._atomic_write_json(root/"candidates"/f"policy_{target_date}.json",bundle)
        return bundle


def load_candidate(data_root,target_date):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    bundle=N._read(N.root(Path(data_root))/"candidates"/f"policy_{target_date}.json")
    N.validate(bundle,target_date=target_date)
    if bundle["continuous_reversal"]["schema"]!=SCHEMA:raise ValueError("reversal_v2_candidate_schema_invalid")
    return N._validate_bundle_sources(bundle,Path(data_root))


def activate(data_root,target_date,*,now=None,intraday_evidence=None):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.infrastructure.runtime_release_router import selected_release
    clock=now or datetime.now(K.KST)
    if clock.astimezone(K.KST).date().isoformat()!=target_date:raise ValueError("reversal_v2_activation_not_today")
    root=N.root(Path(data_root))
    with (root/"publisher.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        bundle=load_candidate(data_root,target_date);family=bundle["continuous_reversal"]
        selected_root,commit=selected_release(Path(data_root).resolve().parent)
        # The router validates the immutable selected checkout. Activation is
        # tied to its code commit, not a workspace or a future target claim.
        if commit!=family["release_commit"]:raise ValueError("reversal_v2_activation_release_mismatch")
        if family['effective_mode']=='intraday':
            from src.engine.automation.intraday_release_handoff import _identity
            e=intraday_evidence or {}
            if (e.get('schema')!='intraday_main_policy_code_pid_v1' or e.get('target_date')!=target_date
                    or e.get('release_commit')!=commit or not e.get('pid_identity')
                    or _identity(e['pid_identity']['pid'])!=e['pid_identity']
                    or e['pid_identity']['cwd']!=str(selected_root/'src')
                    or file_hash(e['consumed_path'])!=e.get('consumed_sha256')):
                raise ValueError('reversal_v2_intraday_code_pid_not_verified')
        parent=N._load_current(Path(data_root),target_date)
        if parent and parent["bundle_sha256"]==bundle["bundle_sha256"]:
            return dict(status="already_active",bundle_sha256=bundle["bundle_sha256"])
        if not parent or parent["bundle_sha256"]!=family["parent_bundle_sha256"]:
            raise ValueError("reversal_v2_activation_parent_cas_failed")
        receipt=dict(schema="continuous_reversal_current_v2",bundle_sha256=bundle["bundle_sha256"],
                     previous_bundle_sha256=parent["bundle_sha256"],effective_from=clock.isoformat(),
                     effective_date=target_date,family_sha256=family["family_sha256"],release_commit=commit)
        if intraday_evidence:receipt['intraday_code_pid_evidence']=intraday_evidence
        receipt["receipt_sha256"]=digest(receipt)
        # Until current.json commits the generation, effective resolution must
        # ignore the new dated v2 bytes and retain the current parent.
        # Preserve the original PREOPEN dated file. Intraday adoption changes
        # only the native current pointer, after the new code PID is verified.
        N._atomic_write_json(root/"current.json",receipt)
        if N.load_effective(data_root=Path(data_root),target_date=target_date)["bundle_sha256"]!=bundle["bundle_sha256"]:
            raise ValueError("reversal_v2_activation_readback_failed")
        return dict(status="activated",**receipt)


_CONSUMED=set()


def record_pid_consumption(data_root,bundle):
    """Executed by the actual Main consumer, never by the activation CLI."""
    import os
    from src.engine.automation.intraday_release_handoff import _identity
    from src.engine.infrastructure.runtime_release_router import selected_release
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    identity=_identity(os.getpid());key=(identity['start_ticks'],bundle['bundle_sha256'])
    if key in _CONSUMED:return
    selected,commit=selected_release(Path(data_root).resolve().parent)
    if identity['cwd']!=str(selected/'src') or commit!=bundle['continuous_reversal']['release_commit']:
        raise ValueError('reversal_v2_consumption_release_mismatch')
    current=N._load_current(Path(data_root),datetime.now(K.KST).date().isoformat())
    if not current or current['bundle_sha256']!=bundle['bundle_sha256']:
        raise ValueError('reversal_v2_consumption_generation_changed')
    receipt=dict(schema='continuous_reversal_pid_consumption_v2',bundle_sha256=bundle['bundle_sha256'],
                 family_sha256=bundle['continuous_reversal']['family_sha256'],release_commit=commit,pid_identity=identity,
                 observed_at=datetime.now(K.KST).isoformat(),actual_pid_consumed=True,actual_order_submitted=False)
    receipt['receipt_sha256']=digest(receipt)
    N._atomic_write_json(N.root(Path(data_root))/'consumed'/datetime.now(K.KST).date().isoformat()/(str(os.getpid())+'.json'),receipt)
    _CONSUMED.add(key)
