"""Postclose deterministic tuner for the standalone BUY cancel-wait runtime."""

from __future__ import annotations

import argparse
import gzip
import json
import ast
import hashlib
import os
import tempfile
import math
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path
from typing import Any, Iterable

from src.engine.scalping.entry_cancel_wait_runtime import (
    DEFAULT_THRESHOLDS,
    POLICY_VERSION,
    RUNTIME_FAMILY,
    KST,
)
from src.utils.constants import DATA_DIR

REPORT_DIR = DATA_DIR / "report" / "entry_cancel_wait_tuning"
SAMPLE_FLOOR = 5
EXECUTABLE_EVIDENCE_DATE = "2026-09-17"


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"entry_cancel_wait_tuning_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _event_path(target_date: str) -> Path:
    plain = DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    return plain if plain.exists() else plain.with_suffix(plain.suffix + ".gz")


def _iter_events(target_date: str) -> Iterable[dict[str, Any]]:
    path = _event_path(target_date)
    if not path.exists():
        return
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except Exception:
                continue
            if isinstance(row, dict):
                yield row


def _latest_previous_thresholds(target_date: str) -> dict[str, int]:
    thresholds = dict(DEFAULT_THRESHOLDS)
    for path in sorted(
        REPORT_DIR.glob("entry_cancel_wait_tuning_*.json"), reverse=True
    ):
        report_date = path.stem.removeprefix("entry_cancel_wait_tuning_")
        if report_date >= target_date:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        values = payload.get("recommended_thresholds")
        if isinstance(values, dict):
            for profile in thresholds:
                if int(values.get(profile, 0) or 0) > 0:
                    thresholds[profile] = int(values[profile])
            break
    return thresholds


def _bounded_next(profile: str, previous: int, proposed: int) -> int:
    if profile in {"standard", "breakout"}:
        delta = 30
    else:
        delta = max(1, int(round(previous * 0.10)))
    return max(5, min(1200, max(previous - delta, min(previous + delta, proposed))))


def _build_legacy_report(target_date: str) -> dict[str, Any]:
    previous = _latest_previous_thresholds(target_date)
    source_path = _event_path(target_date)
    completed: dict[str, dict[int, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    registered = defaultdict(int)
    invalid_rows = 0
    diagnostic_proxy_rows = 0
    for event in _iter_events(target_date) or []:
        stage = str(event.get("stage") or "")
        fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
        if str(fields.get("runtime_family") or "") != RUNTIME_FAMILY:
            continue
        profile = str(fields.get("wait_profile") or "standard")
        if profile not in DEFAULT_THRESHOLDS:
            invalid_rows += 1
            continue
        if target_date >= EXECUTABLE_EVIDENCE_DATE and stage in {
            "entry_cancel_wait_counterfactual_registered",
            "entry_cancel_wait_counterfactual_completed",
        }:
            # The current runtime touch/60s-mark observer is diagnostic. Its
            # gross return is not executable, cost-adjusted tuning evidence.
            diagnostic_proxy_rows += 1
            if stage == "entry_cancel_wait_counterfactual_registered":
                registered[profile] += 1
            continue
        if stage == "entry_cancel_wait_counterfactual_registered":
            registered[profile] += 1
            try:
                actual_timeout = int(float(fields.get("actual_timeout_sec") or 0))
                candidates = [
                    int(token)
                    for token in str(fields.get("candidate_timeout_secs") or "").split(
                        "|"
                    )
                    if token.strip()
                ]
            except Exception:
                invalid_rows += 1
                continue
            for timeout in candidates:
                if timeout <= actual_timeout:
                    completed[profile][timeout].append(0.0)
        elif stage == "entry_cancel_wait_counterfactual_completed":
            try:
                timeout = int(float(fields.get("timeout_sec")))
                ev = float(fields.get("counterfactual_ev_pct"))
                if timeout <= 0 or not math.isfinite(ev):
                    raise ValueError("invalid_counterfactual_metric")
            except Exception:
                invalid_rows += 1
                continue
            completed[profile][timeout].append(ev)

    recommended = dict(previous)
    profiles: dict[str, Any] = {}
    for profile in DEFAULT_THRESHOLDS:
        candidates = []
        for timeout, values in sorted(completed[profile].items()):
            candidates.append(
                {
                    "timeout_sec": timeout,
                    "sample_count": len(values),
                    "equal_weight_avg_profit_pct": round(sum(values) / len(values), 6),
                }
            )
        eligible = [item for item in candidates if item["sample_count"] >= SAMPLE_FLOOR]
        if eligible:
            best = max(
                eligible,
                key=lambda item: (
                    item["equal_weight_avg_profit_pct"],
                    -abs(item["timeout_sec"] - previous[profile]),
                ),
            )
            recommended[profile] = _bounded_next(
                profile, previous[profile], int(best["timeout_sec"])
            )
            state = (
                "adjust"
                if recommended[profile] != previous[profile]
                else "hold_best_unchanged"
            )
        else:
            state = (
                "hold_source_contract"
                if target_date >= EXECUTABLE_EVIDENCE_DATE else "hold_sample"
            )
        profiles[profile] = {
            "previous_threshold_sec": previous[profile],
            "recommended_threshold_sec": recommended[profile],
            "registered_count": registered[profile],
            "completed_candidate_count": sum(
                len(v) for v in completed[profile].values()
            ),
            "sample_floor": SAMPLE_FLOOR,
            "calibration_state": state,
            "candidate_ev": candidates,
        }
    if invalid_rows:
        recommended = dict(previous)
        for profile, item in profiles.items():
            item["recommended_threshold_sec"] = previous[profile]
            item["calibration_state"] = "hold_source_quality"
    source_quality_status = (
        "missing_source_hold"
        if not source_path.exists()
        else "warning" if invalid_rows or diagnostic_proxy_rows else "pass"
    )
    total_registered = sum(registered.values())
    total_completed = sum(
        sum(len(values) for values in profile.values())
        for profile in completed.values()
    )
    threshold_change_supported = any(
        recommended[profile] != previous[profile] for profile in DEFAULT_THRESHOLDS
    )
    evidence_state = (
        "missing_source_hold"
        if not source_path.exists()
        else (
            "diagnostic_proxy_hold" if diagnostic_proxy_rows else "invalid_rows_warning"
            if invalid_rows or diagnostic_proxy_rows
            else (
                "no_observation_hold"
                if total_registered == 0 and total_completed == 0
                else (
                    "candidate_ready" if threshold_change_supported else "observed_hold"
                )
            )
        )
    )
    return {
        "schema_version": 1,
        "report_type": "entry_cancel_wait_tuning",
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "runtime_family": RUNTIME_FAMILY,
        "policy_version": POLICY_VERSION,
        "decision_authority": "entry_cancel_wait_deterministic_ev_only",
        "runtime_effect": False,
        "allowed_runtime_apply": True,
        "standalone_operational_family": True,
        "excluded_consumers": [
            "ADM",
            "LDM",
            "lifecycle_bucket",
            "threshold_cycle_ev",
            "runtime_apply_bridge",
        ],
        "source_quality_status": source_quality_status,
        "invalid_row_count": invalid_rows,
        "diagnostic_proxy_row_count": diagnostic_proxy_rows,
        "economic_tuning_input_allowed": (
            target_date < EXECUTABLE_EVIDENCE_DATE and total_completed > 0 and not invalid_rows
        ),
        "economic_source_gap": (
            "touch_mark_proxy_missing_executable_fill_exit_cost"
            if target_date >= EXECUTABLE_EVIDENCE_DATE else None
        ),
        "evidence_summary": {
            "state": evidence_state,
            "registered_count": total_registered,
            "completed_candidate_count": total_completed,
            "threshold_change_supported": threshold_change_supported,
            "carry_forward_applied": not threshold_change_supported,
        },
        "enabled": True,
        "automatic_off_allowed": False,
        "previous_thresholds": previous,
        "recommended_thresholds": recommended,
        "profiles": profiles,
    }


def _digest(value):
    from src.engine.scalping.strategy_owner_components import digest
    return digest(value)


def _implementation():
    root=Path(__file__).resolve().parents[3]
    paths=(Path(__file__).resolve(),root/'src/engine/scalping/entry_cancel_wait_runtime.py',
        root/'src/engine/scalping/entry_split_order_plan.py',root/'src/engine/scalping/strategy_owner_replay.py',
        root/'src/engine/pipeline_event_summary.py',root/'src/utils/pipeline_event_logger.py')
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def _object(value):
    if isinstance(value, dict):return value
    if not isinstance(value, str) or len(value) > 2*1024*1024:return {}
    try:return json.loads(value)
    except ValueError:return ast.literal_eval(value)


def _atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=path.name+'.')
    try:
        with os.fdopen(fd, 'w') as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write('\n');handle.flush();os.fsync(handle.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)


def _incumbent(target_date):
    keys = ('SCALPING_ENTRY_TIMEOUT_SEC','SCALPING_BREAKOUT_ENTRY_TIMEOUT_SEC',
            'SCALPING_PULLBACK_ENTRY_TIMEOUT_SEC','SCALPING_RESERVE_ENTRY_TIMEOUT_SEC')
    values = dict(DEFAULT_THRESHOLDS)
    runtime_dir=DATA_DIR/'runtime'/'policy_bootstrap'
    for path in sorted(runtime_dir.glob('runtime_policy_bootstrap_????-??-??.json'),reverse=True):
        if 'verify' in path.stem:continue
        day=path.stem[-10:]
        if day > target_date or day < '2026-06-05' or path.is_symlink():continue
        payload=json.loads(path.read_text())
        if str(payload.get('date') or payload.get('target_date') or '') != day:continue
        verify=runtime_dir/f'runtime_policy_bootstrap_verify_{day}.json'
        if not verify.exists() or json.loads(verify.read_text()).get('status')!='pass':continue
        env=payload.get('env_overrides') or {}
        for profile,key in zip(values,keys):
            value=int(env.get('KORSTOCKSCAN_'+key,values[profile]))
            if 5 <= value <= 1200:values[profile]=value
        scopes=[]
        policy_file=env.get('KORSTOCKSCAN_ENTRY_CANCEL_WAIT_POLICY_FILE')
        if policy_file:
            p=Path(policy_file)
            raw=p.read_bytes()
            if p.is_symlink() or hashlib.sha256(raw).hexdigest()!=env.get('KORSTOCKSCAN_ENTRY_CANCEL_WAIT_POLICY_SHA256'):
                raise ValueError('incumbent_scoped_policy_hash_invalid')
            policy=json.loads(raw)
            if policy.get('sha256')!=_digest({k:v for k,v in policy.items() if k!='sha256'}) or policy.get('effective_date')!=day:
                raise ValueError('incumbent_scoped_policy_date_invalid')
            scopes=policy.get('scope_overrides') or []
        return values,dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            previous_scope_overrides=scopes,actual_pid_consumed=False)
    return values,dict(path=None,reason='defaults_no_verified_manifest',actual_pid_consumed=False)


def _current_sources(target_date):
    from src.engine.scalping import entry_split_order_plan as entry
    from src.engine.pipeline_event_summary import CANCEL_WAIT_SUMMARY_STAGES
    try:
        events, projection=entry._bounded_execution_projection(target_date,stages=CANCEL_WAIT_SUMMARY_STAGES,
            families=('dynamic_entry_price_resolver','entry_price_execution_quality'))
    except (OSError,ValueError,TypeError,KeyError) as exc:
        events,projection=[],dict(status='source_gap',reason=str(exc),raw_not_read=True)
    registry,registry_contract=entry._execution_registry_snapshot()
    outcomes,outcome_contract=entry._bounded_actual_entry_outcomes(target_date)
    quality=entry._source_quality_summary(target_date)
    return events,registry,outcomes,dict(projection=projection,registry=registry_contract,
        actual_outcomes=outcome_contract,source_quality=quality)


def _parents(target_date, events, registry):
    inventory={};fills=defaultdict(list)
    for event in registry:
        if event.get('owner_type') != 'main_scalping' or event.get('side') != 'BUY' or event.get('action') != 'NEW':continue
        key=event.get('intent_id')
        inventory.setdefault(key,{}).update(event)
        if event.get('event') == 'FILL_RECORDED':fills[key].append(event)
    by_number={}
    for key,v in inventory.items():
        if not v.get('broker_order_no'):continue
        no=(v.get('order_date'),str(v['broker_order_no']))
        if no in by_number and by_number[no][0]!=key:raise ValueError('submission_account_order_identity_conflict')
        by_number[no]=(key,v)
    parents={};unclassified=0;joined=set()
    for event in events:
        if event.get('stage') != 'entry_cancel_wait_submission' or event.get('emitted_date') != target_date:continue
        f=event.get('fields') or {};context=_object(f.get('entry_cancel_wait_submission_context'))
        if (not isinstance(context,dict) or context.get('sha256') != _digest({k:v for k,v in context.items() if k!='sha256'})
            or context.get('source_date') != target_date):
            raise ValueError('submission_context_hash_or_date_invalid')
        identity=str(f.get('owner_registry_intent_id') or '')
        actual=inventory.get(identity)
        if not actual:
            pair=by_number.get((target_date,str(f.get('broker_order_no'))));identity,actual=pair if pair else ('',None)
        if not actual:
            unclassified+=1;continue
        joined.add(identity)
        seed=context.get('seed') or {};parent=context.get('parent_id') or 'unclassified:'+identity
        if seed and (seed.get('operating_contract') or {}).get('broker_route')!=context['broker_route']:
            raise ValueError('submission_frozen_seed_broker_route_conflict')
        if (actual.get('order_date')!=target_date or actual.get('quantity')!=context['requested_qty']
            or actual.get('symbol')!=context.get('stock_code') or actual.get('route')!=context['broker_route']):
            raise ValueError('submission_owner_quantity_symbol_route_conflict')
        p=parents.setdefault(parent,dict(parent_id=parent,source_date=target_date,seed=seed,
            incumbent_timeout_sec=context['actual_timeout_sec'],profile=context['wait_profile'],children={}))
        if p['seed'] != seed or p['incumbent_timeout_sec'] != context['actual_timeout_sec']:
            raise ValueError('submission_parent_context_conflict')
        child=dict(quantity=actual.get('quantity'),submitted_price=context['submitted_price'],
            submitted_at=context['frozen_at'],terminal_at=actual.get('observed_at_kst'),fills=fills[identity],
            terminal_reconciled=actual.get('state')=='ORDER_TERMINAL' and bool(actual.get('terminal_reconciliation')),
            child_id=context['child_id'],intent_id=identity,broker_order_no=actual.get('broker_order_no'))
        if identity in p['children'] and p['children'][identity] != child:raise ValueError('conflicting_submission_child')
        p['children'][identity]=child
    for identity,actual in inventory.items():
        if actual.get('order_date')!=target_date or identity in joined:continue
        client=str(actual.get('client_intent_id') or '')
        if ':AVG_DOWN:' in client or ':PYRAMID:' in client:continue
        # Missing producer events, unknown actions and rejected/ambiguous owner
        # attempts remain in the census; a verified projection zero is not enough.
        unclassified+=1
    return list(parents.values()),unclassified


def _previous_state(target_date):
    from src.engine.scalping.entry_cancel_wait_runtime import ECONOMIC_SCHEMA
    for path in sorted(REPORT_DIR.glob('entry_cancel_wait_tuning_*.json'),reverse=True):
        day=path.stem[-10:]
        if not '2026-06-05' <= day < target_date or path.is_symlink() or path.stat().st_size>64*1024*1024:continue
        payload=json.loads(path.read_text());state=payload.get('economic_state') or {}
        if payload.get('economic_schema') != ECONOMIC_SCHEMA:continue
        if state.get('sha256') != _digest({k:v for k,v in state.items() if k!='sha256'}):
            raise ValueError('cancel_wait_predecessor_state_invalid')
        from src.engine.scalping import entry_split_order_plan as entry
        from src.engine.pipeline_event_summary import CANCEL_WAIT_SUMMARY_STAGES
        registry,registry_contract=entry._execution_registry_snapshot()
        if state.get('parents') and registry_contract.get('status')!='verified':
            raise ValueError('cancel_wait_predecessor_registry_unverified')
        for source_day in set(state.get('source_counts',{}))|{p['source_date'] for p in state.get('parents',[])}:
            original,contract=entry._bounded_execution_projection(source_day,stages=CANCEL_WAIT_SUMMARY_STAGES,
                families=('dynamic_entry_price_resolver','entry_price_execution_quality'))
            retained=[e for e in state.get('source_events',[]) if e.get('emitted_date')==source_day]
            if contract.get('status')!='ready' or {_digest(e) for e in original}!={_digest(e) for e in retained}:
                raise ValueError('cancel_wait_predecessor_original_projection_changed:'+source_day)
            reconstructed,_=_parents(source_day,original,registry)
            immutable=lambda p:(p['seed'],p['profile'],p['incumbent_timeout_sec'],
                {key:{k:c[k] for k in ('quantity','submitted_price','submitted_at','child_id','intent_id','broker_order_no')}
                 for key,c in p['children'].items()})
            originals={p['parent_id']:immutable(p) for p in reconstructed}
            if any(originals.get(p['parent_id'])!=immutable(p) for p in state.get('parents',[]) if p['source_date']==source_day):
                raise ValueError('cancel_wait_predecessor_frozen_context_changed:'+source_day)
        relevant={p['parent_id'] for p in state.get('parents',[])}
        for completion_day in {r['completion_date'] for r in state.get('actual_outcomes',[]) if r.get('plan_sha256') in relevant}:
            original,contract=entry._bounded_actual_entry_outcomes(completion_day)
            if contract.get('status')!='ready' or any(_digest(r) not in {_digest(o) for o in original}
                for r in state.get('actual_outcomes',[]) if r.get('completion_date')==completion_day and r.get('plan_sha256') in relevant):
                raise ValueError('cancel_wait_predecessor_original_cost_receipt_changed:'+completion_day)
        return state
    return {}


def _unresolved_prior_custody(target_date, registry, parents, outcomes):
    """A submission census zero alone does not prove zero exposure/PnL."""
    from src.engine.scalping.entry_split_order_plan import _canonical_sha256
    completed={r.get('plan_sha256') for r in outcomes if r.get('status')=='COMPLETED'
        and r.get('cost_complete') is True and r.get('exact_lineage') is True
        and r.get('completion_date','9999') <= target_date
        and r.get('sha256')==_canonical_sha256({k:v for k,v in r.items() if k!='sha256'})}
    parent_by_intent={key:p['parent_id'] for p in parents for key in p['children']}
    inventory={}
    for event in registry:
        if event.get('owner_type')=='main_scalping' and event.get('side')=='BUY' and event.get('action')=='NEW':
            inventory.setdefault(event.get('intent_id'),{}).update(event)
    return [key for key,row in inventory.items() if '2026-06-05' <= str(row.get('order_date','')) < target_date
        and (row.get('state')!='ORDER_TERMINAL' or not row.get('terminal_reconciliation')
             or (row.get('filled_qty',0)>0 and parent_by_intent.get(key) not in completed))]


def _fit_model(model_rows, identity):
    """Reuse the entry owner's chronological empirical 20-receipt contract.

    Cancel/no-fill/partial support additionally needs those actual states on both
    dates. A full-fill-only model never opens the cancel states.
    """
    from src.engine.scalping.strategy_owner_replay import ENTRY_MODEL_SELECTION
    complete=[r for r in model_rows if r.get('complete') and r.get('model_identity')==identity]
    scopes=sorted({tuple(r['scope']) for r in complete})
    supported=[scope for scope in scopes if sum(tuple(r['scope'])==scope for r in complete)>=20]
    valid=[r for r in complete if supported and tuple(r['scope'])==supported[0]]
    days=sorted({r['source_date'] for r in valid})
    model=dict(contract=ENTRY_MODEL_SELECTION,validated=False,actual_parent_ids=[],supported_states=[],
               net_error_pct=None,available_after_date=None,model_identity=identity)
    if len(days)<2:return model
    cal=[r for r in valid if r['source_date']==days[0]];held=[r for r in valid if r['source_date']==days[1]]
    if len(cal)+len(held)<20:return model
    if len({tuple(r['scope']) for r in cal+held}) != 1:return {**model,'blocker':'model_scope_pooling_forbidden'}
    dimensions=('net_error_pct','cancel_ack_delay_sec','late_fill_window_sec','capital_error_minutes','reserve_error_minutes')
    tolerance={k:max(abs(r[k]) for r in cal) for k in dimensions}
    states=sorted(set(r['fill_class'] for r in cal)&set(r['fill_class'] for r in held))
    declared=[r for r in model_rows if r['source_date'] in days[:2] and r.get('scope')==cal[0]['scope']]
    coverage=len(cal+held)/len(declared) if declared else 0.
    model.update(scope=cal[0]['scope'],validated=coverage>=.8 and bool(states) and all(
        all(abs(r[k])<=tolerance[k]+1e-8 for k in dimensions) for r in held),coverage=coverage,
        actual_parent_ids=[r['parent_id'] for r in cal+held],supported_states=states,
        calibration_dates=[days[0]],holdout_dates=[days[1]],actual_sample_count=len(cal+held),
        available_after_date=max(r['completion_date'] for r in cal+held),net_error_pct=tolerance['net_error_pct'],
        cancel_ack_delay_sec=tolerance['cancel_ack_delay_sec'],late_fill_window_sec=tolerance['late_fill_window_sec'],
        tolerance=tolerance,actual_rows_sha256=_digest(cal+held),analysis_scope_budget=1,
        scope_selection='first_supported_scope_lexicographic_before_economic_selection',unevaluated_model_scopes=[list(s) for s in supported[1:]])
    model['sha256']=_digest(model)
    return model


def _replay_parents(parents, outcomes, events, model):
    from src.engine.scalping import strategy_owner_replay as replay
    from src.engine.scalping import entry_split_order_plan as entry
    from src.engine.monitoring import machine_microstructure_attribution as micro
    from src.engine.scalping.entry_cancel_wait_runtime import bounded_candidates
    rows=[];models=[];bindings={}
    completed={};conflicts=set()
    for receipt in outcomes:
        key=receipt.get('plan_sha256')
        if key in completed and completed[key]!=receipt:conflicts.add(key)
        completed[key]=receipt
    for key in conflicts:completed.pop(key,None)
    for day in sorted({p['source_date'] for p in parents}):
        day_parents=[p for p in parents if p['source_date']==day]
        if entry._source_quality_summary(day).get('tuning_input_allowed') is not True:
            models += [dict(parent_id=p['parent_id'],source_date=day,complete=False,blocker='historical_source_quality_changed') for p in day_parents]
            continue
        anchors=[dict(anchor_id=p['parent_id'],symbol=p['seed'].get('stock_code'),anchor_at=p['seed'].get('observed_at'),
                      expected_venues=[replay.entry_native_market_venue(p['seed'].get('effective_venue'))],
                      expected_session_buckets=[p['seed'].get('session_bucket')],adaptive_exit_source_only=True)
                 for p in day_parents if replay._entry_seed_valid(p['seed'])]
        if not anchors:
            models += [dict(parent_id=p['parent_id'],source_date=day,complete=False,blocker='frozen_entry_seed_missing') for p in day_parents]
            continue
        canary=micro.resolve_target_canary_snapshot(target_date=date.fromisoformat(day),latest_path=micro.DEFAULT_CANARY_SNAPSHOT_PATH,daily_root=micro.CANARY_DAILY_SNAPSHOT_DIR)
        paths=[micro.OBSERVATION_ROOT/f'trade_date={day}',micro.DEFAULT_SOURCE_EXCLUSION_MANIFEST]
        if canary:paths.append(canary)
        before=micro._source_generation_contract({},extra_paths=paths)
        source,inventory,windows=micro._micro_context(day,micro.OBSERVATION_ROOT,{a['symbol'] for a in anchors},anchors,
            micro.DEFAULT_SOURCE_EXCLUSION_MANIFEST,canary,datetime.now(replay.KST))
        if before != micro._source_generation_contract({},extra_paths=paths):raise ValueError('cancel_wait_native_generation_changed')
        bindings[day]=before
        for p in day_parents:
            seed=p['seed'];window=windows.get(p['parent_id']) or {}
            if not replay._entry_seed_valid(seed) or source.get('source_contract_ready') is not True or window.get('adaptive_exit_source_overflow'):
                models.append(dict(parent_id=p['parent_id'],source_date=day,complete=False,blocker='native_scope_or_seed_unsupported'));continue
            seed=json.loads(json.dumps(seed));context=seed['operating_contract'];context['cancel_wait_profile']=p['profile']
            context['sha256']=_digest({k:v for k,v in context.items() if k!='sha256'});seed['seed_sha256']=_digest({k:v for k,v in seed.items() if k!='seed_sha256'})
            children=sorted(p['children'].values(),key=lambda x:(x['submitted_at'],x['child_id']))
            arms={str(t):replay.replay_cancel_wait_arm(seed,t,children,window.get('raw_depth_rows') or [],window.get('raw_market_rows') or [],
                  incumbent_timeout=p['incumbent_timeout_sec'],cancel_model=model) for t in bounded_candidates(p['profile'],p['incumbent_timeout_sec'])}
            scope=[seed['effective_venue'],seed['session_bucket'],context.get('broker_route'),p['profile']]
            actual_qty=sum(c['fills'][-1]['filled_qty'] if c['fills'] else 0 for c in children)
            kind='no_fill' if not actual_qty else 'full' if actual_qty==seed['total_qty'] else 'partial'
            row=dict(parent_id=p['parent_id'],source_date=day,scope=scope,fill_class=kind,
                submitted_at=seed['observed_at'],notional_krw=sum(x['qty']*x['price'] for x in seed['legs']),
                budget_krw=context['budget_krw'],requested_qty=seed['total_qty'],incumbent_timeout_sec=p['incumbent_timeout_sec'],arms=arms)
            rows.append(row);arm=arms[str(p['incumbent_timeout_sec'])];actual=completed.get(p['parent_id']) or {}
            m=dict(parent_id=p['parent_id'],source_date=day,scope=scope,fill_class=kind,complete=False,
                   model_identity=replay.entry_operating_model_identity(),blocker=arm.get('blocker'))
            if arm.get('status')=='completed_source_only' and all(c['terminal_reconciled'] for c in children):
                if kind=='no_fill':
                    actual_net=0.;completion=max(c['terminal_at'] for c in children)
                elif (actual.get('sha256')==entry._canonical_sha256({k:v for k,v in actual.items() if k!='sha256'}) and actual.get('cost_complete') is True
                      and actual.get('exact_lineage') is True and actual.get('owner')=='main_scalping' and actual.get('origin')=='real'
                      and actual.get('status')=='COMPLETED' and actual.get('entry_qty')==actual_qty
                      and actual.get('cost_policy_version')==context['cost_policy_version']):
                    actual_net=actual['net_pnl_krw'];completion=actual['completed_at']
                else:
                    models.append(m);continue
                diagnostic=dict(actual_journal_legs=children)
                capital,reserve=entry._actual_entry_capital(diagnostic,completion)
                requested={};ack={}
                for event in events:
                    if event.get('emitted_date')!=day:continue
                    f=event.get('fields') or {};no=str(f.get('ord_no') or '')
                    if event.get('stage')=='entry_order_cancel_requested':requested[no]=event['emitted_at']
                    if event.get('stage')=='entry_order_cancel_confirmed' and f.get('cancel_response')=='success':ack[no]=event['emitted_at']
                latencies=[];late=[]
                for child in children:
                    no=child['broker_order_no']
                    if no in requested and no in ack:
                        latencies.append((datetime.fromisoformat(ack[no])-datetime.fromisoformat(requested[no])).total_seconds())
                        late.append((datetime.fromisoformat(child['terminal_at'])-datetime.fromisoformat(ack[no])).total_seconds())
                if kind!='full' and (len(latencies)!=len(children) or any(x<0 for x in latencies+late)):
                    m['blocker']='actual_cancel_ack_late_fill_clock_missing';models.append(m);continue
                m.update(complete=True,completion_date=completion[:10],net_error_pct=abs(arm['net_pnl_krw']-actual_net)/row['notional_krw']*100,
                    cancel_ack_delay_sec=max(latencies,default=0.),late_fill_window_sec=max(late,default=0.),
                    capital_error_minutes=abs(arm['capital_krw_minutes']-capital),reserve_error_minutes=abs(arm['reserve_krw_minutes']-reserve),
                    actual_cost_receipt_sha256=actual.get('sha256'),blocker=None)
            models.append(m)
    return rows,models,bindings


def build_report(target_date: str) -> dict[str, Any]:
    if date.fromisoformat(target_date).isoformat()!=target_date or target_date<'2026-06-05':raise ValueError('clean_source_date_required')
    if target_date < EXECUTABLE_EVIDENCE_DATE:return _build_legacy_report(target_date)
    from src.engine.scalping.entry_cancel_wait_runtime import ECONOMIC_SCHEMA,SELECTION_RULE,evaluate_economic_search
    from src.engine.scalping.strategy_owner_replay import entry_operating_model_identity
    previous,incumbent_source=_incumbent(target_date)
    events,registry,outcomes,source=_current_sources(target_date)
    try:predecessor=_previous_state(target_date)
    except (OSError,ValueError,TypeError,KeyError) as exc:
        predecessor={};source['predecessor']=dict(status='source_gap',reason=str(exc),
            excluded_from_economic_history=True,structural_gap_eta=None)
    outcomes=list({_digest(r):r for r in predecessor.get('actual_outcomes',[])+outcomes}.values())
    events=list({_digest(r):r for r in predecessor.get('source_events',[])+events}.values())
    counts=dict(predecessor.get('source_counts') or {})
    parents=[p for p in predecessor.get('parents',[]) if p['source_date']!=target_date]
    state='source_gap';blocker=source['projection'].get('reason');unclassified=0
    if source['projection'].get('status')=='ready' and source['registry'].get('status')=='verified' and source['source_quality'].get('tuning_input_allowed') is True:
        try:new,unclassified=_parents(target_date,events,registry)
        except (ValueError,TypeError,KeyError,SyntaxError) as exc:
            new=[];unclassified=1;blocker=str(exc)
        parents+=new
        if unclassified:counts.pop(target_date,None)
        else:counts[target_date]=len(new)
        state='no_submitted_orders' if not new and not unclassified else 'model_unvalidated'
        blocker=blocker or 'actual_dispatch_or_parent_lineage_unclassified' if unclassified else None
    else:
        counts.pop(target_date,None)
    # Mature earlier pending parents using the same durable signed journal.
    latest={};filled=defaultdict(list)
    for e in registry:
        key=e.get('intent_id');latest.setdefault(key,{}).update(e)
        if e.get('event')=='FILL_RECORDED':filled[key].append(e)
    parents=json.loads(json.dumps(parents))
    for p in parents:
        for key,c in p['children'].items():
            a=latest.get(key) or {}
            if a:
                c.update(terminal_at=a.get('observed_at_kst'),fills=filled[key],
                    terminal_reconciled=a.get('state')=='ORDER_TERMINAL' and bool(a.get('terminal_reconciliation')))
    # Do not retain old raw reads or silently treat unavailable windows as zero.
    identity=entry_operating_model_identity();model=_fit_model(predecessor.get('model_rows',[]),identity)
    from src.engine.monitoring import machine_microstructure_attribution as micro
    native_generation={d:micro._source_generation_contract({},extra_paths=[
        micro.OBSERVATION_ROOT/f'trade_date={d}',micro.DEFAULT_SOURCE_EXCLUSION_MANIFEST,
        micro.DEFAULT_CANARY_SNAPSHOT_PATH,micro.daily_canary_snapshot_path(date.fromisoformat(d),root=micro.CANARY_DAILY_SNAPSHOT_DIR)])
        for d in {p['source_date'] for p in parents}}
    from src.engine.scalping import entry_split_order_plan as entry
    preflight=_digest(dict(source=source,native=native_generation,historical_quality={d:entry._source_quality_summary(d) for d in native_generation},
        previous=previous,incumbent_source=incumbent_source,predecessor=predecessor.get('sha256'),model=identity,
        implementation=_implementation(),selection=SELECTION_RULE))
    current_path=report_paths(target_date)[0];receipt_path=current_path.with_suffix('.reuse-contract.json')
    if current_path.is_file() and receipt_path.is_file() and not current_path.is_symlink():
        cached=json.loads(current_path.read_text());receipt=json.loads(receipt_path.read_text())
        if (cached.get('preflight_fingerprint')==preflight and cached.get('economic_tuning_input_allowed') is False
            and cached.get('scope_overrides')==incumbent_source.get('previous_scope_overrides',[])
            and cached.get('previous_thresholds')==previous
            and cached.get('proof_sha256')==_digest({k:v for k,v in cached.items() if k not in ('generated_at','proof_sha256')})
            and receipt.get('artifact_sha256')==hashlib.sha256(current_path.read_bytes()).hexdigest()
            and receipt.get('preflight_fingerprint')==preflight):
            return cached
    rows=[];model_rows=[];native={}
    if parents and source['projection'].get('status')=='ready':
        try:
            rows,model_rows,native=_replay_parents(parents,outcomes,events,model)
            fitted=_fit_model(model_rows,identity)
            if fitted!=model:
                model=fitted
                if model.get('validated'):rows,model_rows,native=_replay_parents(parents,outcomes,events,model)
        except (OSError,ValueError,KeyError,TypeError) as exc:
            state='source_gap';blocker='cancel_wait_replay_source:'+str(exc)
    evaluation=evaluate_economic_search(rows,model,counts,consumed_holdouts=predecessor.get('consumed_holdouts',[])) if rows and not unclassified else dict(status=state,selected=None,paired_count=0,consumed_holdouts=predecessor.get('consumed_holdouts',[]))
    if state=='source_gap' or unclassified:evaluation.update(status='source_gap',selected=None,blocker=blocker)
    elif counts.get(target_date)==0:evaluation.update(status='no_submitted_orders',selected=None)
    state=evaluation['status'];selected=evaluation.get('selected');ready=state=='economic_improvement_validated'
    for key in ('incumbent_ev_pct','candidate_ev_pct','delta_ev_pct','mean_day_delta_krw',
                'delta_ev_lower_bound_pct','day_delta_lower_bound_krw'):
        evaluation.setdefault(key,None)
    unresolved=_unresolved_prior_custody(target_date,registry,parents,outcomes)
    if counts.get(target_date)==0 and unresolved:
        counts.pop(target_date,None)
        state='waiting_outcome';ready=False;blocker='prior_custody_or_completed_cost_unresolved'
        evaluation.update(status=state,selected=None,blocker=blocker)
    elif state=='model_unvalidated' and any(not c['terminal_reconciled'] for p in parents for c in p['children'].values()):
        state='waiting_outcome';evaluation.update(status=state,blocker='actual_order_terminal_reconciliation_pending')
    scopes=list(incumbent_source.get('previous_scope_overrides') or [])
    if ready:
        scopes=[s for s in scopes if s['scope']!=selected['scope']]+[dict(scope=selected['scope'],timeout_sec=selected['timeout_sec'],
            incumbent_timeout_sec=selected['incumbent_timeout_sec'],base_timeout_sec=previous[selected['scope'][-1]])]
    state_body=dict(through_date=target_date,parents=parents,model_rows=model_rows,source_counts=counts,
        consumed_holdouts=evaluation['consumed_holdouts'],native_bindings=native,model_identity=identity,
        actual_outcomes=outcomes,source_events=events)
    state_body['sha256']=_digest(state_body)
    source['native']=native
    body=dict(schema_version=2,economic_schema=ECONOMIC_SCHEMA,date=target_date,report_type='entry_cancel_wait_tuning',
        runtime_family=RUNTIME_FAMILY,policy_version=POLICY_VERSION,selection_rule_version=SELECTION_RULE,
        generated_at=datetime.now().astimezone().isoformat(timespec='seconds'),enabled=True,automatic_off_allowed=False,
        standalone_operational_family=True,runtime_effect=False,allowed_runtime_apply=True,
        decision_authority='next_preopen_bounded_entry_cancel_wait_policy',metric_role='primary_ev',
        primary_decision_metric='notional_weighted_ev_pct_and_same_capital_daily_net_delta',
        window_policy='actual_model_calibration_then_model_holdout_then_policy_training_then_unused_holdout',
        sample_floor=dict(owner_model_actual=20,coverage=.8,diagnostic_only=SAMPLE_FLOOR),
        source_quality_gate='lossless_actual_submission_census_verified_owner_inventory_native_exit_cost',
        forbidden_uses=['actual_pnl_from_cf','non_submitted_opportunity','other_family_authority','guard_bypass'],
        excluded_consumers=['ADM','LDM','lifecycle_bucket','threshold_cycle_ev','runtime_apply_bridge'],
        source_quality_status='pass' if source['projection'].get('status')=='ready' and source['source_quality'].get('tuning_input_allowed') is True else 'missing_source_hold',
        economic_tuning_input_allowed=ready,economic_source_gap=blocker or evaluation.get('blocker') if not ready else None,
        previous_thresholds=previous,recommended_thresholds=dict(previous),incumbent_source=incumbent_source,
        registered_count=len(parents),invalid_row_count=unclassified,diagnostic_proxy_row_count=None,
        submission_census=dict(submitted_parent_count=counts.get(target_date),unclassified_count=unclassified,
            coverage_verified=source['projection'].get('status')=='ready' and source['registry'].get('status')=='verified' and not unclassified,
            unresolved_prior_custody_count=len(unresolved),zero_is_verified=state=='no_submitted_orders'),
        evidence_summary=dict(state=state,registered_count=len(parents),completed_candidate_count=evaluation.get('paired_count',0),
            threshold_change_supported=ready,carry_forward_applied=not ready),
        profiles={p:dict(previous_threshold_sec=v,recommended_threshold_sec=v,calibration_state=state,
                    registered_count=sum(x['profile']==p for x in parents),completed_candidate_count=0,candidate_ev=[]) for p,v in previous.items()},
        source_contract=source,model_validation=model,economic_evaluation=evaluation,economic_state=state_body,
        preflight_fingerprint=preflight,
        scope_overrides=scopes)
    body['input_fingerprint']=_digest(dict(source=source,previous=previous,incumbent_source=incumbent_source,predecessor=predecessor.get('sha256'),model=identity,
        implementation=_implementation(),selection=SELECTION_RULE))
    body['proof_sha256']=_digest({k:v for k,v in body.items() if k not in ('generated_at','proof_sha256')})
    return body


def verify_report(payload, *, recompute=True):
    from src.engine.scalping.entry_cancel_wait_runtime import ECONOMIC_SCHEMA
    if payload.get('economic_schema')!=ECONOMIC_SCHEMA:return False,'cancel_wait_executable_schema_required'
    if payload.get('proof_sha256')!=_digest({k:v for k,v in payload.items() if k not in ('generated_at','proof_sha256')}):return False,'cancel_wait_report_hash_invalid'
    if recompute:
        current=build_report(payload['date'])
        if current['proof_sha256']!=payload['proof_sha256']:return False,'cancel_wait_source_or_metric_revalidation_failed'
    return True,None


def prepare_policy(payload, effective_date, *, publication_date=None):
    from src.engine.scalping.entry_cancel_wait_runtime import ECONOMIC_SCHEMA
    valid,reason=verify_report(payload)
    if not valid:raise ValueError(reason)
    from src.engine.automation.machine_entry_timing_tuning import _next_trading_date
    publication_date=publication_date or payload['date']
    if not payload['date'] <= publication_date <= datetime.now(KST).date().isoformat():
        raise ValueError('cancel_wait_publication_date_invalid')
    expected=_next_trading_date(date.fromisoformat(publication_date)).isoformat()
    if effective_date != expected:raise ValueError('cancel_wait_effective_trading_date_invalid')
    policy=dict(schema=ECONOMIC_SCHEMA,runtime_family=RUNTIME_FAMILY,source_date=payload['date'],effective_date=effective_date,
        publication_date=publication_date,
        policy_version=f"{RUNTIME_FAMILY}:{payload['date']}:{payload['proof_sha256'][:12]}",report_proof_sha256=payload['proof_sha256'],
        previous_thresholds=payload['previous_thresholds'],scope_overrides=payload['scope_overrides'],
        disposition='validated_scope_candidate' if payload['economic_tuning_input_allowed'] else 'incumbent_preserved',
        evaluation_status=payload['evidence_summary']['state'],runtime_effect=False,actual_pid_consumed=False)
    policy['sha256']=_digest(policy)
    path=REPORT_DIR/f"entry_cancel_wait_policy_{payload['date']}.json"
    _atomic_json(path,policy)
    return policy,path


def handoff_view(payload, policy, policy_path):
    valid,reason=verify_report(payload,recompute=False)
    if (not valid or policy.get('report_proof_sha256')!=payload['proof_sha256']
        or policy.get('sha256')!=_digest({k:v for k,v in policy.items() if k!='sha256'})):
        raise ValueError(reason or 'cancel_wait_summary_policy_proof_invalid')
    return dict(source_date=payload['date'],publication_date=policy['publication_date'],effective_date=policy['effective_date'],
        evaluation_status=payload['evidence_summary']['state'],policy_disposition=policy['disposition'],
        report_proof_sha256=payload['proof_sha256'],policy_sha256=hashlib.sha256(policy_path.read_bytes()).hexdigest(),
        previous_thresholds=payload['previous_thresholds'],scope_overrides=policy['scope_overrides'],
        economic_tuning_input_allowed=payload['economic_tuning_input_allowed'],
        delta_ev_pct=payload['economic_evaluation'].get('delta_ev_pct'),mean_day_delta_krw=payload['economic_evaluation'].get('mean_day_delta_krw'),
        actual_pid_consumed=False,whole_native_chain_done_claimed=False,owner='KiwoomCommonHealthOpportunityCostAcceptance0917')


def load_handoff_view(target_date, report_dir):
    directory=report_dir/'entry_cancel_wait_tuning'
    rp=directory/f'entry_cancel_wait_tuning_{target_date}.json';pp=directory/f'entry_cancel_wait_policy_{target_date}.json'
    if not rp.is_file():return None
    payload=json.loads(rp.read_text())
    if payload.get('schema_version')!=2:return None
    return handoff_view(payload,json.loads(pp.read_text()),pp)


def checklist_handoff(view):
    return '\n'.join(['<!-- entry_cancel_wait_handoff:start -->',
        '<!-- entry_cancel_wait_handoff_sha256:'+_digest(view)+' -->','','## Entry cancel-wait 장후 handoff','',
        f"- 평가 {view['source_date']}; 발행 {view['publication_date']}; 적용 {view['effective_date']}. `{view['evaluation_status']}` / `{view['policy_disposition']}`.",
        '- common timeout `'+json.dumps(view['previous_thresholds'],sort_keys=True)+'` 보존; ΔEV `%p` / 평균 일별 순익 차이 `원/일`: `'+json.dumps([view['delta_ev_pct'],view['mean_day_delta_krw']])+'`.',
        '- 자연 원천/model/미사용 holdout·정규 PREOPEN/PID·비용 후 성과는 기존 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`의 Acceptance다. 전체 native DONE/PID 소비를 주장하지 않는다.','',
        '<!-- entry_cancel_wait_handoff:end -->'])


def verify_handoff(target_date, *, require_summary=True):
    issues=[]
    try:
        payload=json.loads(report_paths(target_date)[0].read_text())
        valid,reason=verify_report(payload)
        if not valid:issues.append(reason)
        path=REPORT_DIR/f'entry_cancel_wait_policy_{target_date}.json'
        policy=json.loads(path.read_text())
        from src.engine.automation.machine_entry_timing_tuning import _next_trading_date
        publication_date=policy.get('publication_date',target_date)
        if (not target_date <= publication_date <= datetime.now(KST).date().isoformat()
            or policy.get('source_date')!=target_date or policy.get('effective_date')!=_next_trading_date(date.fromisoformat(publication_date)).isoformat()
            or policy.get('sha256')!=_digest({k:v for k,v in policy.items() if k!='sha256'})
            or policy.get('report_proof_sha256')!=payload.get('proof_sha256')
            or policy.get('scope_overrides')!=payload.get('scope_overrides')
            or policy.get('previous_thresholds')!=payload.get('previous_thresholds')):
            issues.append('cancel_wait_policy_proof_date_or_mapping_invalid')
        if require_summary:
            from src.engine.automation.postclose_summary_handoff import verify_summary_handoff
            result=verify_summary_handoff(target_date,report_dir=DATA_DIR/'report',
                checklist_path=DATA_DIR.parent/'docs'/'checklists'/f"{policy['effective_date']}-stage2-todo-checklist.md")
            issues+=result['issues']
            view=handoff_view(payload,policy,path)
            tower=json.loads((DATA_DIR/'report/tuning_performance_control_tower'/f'tuning_performance_control_tower_{target_date}.json').read_text())
            text=(DATA_DIR.parent/'docs/checklists'/f"{policy['effective_date']}-stage2-todo-checklist.md").read_text()
            if tower.get('entry_cancel_wait_economic_tuning')!=view or text.count(checklist_handoff(view))!=1:
                issues.append('cancel_wait_last_consumer_semantics_or_generation_invalid')
    except (OSError,ValueError,TypeError,KeyError) as exc:
        issues.append('cancel_wait_handoff:'+str(exc))
    return dict(status='FAIL' if issues else 'PASS',scope='entry_cancel_wait_only',source_date=target_date,
                issues=issues,whole_native_chain_done_claimed=False,actual_pid_consumed=False)


def write_report(target_date: str, *, effective_date=None, publication_date=None) -> dict[str, Any]:
    payload = build_report(target_date)
    json_path, md_path = report_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_json(json_path,payload)
    if target_date >= EXECUTABLE_EVIDENCE_DATE:
        from src.engine.automation.machine_entry_timing_tuning import _next_trading_date
        policy,path=prepare_policy(payload,effective_date or _next_trading_date(date.fromisoformat(publication_date or target_date)).isoformat(),publication_date=publication_date)
        _atomic_json(json_path.with_suffix('.reuse-contract.json'),dict(artifact_sha256=hashlib.sha256(json_path.read_bytes()).hexdigest(),
            preflight_fingerprint=payload['preflight_fingerprint'],as_of=payload['generated_at']))
    lines = [
        f"# Entry Cancel Wait Tuning {target_date}",
        "",
        f"- family: `{RUNTIME_FAMILY}`",
        f"- source_quality_status: `{payload['source_quality_status']}`",
        f"- evidence_state: `{payload['evidence_summary']['state']}`",
        f"- registered_count: `{payload['evidence_summary']['registered_count']}`",
        f"- completed_candidate_count: `{payload['evidence_summary']['completed_candidate_count']}`",
        f"- threshold_change_supported: `{payload['evidence_summary']['threshold_change_supported']}`",
        "- enabled: `true` (automatic OFF forbidden)",
        "- excluded_consumers: `ADM, LDM, lifecycle_bucket, threshold_cycle_ev, runtime_apply_bridge`",
        "",
        "| profile | previous | recommended | state | completed |",
        "|---|---:|---:|---|---:|",
    ]
    for profile, item in payload["profiles"].items():
        lines.append(
            f"| {profile} | {item['previous_threshold_sec']} | {item['recommended_threshold_sec']} | {item['calibration_state']} | {item['completed_candidate_count']} |"
        )
    if payload.get('schema_version')==2:
        lines += ['', '## Submitted-order economics', '',
            '- submission_census: `'+json.dumps(payload['submission_census'],sort_keys=True)+'`',
            '- model_validation: `'+json.dumps(payload['model_validation'],sort_keys=True)+'`',
            '- economic_evaluation: `'+json.dumps(payload['economic_evaluation'],sort_keys=True)+'`',
            '- scope_overrides: `'+json.dumps(payload['scope_overrides'],sort_keys=True)+'`',
            f'- prepared_policy: `{path}`',f"- effective_date: `{policy['effective_date']}`",'- actual_pid_consumed: `false`']
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--effective-date")
    parser.add_argument("--publication-date")
    args = parser.parse_args()
    payload=write_report(args.date,effective_date=args.effective_date,publication_date=args.publication_date)
    print(json.dumps(dict(date=args.date,state=payload['evidence_summary']['state'],
        economic_tuning_input_allowed=payload['economic_tuning_input_allowed'],raw_not_read=True)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
