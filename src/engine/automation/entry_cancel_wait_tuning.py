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
from itertools import chain
from datetime import datetime, date, timedelta
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
RECONCILIATION_VERSION = "entry_cancel_wait_source_reconciliation_v1"
RECONCILIATION_OWNER = "EntryCancelWaitSourceReconciliation1002"
MAX_RECONCILIATION_METADATA_BYTES = 64 * 1024 * 1024
_RECONCILIATION_VIEW_CACHE = {}


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
        events, projection=entry._bounded_execution_projection(target_date,stages=CANCEL_WAIT_SUMMARY_STAGES | {'order_leg_sent'},
            families=('dynamic_entry_price_resolver','entry_price_execution_quality'))
    except (OSError,ValueError,TypeError,KeyError) as exc:
        events,projection=[],dict(status='source_gap',reason=str(exc),raw_not_read=True)
    registry,registry_contract=entry._execution_registry_snapshot()
    outcomes,outcome_contract=entry._bounded_actual_entry_outcomes(target_date)
    quality=entry._source_quality_summary(target_date)
    return events,registry,outcomes,dict(projection=projection,registry=registry_contract,
        actual_outcomes=outcome_contract,source_quality=quality)


def _sequential_first_context_valid(context, sent, target_date):
    from src.engine.scalping.initial_quantity_timeout import timeout_schedule_valid

    fields = sent.get('fields') or {}
    schedule = context.get('initial_quantity_schedule')
    if not timeout_schedule_valid(schedule):
        return False
    try:
        start = datetime.fromisoformat(schedule['order_start_at'])
        frozen = datetime.fromisoformat(context['frozen_at'])
        submitted = datetime.fromisoformat(fields['entry_split_submitted_at'])
    except (KeyError, TypeError, ValueError):
        return False
    if (start.tzinfo is None or frozen.tzinfo is None or submitted.tzinfo is None
            or not start <= frozen <= submitted):
        return False
    first_qty=context.get('requested_qty')
    total_qty=context.get('plan_total_qty')
    return bool(
        context.get('schema') == 'entry_cancel_wait_submitted_paired_v2'
        and context.get('timeout_owner') == 'initial_quantity_bundle_timeout_schedule'
        and context.get('economic_eligible') is False
        and context.get('observation_only') is True
        and context.get('actual_timeout_sec') is None
        and context.get('candidate_timeout_secs') == []
        and context.get('source_date') == target_date
        and schedule['order_start_at'][:10] == target_date
        and bool(context.get('parent_id'))
        and context.get('parent_id') == fields.get('buy_parent_id')
        and bool(context.get('bundle_attempt_id'))
        and context.get('bundle_attempt_id') == fields.get('initial_quantity_attempt_id')
        and schedule['schedule_sha256'] == fields.get('initial_quantity_schedule_sha256')
        and schedule['policy_sha256'] == fields.get('initial_quantity_policy_file_sha256')
        and str(fields.get('initial_quantity_leg_index')) == '0'
        and type(first_qty) is int and type(total_qty) is int
        and 0 < first_qty <= total_qty
        and str(total_qty) == str(fields.get('initial_quantity_requested_qty'))
        and str(first_qty) == str(fields.get('submitted_qty'))
        and str(context.get('submitted_price')) == str(fields.get('entry_split_submitted_price'))
        and bool(context.get('child_id'))
        and context.get('child_id') == fields.get('tag')
        and context.get('stock_code') == sent.get('stock_code')
        and context.get('broker_route') == fields.get('broker_route')
        and context.get('session_bucket') == fields.get('market_session_bucket')
        and context.get('owner_type') == fields.get('buy_owner_type') == 'main_scalping'
        and bool(context.get('owner_id'))
        and context.get('owner_id') == fields.get('buy_owner_id')
        and bool(context.get('owner_client_intent_id'))
        and context.get('owner_client_intent_id') == fields.get('buy_owner_client_intent_id')
    )


def _sequential_terminal_proof_valid(actual):
    proof=actual.get('terminal_reconciliation')
    sha=proof.get('receipt_sha256') if isinstance(proof,dict) else None
    fields=('intent_id','account_key','order_date','broker_order_no',
        'owner_type','owner_id','symbol','side','action','route',
        'quantity','filled_qty')
    return bool(type(actual.get('quantity')) is int and actual['quantity'] > 0
        and type(actual.get('filled_qty')) is int and 0 <= actual['filled_qty'] <= actual['quantity']
        and all(actual.get(field) is not None for field in fields)
        and actual.get('state')=='ORDER_TERMINAL'
        and isinstance(proof,dict)
        and proof.get('schema')=='order_owner_terminal_reconciliation_v1'
        and isinstance(sha,str) and len(sha)==64
        and all(char in '0123456789abcdef' for char in sha)
        and all(proof.get(field)==actual.get(field) for field in fields))


def _parents(target_date, events, registry, *, details=None):
    from src.engine.scalping.entry_split_order_plan import _safe_bool
    from src.trading.order.owner_custody_registry import OrderOwnerRegistry

    states=OrderOwnerRegistry._state(registry)
    inventory={key:row for key,row in states.items()
        if row.get('owner_type')=='main_scalping'
        and row.get('side')=='BUY' and row.get('action')=='NEW'}
    cancel_inventory={key:row for key,row in states.items()
        if row.get('side')=='BUY' and row.get('action')=='CANCEL'}
    fills=defaultdict(list)
    for event in registry:
        key=event.get('intent_id')
        if key in inventory and event.get('event')=='FILL_RECORDED':
            fills[key].append(event)
    sent_by_record_order={}
    for event in events:
        if event.get('stage')!='order_leg_sent' or event.get('emitted_date')!=target_date:
            continue
        f=event.get('fields') or {}
        if not _safe_bool(f.get('actual_order_submitted')):
            continue
        no=str(f.get('broker_order_no') or f.get('ord_no') or '')
        key=(str(event.get('record_id') or ''),no)
        if key in sent_by_record_order and sent_by_record_order[key]!=event:
            raise ValueError('submission_duplicate_order_projection_conflict')
        sent_by_record_order[key]=event
    parents={}
    unclassified=set()
    joined=set()
    joined_sent=set()
    accepted_context_hashes=set()
    uncertain_contexts={}
    for event in events:
        if (event.get('stage')!='entry_cancel_wait_submission'
                or event.get('emitted_date')!=target_date):
            continue
        fields=event.get('fields') or {}
        if fields.get('dispatch_disposition')!='response_uncertain':
            continue
        context=_object(fields.get('entry_cancel_wait_submission_context'))
        if (not isinstance(context,dict)
                or context.get('sha256')!=_digest({k:v for k,v in context.items() if k!='sha256'})
                or context.get('source_date')!=target_date
                or context.get('timeout_owner')!='initial_quantity_bundle_timeout_schedule'):
            raise ValueError('sequential_uncertain_context_invalid')
        key=(str(event.get('record_id') or ''),context['sha256'])
        uncertain_contexts[key]=context
    submissions={}
    for event in events:
        if event.get('stage') != 'entry_cancel_wait_submission' or event.get('emitted_date') != target_date:
            continue
        fields=event.get('fields') or {}
        if not _safe_bool(fields.get('actual_order_submitted')):continue
        key=(str(event.get('record_id') or ''),str(fields.get('broker_order_no') or ''))
        if key in submissions and submissions[key]!=event:
            raise ValueError('cancel_wait_submission_duplicate_conflict')
        submissions[key]=event
    for key,sent in sent_by_record_order.items():
        fields=sent.get('fields') or {}
        if not fields.get('entry_cancel_wait_submission_context'):
            continue
        if fields.get('cancel_wait_timeout_owner') != 'initial_quantity_bundle_timeout_schedule':
            raise ValueError('sequential_timeout_owner_missing')
        if key in submissions:
            existing=submissions[key].get('fields') or {}
            if existing.get('entry_cancel_wait_submission_context') != fields.get('entry_cancel_wait_submission_context'):
                raise ValueError('sequential_duplicate_submission_context_conflict')
            continue
        submissions[key]={**sent,'stage':'entry_cancel_wait_submission',
            'fields':{**fields,'actual_order_submitted':True}}
    for event in submissions.values():
        f=event.get('fields') or {}
        context=_object(f.get('entry_cancel_wait_submission_context'))
        if (not isinstance(context,dict) or context.get('sha256') != _digest({k:v for k,v in context.items() if k!='sha256'})
            or context.get('source_date') != target_date):
            raise ValueError('submission_context_hash_or_date_invalid')
        no=str(f.get('broker_order_no') or '')
        sent=sent_by_record_order.get((str(event.get('record_id') or ''),no))
        sf=(sent or {}).get('fields') or {}
        sequential=context.get('timeout_owner')=='initial_quantity_bundle_timeout_schedule'
        if sequential and (sent is None or not _sequential_first_context_valid(
                context,sent,target_date)):
            raise ValueError('sequential_schedule_or_first_leg_identity_invalid')
        identity=str(f.get('owner_registry_intent_id') or '')
        actual=inventory.get(identity)
        policy_generation_valid=False
        if sf.get('buy_registry_mode')=='single_owner_unregistered':
            try:
                from src.trading.config.native_owner_policy import resolve_symbol_owner_policy, historical_single_owner_binding
                policy_generation_valid = historical_single_owner_binding(
                    {**sf, 'stock_code': event.get('stock_code')},
                    observed_at=(sent or {}).get('timestamp'))
                if not policy_generation_valid:
                    policy=resolve_symbol_owner_policy(event.get('stock_code'),target_date=target_date)
                    policy_generation_valid=(policy.target_date==target_date
                        and not policy.symbol_selected and not policy.coexistence_enabled
                        and sf.get('buy_owner_policy_reason')==policy.reason
                        and str(sf.get('buy_owner_policy_hash') or '')==policy.policy_hash)
            except Exception:
                policy_generation_valid=False
        single_owner=(not identity and sent is not None
            and sf.get('buy_registry_mode')=='single_owner_unregistered'
            and policy_generation_valid
            and str(sf.get('buy_owner_policy_selected')).lower()=='false'
            and str(sf.get('buy_owner_policy_coexistence')).lower()=='false'
            and sf.get('buy_owner_policy_date')==target_date
            and not any(r.get('symbol')==event.get('stock_code')
                and r.get('order_date')==target_date for r in registry))
        if sequential and (single_owner or not identity):
            raise ValueError('sequential_registry_owner_identity_missing')
        if single_owner:
            identity='source_only:'+_digest(sent)
            actual=dict(order_date=target_date,broker_order_no=no,
                quantity=context.get('requested_qty'),symbol=context.get('stock_code'),
                route=context.get('broker_route'),owner_id=sf.get('buy_owner_id'),
                account_key=sf.get('buy_account_key'),state='OPEN')
        if (not actual or not sent or (not single_owner and not identity)
            or sf.get('owner_registry_intent_id')!=str(f.get('owner_registry_intent_id') or '')):
            unclassified.add(('order',target_date,str(event.get('record_id') or ''),
                str(sf.get('buy_account_key') or ''),no) if no else ('submission',_digest(event)))
            continue
        if sequential and actual.get('client_intent_id') != context.get('owner_client_intent_id'):
            raise ValueError('sequential_owner_client_intent_conflict')
        account=str(sf.get('buy_account_key') or '')
        parent_id=str(sf.get('buy_parent_id') or '')
        child_id=str(sf.get('buy_child_id') or '')
        record=str(event.get('record_id') or '')
        if (not account or not parent_id or not child_id.startswith(parent_id+':')
            or str(sent.get('stock_code') or '')!=str(event.get('stock_code') or '')
            or sf.get('buy_owner_type')!='main_scalping'
            or sf.get('buy_owner_id')!=f'main_scalping:{record}'
            or actual.get('owner_id')!=sf.get('buy_owner_id')
            or actual.get('account_key')!=account
            or str(actual.get('broker_order_no') or '')!=no
            or str(sf.get('submitted_qty') or '')!=str(actual.get('quantity') or '')
            or str(sf.get('broker_route') or '')!=str(actual.get('route') or '')):
            raise ValueError('submission_owner_account_parent_identity_conflict')
        if not single_owner:
            joined.add(identity)
        joined_sent.add((record,no))
        if sequential:
            accepted_context_hashes.add((record,context['sha256']))
        seed=context.get('seed') or {}
        parent=context.get('parent_id') or parent_id
        if seed and (seed.get('operating_contract') or {}).get('broker_route')!=context['broker_route']:
            raise ValueError('submission_frozen_seed_broker_route_conflict')
        if (actual.get('order_date')!=target_date or actual.get('quantity')!=context['requested_qty']
            or actual.get('symbol')!=context.get('stock_code') or actual.get('route')!=context['broker_route']):
            raise ValueError('submission_owner_quantity_symbol_route_conflict')
        timeout_owner=('initial_quantity_bundle_timeout_schedule' if sequential
                       else 'entry_cancel_wait_runtime')
        profile=('initial_quantity_sequential' if sequential else context['wait_profile'])
        p=parents.setdefault(parent,dict(parent_id=parent,source_date=target_date,seed=seed,
            incumbent_timeout_sec=context['actual_timeout_sec'],profile=profile,
            timeout_owner=timeout_owner,economic_eligible=not sequential,children={}))
        if (p['seed'] != seed or p['incumbent_timeout_sec'] != context['actual_timeout_sec']
                or p['timeout_owner'] != timeout_owner or p['profile'] != profile):
            raise ValueError('submission_parent_context_conflict')
        child=dict(quantity=actual.get('quantity'),submitted_price=context['submitted_price'],
            submitted_at=(sf.get('entry_split_submitted_at') if sequential else context['frozen_at']),
            context_frozen_at=context['frozen_at'],
            terminal_at=actual.get('observed_at_kst'),fills=fills[identity],
            terminal_reconciled=_sequential_terminal_proof_valid(actual),
            child_id=context['child_id'],submit_child_id=child_id,submit_parent_id=parent_id,
            account_key=account,owner_id=actual.get('owner_id'),
            intent_id=None if single_owner else identity,
            custody_mode='single_owner_unregistered' if single_owner else 'registry_managed',
            broker_order_no=actual.get('broker_order_no'))
        if sequential:
            filled_qty=0
            if fills[identity]:
                filled_qty=fills[identity][-1].get('filled_qty')
            if (type(filled_qty) is not int or filled_qty<0
                    or filled_qty>actual.get('quantity',-1)):
                raise ValueError('sequential_fill_quantity_invalid')
            if actual.get('filled_qty') not in (None,filled_qty):
                raise ValueError('sequential_fill_journal_state_conflict')
            child['terminal_reconciled']=_sequential_terminal_proof_valid(actual)
            cancel_pending=any(c.get('original_order_no')==no
                and c.get('account_key')==account
                and c.get('order_date')==target_date
                and c.get('owner_id')==sf.get('buy_owner_id')
                and c.get('state')!='ORDER_TERMINAL'
                for c in cancel_inventory.values())
            terminal_state=(
                'full_terminal' if child['terminal_reconciled']
                    and filled_qty==actual['quantity'] else
                'partial_terminal' if child['terminal_reconciled']
                    and filled_qty>0 else
                'terminal_unfilled' if child['terminal_reconciled'] else
                'terminal_unverified' if actual.get('state')=='ORDER_TERMINAL' else
                'cancel_pending' if cancel_pending else
                'partial_open' if filled_qty>0 else 'open')
            child.update(filled_qty=filled_qty,cancel_pending=cancel_pending,
                terminal_state=terminal_state,cost_krw=None)
        if identity in p['children'] and p['children'][identity] != child:
            raise ValueError('conflicting_submission_child')
        p['children'][identity]=child
    unresolved_uncertain={key:context for key,context in uncertain_contexts.items()
        if key not in accepted_context_hashes}
    for key in unresolved_uncertain:
        unclassified.add(('uncertain_sequential_submit',*key))
    uncertain_client_ids={context.get('owner_client_intent_id')
        for context in unresolved_uncertain.values()}
    for identity,actual in inventory.items():
        if actual.get('order_date')!=target_date or identity in joined:
            continue
        client=str(actual.get('client_intent_id') or '')
        if client and client in uncertain_client_ids:
            continue
        if ':AVG_DOWN:' in client or ':PYRAMID:' in client:continue
        # Missing producer events, unknown actions and rejected/ambiguous owner
        # attempts remain in the census; a verified projection zero is not enough.
        no=str(actual.get('broker_order_no') or '')
        owner_record=str(actual.get('owner_id') or '').removeprefix('main_scalping:')
        unclassified.add(('order',target_date,owner_record,
            str(actual.get('account_key') or ''),no) if no else ('intent',identity))
    for event in events:
        if event.get('stage')!='order_leg_sent' or event.get('emitted_date')!=target_date:continue
        fields=event.get('fields') or {}
        if not _safe_bool(fields.get('actual_order_submitted')):continue
        no=str(fields.get('broker_order_no') or fields.get('ord_no') or '')
        key=('order',target_date,str(event.get('record_id') or ''),
            str(fields.get('buy_account_key') or ''),no) if no else ('projection',_digest(event))
        if no and (str(event.get('record_id') or ''),no) in joined_sent:
            continue
        unclassified.add(key)
    if details is not None:
        details.update(response_uncertain_attempt_count=len(uncertain_contexts),
            unresolved_uncertain_attempt_count=len(unresolved_uncertain),
            resolved_uncertain_attempt_count=len(uncertain_contexts)-len(unresolved_uncertain),
            sequential_source_only_parent_count=sum(
                p.get('economic_eligible') is False for p in parents.values()),
            economic_parent_count=sum(
                p.get('economic_eligible') is True for p in parents.values()),
            unclassified_identities=sorted(_digest(list(key)) for key in unclassified))
    return list(parents.values()),len(unclassified)


def _unclassified_source_identities(target_date, events):
    from src.engine.scalping.entry_split_order_plan import _safe_bool
    sent = {(str(e.get('record_id') or ''), str((e.get('fields') or {}).get('broker_order_no') or (e.get('fields') or {}).get('ord_no') or '')):
            (e.get('fields') or {}) for e in events if e.get('emitted_date') == target_date and e.get('stage') == 'order_leg_sent'}
    keys = set()
    for event in events:
        if event.get('emitted_date') != target_date or event.get('stage') not in {'order_leg_sent','entry_cancel_wait_submission'}:
            continue
        fields = event.get('fields') or {}
        if fields.get('dispatch_disposition') == 'response_uncertain':
            keys.add(_digest(['uncertain', target_date, event.get('record_id'), fields.get('entry_cancel_wait_submission_context')]))
        elif _safe_bool(fields.get('actual_order_submitted')):
            record = str(event.get('record_id') or '')
            no = str(fields.get('broker_order_no') or fields.get('ord_no') or '')
            account = (sent.get((record,no)) or fields).get('buy_account_key') or ''
            keys.add(_digest(['order', target_date, record, account, no]) if no else _digest(event))
    return sorted(keys)


def _reconciliation_dates(state):
    days = set(state.get('source_counts') or {})
    days.update(p['source_date'] for p in state.get('parents', []))
    days.update(e['emitted_date'] for e in state.get('source_events', []))
    days.update((state.get('submission_reconciliation') or {}).get('by_date') or {})
    days.update(state.get('_verified_source_bindings') or {})
    for day in days:
        if not isinstance(day, str) or date.fromisoformat(day).isoformat() != day:
            raise ValueError('cancel_wait_source_date_invalid')
    return days


def _source_binding(projection, registry_contract):
    census = projection.get('producer_census') or {}
    return dict(status=projection.get('status'),
                projection_sha256=_digest(projection),
                producer_manifest_sha256=census.get('manifest_sha256'),
                retained_event_count=projection.get('retained_event_count'),
                registry_tail_hash=registry_contract.get('tail_hash'))


def _previous_state(target_date):
    from src.engine.scalping.entry_cancel_wait_runtime import ECONOMIC_SCHEMA
    from src.engine.automation.source_quality_clean_baseline import policy_refresh_start_date
    refresh_floor = policy_refresh_start_date(target_date)
    for path in sorted(REPORT_DIR.glob('entry_cancel_wait_tuning_*.json'),reverse=True):
        day=path.stem[-10:]
        if not max(refresh_floor,EXECUTABLE_EVIDENCE_DATE) <= day < target_date:continue
        if path.is_symlink() or path.stat().st_size > MAX_RECONCILIATION_METADATA_BYTES:
            raise ValueError('cancel_wait_predecessor_path_or_size_invalid:'+str(path))
        payload,_=_bounded_semantic_json(path);state=payload.get('economic_state') or {}
        if payload.get('economic_schema') != ECONOMIC_SCHEMA:continue
        if payload.get('proof_sha256') and payload['proof_sha256'] != _digest({k:v for k,v in payload.items() if k not in ('generated_at','proof_sha256')}):
            raise ValueError('cancel_wait_predecessor_report_hash_invalid')
        if (payload.get('date', day) != day or state.get('through_date') != day):
            raise ValueError('cancel_wait_predecessor_report_date_invalid')
        if state.get('sha256') != _digest({k:v for k,v in state.items() if k!='sha256'}):
            raise ValueError('cancel_wait_predecessor_state_invalid')
        from src.engine.scalping import entry_split_order_plan as entry
        from src.engine.pipeline_event_summary import CANCEL_WAIT_SUMMARY_STAGES
        registry,registry_contract=entry._execution_registry_snapshot()
        if state.get('parents') and registry_contract.get('status')!='verified':
            raise ValueError('cancel_wait_predecessor_registry_unverified')
        bindings, rebuilt_parents, quarantined, rebuilt_events = {}, [], {}, []
        rebuilt_counts = dict(state.get('source_counts') or {})
        for source_day in sorted(_reconciliation_dates(state)):
            if not refresh_floor <= source_day <= day:
                raise ValueError('cancel_wait_predecessor_source_date_outside_scope')
            try:
                original,contract=entry._bounded_execution_projection(source_day,stages=CANCEL_WAIT_SUMMARY_STAGES | {'order_leg_sent'},
                    families=('dynamic_entry_price_resolver','entry_price_execution_quality'))
                retained=[e for e in state.get('source_events',[]) if e.get('emitted_date')==source_day]
                expected={_digest(e) for e in retained}
                prior_row=((state.get('submission_reconciliation') or {}).get('by_date') or {}).get(source_day) or {}
                if not expected and prior_row.get('excluded_source_event_sha256s'):
                    expected=set(prior_row['excluded_source_event_sha256s'])
                if contract.get('status')!='ready' or {_digest(e) for e in original}!=expected:
                    raise ValueError('cancel_wait_predecessor_original_projection_changed:'+source_day)
                bindings[source_day] = _source_binding(contract, registry_contract)
                reconstructed,unknown=_parents(source_day,original,registry)
                if unknown:
                    rebuilt_counts.pop(source_day, None)
                else:
                    rebuilt_counts[source_day] = len(reconstructed)
                immutable=lambda p:(p['seed'],p['profile'],p['incumbent_timeout_sec'],
                    p.get('timeout_owner','entry_cancel_wait_runtime'),
                    p.get('economic_eligible',True),
                    {key:{k:c[k] for k in ('quantity','submitted_price','submitted_at','child_id','intent_id','broker_order_no')}
                     for key,c in p['children'].items()})
                originals={p['parent_id']:immutable(p) for p in reconstructed}
                if any(originals.get(p['parent_id'])!=immutable(p) for p in state.get('parents',[]) if p['source_date']==source_day):
                    raise ValueError('cancel_wait_predecessor_frozen_context_changed:'+source_day)
                rebuilt_parents.extend(reconstructed)
                rebuilt_events.extend(original)
            except (OSError, ValueError, TypeError, KeyError, SyntaxError) as exc:
                retained=[e for e in state.get('source_events',[]) if e.get('emitted_date')==source_day]
                refs=sorted({_digest(e) for e in retained})
                if not refs:
                    refs=(((state.get('submission_reconciliation') or {}).get('by_date') or {}).get(source_day) or {}).get('excluded_source_event_sha256s') or []
                quarantined[source_day]=dict(reason=str(exc), excluded_source_event_sha256s=refs,
                    artifact_path=str(path), artifact_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                bindings[source_day]=dict(status='source_gap', reason=str(exc))
                rebuilt_counts.pop(source_day,None)
        if quarantined and not any(v.get('status')=='ready' for v in bindings.values()):
            raise ValueError(next(iter(quarantined.values()))['reason'])
        relevant={p['parent_id'] for p in rebuilt_parents}
        for completion_day in {r['completion_date'] for r in state.get('actual_outcomes',[]) if r.get('plan_sha256') in relevant}:
            original,contract=entry._bounded_actual_entry_outcomes(completion_day)
            if contract.get('status')!='ready' or any(_digest(r) not in {_digest(o) for o in original}
                for r in state.get('actual_outcomes',[]) if r.get('completion_date')==completion_day and r.get('plan_sha256') in relevant):
                raise ValueError('cancel_wait_predecessor_original_cost_receipt_changed:'+completion_day)
        # Keep historical source bindings even when there are no classified
        # parents or economic source counts. Old report bytes remain untouched.
        result = json.loads(json.dumps(state))
        result['_verified_source_bindings'] = bindings
        result['parents'] = rebuilt_parents
        result['source_events'] = rebuilt_events
        result['actual_outcomes'] = [r for r in state.get('actual_outcomes',[]) if r.get('plan_sha256') in relevant]
        if quarantined:
            result['model_rows'] = [r for r in state.get('model_rows',[]) if r.get('source_date') and r['source_date'] not in quarantined]
        result['_quarantined_sources'] = quarantined
        result['source_counts'] = rebuilt_counts
        return result
    return {}


def _unresolved_prior_custody(target_date, registry, parents, outcomes, *, details=None):
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
    unresolved = [key for key,row in inventory.items() if '2026-06-05' <= str(row.get('order_date','')) < target_date
        and (not _sequential_terminal_proof_valid(row)
             or (row.get('filled_qty',0)>0 and parent_by_intent.get(key) not in completed))]
    for parent in parents:
        if parent['source_date'] >= target_date:
            continue
        for key, child in parent['children'].items():
            if key in inventory:
                continue
            filled = (child.get('fills') or [{}])[-1].get('filled_qty', 0)
            if not child.get('terminal_reconciled') or (filled > 0 and parent['parent_id'] not in completed):
                unresolved.append(key)
    if details is not None:
        open_keys, terminal_keys, cost_keys = set(), set(), set()
        children = {key:(p, c) for p in parents if p['source_date'] < target_date
                    for key, c in p['children'].items()}
        for key in set(unresolved):
            row = inventory.get(key)
            parent, child = children.get(key, ({}, {}))
            if row and row.get('state') != 'ORDER_TERMINAL' and row.get('broker_order_no'):
                open_keys.add(key)
            elif not row or not _sequential_terminal_proof_valid(row):
                terminal_keys.add(key)
            filled = row.get('filled_qty', 0) if row else (child.get('fills') or [{}])[-1].get('filled_qty', 0)
            if filled and parent.get('parent_id') not in completed:
                cost_keys.add(key)
        details.update(known_open_order_count=len(open_keys),
            terminal_unverified_count=len(terminal_keys),
            filled_cost_unresolved_count=len(cost_keys))
    return sorted(set(unresolved))


def _history_dates(target_date):
    from src.engine.automation.source_quality_clean_baseline import policy_refresh_start_date
    from src.utils.market_day import is_krx_trading_day
    if target_date < '2026-09-29':
        return set()
    cursor = date.fromisoformat(policy_refresh_start_date(target_date))
    days = set()
    while cursor < date.fromisoformat(target_date):
        if is_krx_trading_day(cursor):
            days.add(cursor.isoformat())
        cursor += timedelta(days=1)
    return days


def _hydrate_missing_history(target_date, predecessor, registry, source):
    """Use compact, sealed sources for forward dates absent from prior reports."""
    from src.engine.scalping import entry_split_order_plan as entry
    from src.engine.pipeline_event_summary import CANCEL_WAIT_SUMMARY_STAGES
    bindings = predecessor.setdefault('_verified_source_bindings', {})
    for day in sorted(_history_dates(target_date) - _reconciliation_dates(predecessor)):
        try:
            original, contract = entry._bounded_execution_projection(day,
                stages=CANCEL_WAIT_SUMMARY_STAGES | {'order_leg_sent'},
                families=('dynamic_entry_price_resolver', 'entry_price_execution_quality'))
            bindings[day] = _source_binding(contract, source['registry'])
            if contract.get('status') != 'ready':
                continue
            reconstructed, unknown = _parents(day, original, registry)
            predecessor.setdefault('source_events', []).extend(original)
            predecessor.setdefault('parents', []).extend(reconstructed)
            if not unknown:
                predecessor.setdefault('source_counts', {})[day] = len(reconstructed)
        except (OSError, ValueError, TypeError, KeyError, SyntaxError) as exc:
            bindings[day] = dict(status='source_gap', reason=str(exc))


def _reconcile_history(target_date, events, registry, parents, outcomes, source,
                       predecessor, current_details):
    """Separate observed custody from the completeness of historical sources."""
    from src.engine.automation.source_quality_clean_baseline import policy_refresh_start_date
    from src.utils.market_day import is_krx_trading_day
    floor = policy_refresh_start_date(target_date)
    days = _reconciliation_dates(predecessor) | {target_date}
    # The forward refresh window declares its trading dates. Earlier legacy
    # audits retain only their declared dates, rather than replaying all history.
    days.update(_history_dates(target_date))
    bindings = dict(predecessor.get('_verified_source_bindings') or {})
    bindings.update({day: row.get('source_binding', {}) for day, row in
                     (predecessor.get('submission_reconciliation') or {}).get('by_date', {}).items()
                     if day not in bindings})
    bindings[target_date] = _source_binding(source['projection'], source['registry'])
    by_date = {}
    for day in sorted(days):
        if day > target_date or day < floor:
            continue
        details = current_details if day == target_date else {}
        retained = [p for p in parents if p['source_date'] == day]
        reason = None
        if day != target_date:
            try:
                reconstructed, _ = _parents(day, events, registry, details=details)
                retained = reconstructed
            except (ValueError, TypeError, KeyError, SyntaxError) as exc:
                reason = str(exc)
                details['unclassified_identities'] = _unclassified_source_identities(day, events)
        unknown = details.get('unclassified_identities') or []
        verified = bindings.get(day, {}).get('status') == 'ready'
        if day == target_date:
            verified = (verified and source['registry'].get('status') == 'verified'
                        and source['source_quality'].get('tuning_input_allowed') is True)
        by_date[day] = dict(source_binding=bindings.get(day),
            source_event_sha256s=sorted({_digest(e) for e in events if e.get('emitted_date') == day}),
            parent_identities=sorted(p['parent_id'] for p in retained),
            excluded_source_event_sha256s=(predecessor.get('_quarantined_sources') or {}).get(day,{}).get('excluded_source_event_sha256s',[]),
            classified_parent_count=len(retained), unclassified_identities=unknown,
            unclassified_submission_count=len(unknown), coverage_verified=verified,
            blocker=reason or ('historical_source_binding_missing' if not verified else
                              'actual_dispatch_or_parent_lineage_unclassified' if unknown else None))
    required = sorted(day for day in by_date if day < target_date)
    missing = [day for day in required if not by_date[day]['coverage_verified']]
    unknown = sorted({key for day in required for key in by_date[day]['unclassified_identities']})
    custody = {}
    unresolved = _unresolved_prior_custody(target_date, registry, parents, outcomes, details=custody)
    registry_valid = source['registry'].get('status') == 'verified'
    predecessor_gap = (source.get('predecessor', {}).get('status') == 'source_gap'
                       or (predecessor.get('submission_reconciliation') or {}).get(
                           'predecessor_source_gap') is True)
    coverage = registry_valid and not missing and not predecessor_gap and not unknown
    status = ('source_gap' if not coverage else 'waiting_outcome' if unresolved else 'verified_empty')
    history = dict(contract_version=RECONCILIATION_VERSION, history_scope_start=floor,
        history_scope_end=target_date, required_dates=required,
        verified_dates=[day for day in required if day not in missing], missing_dates=missing,
        unclassified_submission_count=len(unknown), known_unresolved_custody_count=len(unresolved),
        unresolved_prior_custody_count=len(unresolved) if coverage else None,
        coverage_verified=coverage, zero_is_verified=coverage and not unresolved,
        status=status, blocker=('historical_submission_or_source_unreconciled' if not coverage else
                              'prior_custody_or_completed_cost_unresolved' if unresolved else None),
        **custody, custody_scope_start='2026-06-05',
        owner=RECONCILIATION_OWNER,
        closure_test='declared_dates_original_source_identity_and_owner_terminal_cost_reconciled')
    ledger = dict(contract_version=RECONCILIATION_VERSION, by_date=by_date,
                  unresolved_custody_identities=sorted(_digest(key) for key in unresolved),
                  custody_counts=custody, quarantined_sources=predecessor.get('_quarantined_sources') or {},
                  predecessor_source_gap=predecessor_gap,
                  predecessor_source_failure=source.get('predecessor') or
                      (predecessor.get('submission_reconciliation') or {}).get('predecessor_source_failure'))
    return ledger, history


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
    from src.engine.scalping import native_packet_validation as micro
    from src.engine.scalping.entry_cancel_wait_runtime import bounded_candidates
    rows=[];models=[];bindings={}
    completed={};conflicts=set()
    for receipt in outcomes:
        key=receipt.get('plan_sha256')
        if key in completed and completed[key]!=receipt:conflicts.add(key)
        completed[key]=receipt
    for key in conflicts:completed.pop(key,None)
    for day in sorted({p['source_date'] for p in parents}):
        day_parents=[p for p in parents if p['source_date']==day
            and p.get('economic_eligible',True) is True]
        if not day_parents:
            continue
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
            artifacts=[dict(path=str(path), date=path.stem[-10:],
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                for path in REPORT_DIR.glob('entry_cancel_wait_tuning_*.json')
                if path.stem[-10:] < target_date and not path.is_symlink()
                and path.stat().st_size <= 64*1024*1024],
            excluded_from_economic_history=True,structural_gap_eta=None)
    _hydrate_missing_history(target_date, predecessor, registry, source)
    outcomes=list({_digest(r):r for r in predecessor.get('actual_outcomes',[])+outcomes}.values())
    events=list({_digest(r):r for r in chain(predecessor.get('source_events',[]),events)}.values())
    counts=dict(predecessor.get('source_counts') or {})
    parents=[p for p in predecessor.get('parents',[]) if p['source_date']!=target_date]
    state='source_gap';blocker=source['projection'].get('reason');unclassified=0
    parent_details={}
    if source['projection'].get('status')=='ready' and source['registry'].get('status')=='verified' and source['source_quality'].get('tuning_input_allowed') is True:
        try:new,unclassified=_parents(target_date,events,registry,details=parent_details)
        except (ValueError,TypeError,KeyError,SyntaxError) as exc:
            new=[];blocker=str(exc)
            parent_details['unclassified_identities'] = _unclassified_source_identities(target_date,events) or [_digest(dict(source_date=target_date,failure=str(exc)))]
            unclassified=len(parent_details['unclassified_identities'])
        parents+=new
        if unclassified:counts.pop(target_date,None)
        else:counts[target_date]=len(new)
        state=('no_submitted_orders' if not new and not unclassified else
            'source_only_sequential_excluded' if new and not unclassified
                and not any(p.get('economic_eligible',True) for p in new) else
            'model_unvalidated')
        blocker=blocker or 'actual_dispatch_or_parent_lineage_unclassified' if unclassified else None
    else:
        counts.pop(target_date,None)
        parent_details['unclassified_identities'] = _unclassified_source_identities(target_date,events)
        unclassified=len(parent_details['unclassified_identities'])
    # Mature earlier pending parents using the same durable signed journal.
    from src.trading.order.owner_custody_registry import OrderOwnerRegistry
    latest=OrderOwnerRegistry._state(registry);filled=defaultdict(list)
    cancel_inventory=[row for row in latest.values()
        if row.get('side')=='BUY' and row.get('action')=='CANCEL']
    for e in registry:
        if e.get('event')=='FILL_RECORDED':filled[e.get('intent_id')].append(e)
    parents=json.loads(json.dumps(parents))
    for p in parents:
        for key,c in p['children'].items():
            a=latest.get(key) or {}
            if a:
                terminal=_sequential_terminal_proof_valid(a)
                c.update(terminal_at=a.get('observed_at_kst'),fills=filled[key],
                    terminal_reconciled=terminal)
                if p.get('timeout_owner')=='initial_quantity_bundle_timeout_schedule':
                    quantity=a.get('quantity')
                    filled_qty=a.get('filled_qty',0)
                    valid_quantity=(type(quantity) is int and quantity>0
                        and type(filled_qty) is int and 0<=filled_qty<=quantity)
                    cancel_pending=any(row.get('original_order_no')==a.get('broker_order_no')
                        and row.get('account_key')==a.get('account_key')
                        and row.get('owner_id')==a.get('owner_id')
                        and row.get('order_date')==a.get('order_date')
                        and row.get('state')!='ORDER_TERMINAL'
                        for row in cancel_inventory)
                    c.update(filled_qty=filled_qty if valid_quantity else None,
                        cancel_pending=cancel_pending, cost_krw=None,
                        terminal_state=(
                            'terminal_unverified' if not valid_quantity else
                            'full_terminal' if terminal and filled_qty==quantity else
                            'partial_terminal' if terminal and filled_qty>0 else
                            'terminal_unfilled' if terminal else
                            'terminal_unverified' if a.get('state')=='ORDER_TERMINAL' else
                            'cancel_pending' if cancel_pending else
                            'partial_open' if filled_qty>0 else 'open'))
    ledger, history = _reconcile_history(target_date, events, registry, parents,
        outcomes, source, predecessor, parent_details)
    daily_zero = (counts.get(target_date) == 0 and not unclassified
                  and source['projection'].get('status') == 'ready'
                  and source['registry'].get('status') == 'verified'
                  and source['source_quality'].get('tuning_input_allowed') is True)
    # Do not retain old raw reads or silently treat unavailable windows as zero.
    identity=entry_operating_model_identity();model=_fit_model(predecessor.get('model_rows',[]),identity)
    from src.engine.scalping import native_packet_validation as micro
    native_generation={d:micro._source_generation_contract({},extra_paths=[
        micro.OBSERVATION_ROOT/f'trade_date={d}',micro.DEFAULT_SOURCE_EXCLUSION_MANIFEST,
        micro.DEFAULT_CANARY_SNAPSHOT_PATH,micro.daily_canary_snapshot_path(date.fromisoformat(d),root=micro.CANARY_DAILY_SNAPSHOT_DIR)])
        for d in {p['source_date'] for p in parents if p.get('economic_eligible',True)}}
    from src.engine.scalping import entry_split_order_plan as entry
    preflight=_digest(dict(source=source,native=native_generation,historical_quality={d:entry._source_quality_summary(d) for d in native_generation},
        previous=previous,incumbent_source=incumbent_source,predecessor=predecessor.get('sha256'),model=identity,
        implementation=_implementation(),selection=SELECTION_RULE,
        reconciliation=ledger,historical_reconciliation=history))
    current_path=report_paths(target_date)[0];receipt_path=current_path.with_suffix('.reuse-contract.json')
    if current_path.is_file() and receipt_path.is_file() and not current_path.is_symlink():
        cached=json.loads(current_path.read_text());receipt=json.loads(receipt_path.read_text())
        if (cached.get('preflight_fingerprint')==preflight and cached.get('economic_tuning_input_allowed') is False
            and cached.get('scope_overrides')==incumbent_source.get('previous_scope_overrides',[])
            and cached.get('previous_thresholds')==previous
            and cached.get('proof_sha256')==_digest({k:v for k,v in cached.items() if k not in ('generated_at','proof_sha256')})
            and receipt.get('artifact_sha256')==hashlib.sha256(current_path.read_bytes()).hexdigest()
            and receipt.get('preflight_fingerprint')==preflight
            and not validated_reconciliation_view(cached).get('findings')):
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
    economic_counts={day:sum(p['source_date']==day and p.get('economic_eligible',True)
        for p in parents) for day in counts}
    evaluation=evaluate_economic_search(rows,model,economic_counts,consumed_holdouts=predecessor.get('consumed_holdouts',[])) if rows and not unclassified else dict(status=state,selected=None,paired_count=0,consumed_holdouts=predecessor.get('consumed_holdouts',[]))
    if state=='source_gap' or unclassified:evaluation.update(status='source_gap',selected=None,blocker=blocker)
    elif counts.get(target_date)==0:evaluation.update(status='no_submitted_orders',selected=None)
    state=evaluation['status'];selected=evaluation.get('selected');ready=state=='economic_improvement_validated'
    for key in ('incumbent_ev_pct','candidate_ev_pct','delta_ev_pct','mean_day_delta_krw',
                'delta_ev_lower_bound_pct','day_delta_lower_bound_krw'):
        evaluation.setdefault(key,None)
    if daily_zero or history['status'] != 'verified_empty':
        evaluation.update({key:None for key in ('incumbent_ev_pct','candidate_ev_pct',
            'delta_ev_pct','mean_day_delta_krw','delta_ev_lower_bound_pct','day_delta_lower_bound_krw')})
    unresolved=_unresolved_prior_custody(target_date,registry,parents,outcomes)
    if history['status']=='source_gap':
        state='source_gap';ready=False;blocker=history['blocker']
        evaluation.update(status=state,selected=None,blocker=blocker)
    elif unresolved:
        state='waiting_outcome';ready=False;blocker='prior_custody_or_completed_cost_unresolved'
        evaluation.update(status=state,selected=None,blocker=blocker)
    elif state=='model_unvalidated' and any(not c['terminal_reconciled'] for p in parents
        if p.get('economic_eligible',True) for c in p['children'].values()):
        state='waiting_outcome';evaluation.update(status=state,blocker='actual_order_terminal_reconciliation_pending')
    scopes=list(incumbent_source.get('previous_scope_overrides') or [])
    if ready:
        scopes=[s for s in scopes if s['scope']!=selected['scope']]+[dict(scope=selected['scope'],timeout_sec=selected['timeout_sec'],
            incumbent_timeout_sec=selected['incumbent_timeout_sec'],base_timeout_sec=previous[selected['scope'][-1]])]
    state_body=dict(through_date=target_date,parents=parents,model_rows=model_rows,source_counts=counts,
        consumed_holdouts=evaluation['consumed_holdouts'],native_bindings=native,model_identity=identity,
        actual_outcomes=outcomes,source_events=events)
    state_body['submission_reconciliation'] = ledger
    state_body['sha256']=_digest(state_body)
    source['native']=native
    body=dict(schema_version=2,economic_schema=ECONOMIC_SCHEMA,date=target_date,report_type='entry_cancel_wait_tuning',
        reconciliation_contract_version=RECONCILIATION_VERSION,
        runtime_family=RUNTIME_FAMILY,policy_version=POLICY_VERSION,selection_rule_version=SELECTION_RULE,
        implementation_sha256s=_implementation(),
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
            economic_parent_count=parent_details.get('economic_parent_count'),
            excluded_sequential_timeout_owner_count=parent_details.get('sequential_source_only_parent_count'),
            response_uncertain_attempt_count=parent_details.get('response_uncertain_attempt_count'),
            unresolved_uncertain_attempt_count=parent_details.get('unresolved_uncertain_attempt_count'),
            coverage_verified=source['projection'].get('status')=='ready' and source['registry'].get('status')=='verified' and source['source_quality'].get('tuning_input_allowed') is True and not unclassified,
            source_date=target_date,coverage_scope='target_date_main_initial_buy_submission',
            unresolved_prior_custody_count=history['unresolved_prior_custody_count'],
            zero_is_verified=daily_zero),
        historical_reconciliation=history,
        evidence_summary=dict(state=state,registered_count=len(parents),completed_candidate_count=evaluation.get('paired_count',0),
            daily_state='no_submitted_orders' if daily_zero else
                'source_gap' if counts.get(target_date) is None else 'submitted_orders_observed',
            historical_state=history['status'],
            threshold_change_supported=ready,carry_forward_applied=not ready),
        profiles={p:dict(previous_threshold_sec=v,recommended_threshold_sec=v,calibration_state=state,
                    registered_count=sum(x['profile']==p for x in parents),completed_candidate_count=0,candidate_ev=[]) for p,v in previous.items()},
        source_contract=source,model_validation=model,economic_evaluation=evaluation,economic_state=state_body,
        preflight_fingerprint=preflight,
        scope_overrides=scopes)
    body['input_fingerprint']=_digest(dict(source=source,previous=previous,incumbent_source=incumbent_source,predecessor=predecessor.get('sha256'),model=identity,
        implementation=_implementation(),selection=SELECTION_RULE,reconciliation=ledger))
    body['proof_sha256']=_digest({k:v for k,v in body.items() if k not in ('generated_at','proof_sha256')})
    return body


def _bounded_semantic_json(path):
    """One stable JSON receipt; no replay, source reconstruction, or writes."""
    if path.is_symlink() or path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError('cancel_wait_artifact_path_or_size_invalid')
    before = path.stat()
    with path.open('rb') as handle:
        raw = handle.read(MAX_RECONCILIATION_METADATA_BYTES + 1)
    after = path.stat()
    stamp = lambda value: (value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
    if stamp(before) != stamp(after):
        raise ValueError('semantic_generation_changed_during_read')
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError('cancel_wait_artifact_object_invalid')
    return value, hashlib.sha256(raw).hexdigest()


def _sealed_census_matches(data_root, day, events, manifest):
    """Check retained event identities against bounded producer metadata only."""
    from collections import Counter
    from src.engine.pipeline_event_summary import (producer_summary_paths,
        CANCEL_WAIT_SUMMARY_STAGES, IDENTITY_CONTRACT, IDENTITY_MODULUS,
        execution_projection_identity)
    path, _ = producer_summary_paths(Path(data_root)/'pipeline_event_summaries', day)
    stages = CANCEL_WAIT_SUMMARY_STAGES | {'order_leg_sent'}
    if (manifest.get('identity_contract') != IDENTITY_CONTRACT
        or not stages <= set(manifest.get('summary_stages') or [])):
        return False
    if path.is_symlink() or path.stat().st_size > 64 * 1024 * 1024:
        return False
    before = path.stat()
    with path.open('rb') as handle:
        raw = handle.read(MAX_RECONCILIATION_METADATA_BYTES + 1)
    after = path.stat()
    stamp = lambda value: (value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
    if stamp(before) != stamp(after):
        raise ValueError('semantic_generation_changed_during_read')
    if manifest.get('summary_storage_size_bytes') != len(raw):
        return False
    expected, expected_hash = Counter(), Counter()
    for line in raw.splitlines():
        row = json.loads(line)
        stage = row.get('stage')
        if stage not in stages:
            continue
        if (row.get('target_date') != day or row.get('identity_contract') != IDENTITY_CONTRACT
            or row.get('execution_projection_identity_contract') != 'lossless_execution_projection_v1'
            or type(row.get('event_count')) is not int or row['event_count'] < 0):
            return False
        expected[stage] += row['event_count']
        expected_hash[stage] = (expected_hash[stage] + int(row['execution_projection_hash_sum'],16)) % IDENTITY_MODULUS
    observed, observed_hash = Counter(), Counter()
    for event in events:
        stage = event.get('stage')
        value = event.get('execution_source_event_sha256')
        if stage not in stages or event.get('emitted_date') != day or value != execution_projection_identity(event):
            return False
        observed[stage] += 1
        observed_hash[stage] = (observed_hash[stage] + int(value,16)) % IDENTITY_MODULUS
    return expected == observed and expected_hash == observed_hash


def _candidate_evidence_valid(payload):
    """Enforce the existing economic promotion contract without replaying it."""
    from src.engine.scalping.entry_cancel_wait_runtime import SELECTION_RULE
    economic = payload['economic_evaluation']
    model = payload['model_validation']
    selected = economic.get('selected')
    if not isinstance(selected, dict):
        return False
    training, held = selected.get('training') or {}, selected.get('holdout') or {}
    paired = economic.get('paired_count')
    current = payload['submission_census'].get('economic_parent_count')
    sample = model.get('actual_sample_count')
    if (economic.get('status') != 'economic_improvement_validated'
        or economic.get('selection_rule_version') != SELECTION_RULE
        or model.get('validated') is not True or type(sample) is not int or sample < 20
        or selected.get('scope') != model.get('scope')
        or type(paired) is not int or paired <= 0 or type(current) is not int or current < paired
        or training.get('eligible') is not True or held.get('eligible') is not True
        or held.get('paired_count') != paired):
        return False
    train_days, held_days = training.get('verification_dates') or [], held.get('verification_dates') or []
    holdout = selected.get('holdout_date')
    if (not train_days or held_days != [holdout]
        or not model.get('available_after_date') < min(train_days) <= max(train_days) < holdout <= payload['date']):
        return False
    for key in ('delta_ev_pct','mean_day_delta_krw','delta_ev_lower_bound_pct','day_delta_lower_bound_krw'):
        value = economic.get(key)
        if type(value) not in (int,float) or not math.isfinite(value) or value <= 0 or held.get(key) != value:
            return False
    return True


def _reconciliation_metadata_generation(data_root, by_date):
    from src.engine.pipeline_event_summary import producer_summary_paths
    paths = [Path(data_root)/'runtime/order_owner_registry.jsonl']
    for day, row in sorted(by_date.items()):
        if row['coverage_verified']:
            paths.extend(producer_summary_paths(Path(data_root)/'pipeline_event_summaries',day))
    generation = []
    for path in paths:
        stat = path.lstat()
        generation.append((str(path.resolve()),stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns,path.is_symlink()))
    return tuple(generation)


def validated_reconciliation_view(payload, policy=None, *, data_root=None, read_object=None):
    """Validate the bounded report/ledger projection shared by every consumer.

    ``data_root`` adds sealed generation/registry checks. It never calls the
    producer, replay, an API, or a writer. Legacy v2 cannot prove historical zero.
    """
    from src.engine.scalping.entry_cancel_wait_runtime import ECONOMIC_SCHEMA
    from src.engine.scalping.entry_split_order_plan import _safe_bool
    from src.engine.automation.source_quality_clean_baseline import policy_refresh_start_date
    from src.trading.order.owner_custody_registry import OwnerRegistryError
    findings = []
    result = dict(status='source_invalid', findings=findings, source_date=payload.get('date'),
        owner=RECONCILIATION_OWNER, runtime_effect=False, allowed_runtime_apply=False,
        actual_pid_consumed=False, whole_native_chain_done_claimed=False,
        closure_test='same_date_original_source_ledger_policy_and_consumer_projection')
    if payload.get('reconciliation_contract_version') is None:
        result.update(status='not_evaluated_legacy', daily_zero_is_verified=None,
                      historical_zero_is_verified=None, unresolved_prior_custody_count=None)
        return result
    try:
        day = payload['date']
        if day > datetime.now(KST).date().isoformat():
            raise ValueError('cancel_wait_future_source_date_invalid')
        if date.fromisoformat(day).isoformat() != day or payload.get('economic_schema') != ECONOMIC_SCHEMA:
            findings.append('cancel_wait_report_date_or_hash_invalid')
        if payload.get('proof_sha256') != _digest({k:v for k,v in payload.items() if k not in ('generated_at','proof_sha256')}):
            findings.append('cancel_wait_report_date_or_hash_invalid')
        state = payload['economic_state']
        ledger = state['submission_reconciliation']
        history = payload['historical_reconciliation']
        census = payload['submission_census']
        by_date = ledger['by_date']
        if (state.get('through_date') != day
            or state.get('sha256') != _digest({k:v for k,v in state.items() if k != 'sha256'})
            or any(value != RECONCILIATION_VERSION for value in (
                payload['reconciliation_contract_version'], ledger.get('contract_version'), history.get('contract_version')))):
            findings.append('cancel_wait_reconciliation_ledger_invalid')
        if any(date.fromisoformat(d).isoformat() != d or d > day for d in by_date):
            findings.append('cancel_wait_reconciliation_ledger_invalid')
        required = sorted(d for d in by_date if d < day)
        declared = _reconciliation_dates(state) | _history_dates(day) | {day}
        if not declared <= set(by_date):
            findings.append('cancel_wait_history_source_binding_missing')
        missing, unknown = [], set()
        for d, row in by_date.items():
            keys = row['unclassified_identities']
            parents = [p for p in state['parents'] if p['source_date'] == d]
            identities = sorted(p['parent_id'] for p in parents)
            count = row['classified_parent_count']
            source_count = state['source_counts'].get(d)
            if source_count is not None and (type(source_count) is not int or source_count != len(parents) or keys):
                findings.append('cancel_wait_reconciliation_ledger_invalid')
            if (type(count) is not int or count < 0 or count != len(parents)
                or len(set(identities)) != len(identities) or row.get('parent_identities') != identities
                or not isinstance(keys, list) or len(set(keys)) != len(keys)
                or type(row['unclassified_submission_count']) is not int
                or row['unclassified_submission_count'] != len(keys)
                or row.get('source_event_sha256s') != sorted({_digest(e) for e in state['source_events'] if e.get('emitted_date') == d})
                or type(row.get('coverage_verified')) is not bool):
                findings.append('cancel_wait_reconciliation_ledger_invalid')
            orders = {(str(c.get('account_key') or ''), str(c['broker_order_no'])) for p in parents for c in p['children'].values()}
            unbound = any(e.get('emitted_date') == d and e.get('stage') == 'order_leg_sent'
                and _safe_bool((e.get('fields') or {}).get('actual_order_submitted'))
                and (str((e.get('fields') or {}).get('buy_account_key') or ''),
                     str((e.get('fields') or {}).get('broker_order_no') or (e.get('fields') or {}).get('ord_no') or '')) not in orders
                for e in state['source_events'])
            if unbound and not keys:
                findings.append('cancel_wait_false_historical_zero' if d < day else 'cancel_wait_false_daily_zero')
            if row['coverage_verified'] and ((row.get('source_binding') or {}).get('status') != 'ready'
                or (row.get('source_binding') or {}).get('retained_event_count') != len([e for e in state['source_events'] if e.get('emitted_date') == d])):
                findings.append('cancel_wait_history_source_binding_missing')
            if d < day:
                if not row['coverage_verified']:
                    missing.append(d)
                unknown.update(keys)
        missing.sort()
        unresolved = ledger['unresolved_custody_identities']
        if len(set(unresolved)) != len(unresolved):
            findings.append('cancel_wait_reconciliation_ledger_invalid')
        registry_valid = (payload['source_contract']['registry'].get('status') == 'verified')
        coverage = registry_valid and not missing and not unknown and not ledger['predecessor_source_gap']
        total = len(unresolved) if coverage else None
        expected_status = 'source_gap' if not coverage else 'waiting_outcome' if unresolved else 'verified_empty'
        if (history.get('required_dates') != required or history.get('missing_dates') != missing
            or history.get('verified_dates') != sorted(set(required) - set(missing))
            or history.get('unclassified_submission_count') != len(unknown)
            or type(history.get('unclassified_submission_count')) is not int
            or history.get('known_unresolved_custody_count') != len(unresolved)
            or type(history.get('known_unresolved_custody_count')) is not int
            or type(history.get('coverage_verified')) is not bool or history['coverage_verified'] != coverage
            or history.get('status') != expected_status
            or history.get('history_scope_start') != policy_refresh_start_date(day)
            or history.get('history_scope_end') != day):
            findings.append('cancel_wait_reconciliation_ledger_invalid')
        for key in ('known_open_order_count', 'terminal_unverified_count', 'filled_cost_unresolved_count'):
            value = (ledger.get('custody_counts') or {}).get(key)
            if type(value) is not int or not 0 <= value <= len(unresolved) or history.get(key) != value:
                findings.append('cancel_wait_reconciliation_ledger_invalid')
        if (history.get('unresolved_prior_custody_count') != total
            or census.get('unresolved_prior_custody_count') != total
            or (total is not None and (type(history.get('unresolved_prior_custody_count')) is not int
                or type(census.get('unresolved_prior_custody_count')) is not int))
            or type(history.get('zero_is_verified')) is not bool
            or history['zero_is_verified'] != (coverage and not unresolved)):
            findings.append('cancel_wait_false_historical_zero')
        current = by_date[day]
        count = state['source_counts'].get(day)
        daily_coverage = current['coverage_verified'] and not current['unclassified_identities']
        zero = daily_coverage and count == 0
        if (count is not None and (type(count) is not int or count < 0)
            or census.get('source_date') != day
            or census.get('coverage_scope') != 'target_date_main_initial_buy_submission'
            or census.get('submitted_parent_count') != count
            or (count is not None and type(census.get('submitted_parent_count')) is not int)
            or type(census.get('unclassified_count')) is not int
            or census['unclassified_count'] != current['unclassified_submission_count']
            or type(census.get('coverage_verified')) is not bool or census['coverage_verified'] != daily_coverage
            or type(census.get('zero_is_verified')) is not bool or census['zero_is_verified'] != zero):
            findings.append('cancel_wait_false_daily_zero')
        economic = payload['economic_evaluation']
        for key in ('incumbent_ev_pct','candidate_ev_pct','delta_ev_pct','mean_day_delta_krw',
                    'delta_ev_lower_bound_pct','day_delta_lower_bound_krw'):
            value = economic.get(key)
            if value is not None and (type(value) not in (int,float) or not math.isfinite(value)):
                findings.append('cancel_wait_economics_invalid')
        if (type(payload.get('economic_tuning_input_allowed')) is not bool
            or payload['evidence_summary'].get('state') != economic.get('status')
            or payload['evidence_summary'].get('historical_state') != expected_status
            or payload['evidence_summary'].get('daily_state') != ('no_submitted_orders' if zero else 'source_gap' if count is None else 'submitted_orders_observed')
            or payload['evidence_summary'].get('threshold_change_supported') is not payload['economic_tuning_input_allowed']
            or payload['evidence_summary'].get('carry_forward_applied') is not (not payload['economic_tuning_input_allowed'])):
            findings.append('cancel_wait_evidence_projection_invalid')
        if not coverage and (payload.get('economic_tuning_input_allowed') is not False
            or economic.get('status') != 'source_gap' or economic.get('selected') is not None):
            findings.append('cancel_wait_history_gap_erased')
        if payload.get('economic_tuning_input_allowed') is True and not _candidate_evidence_valid(payload):
            findings.append('cancel_wait_selected_without_economic_evidence')
        if unresolved and payload.get('economic_tuning_input_allowed') is not False:
            findings.append('cancel_wait_unresolved_custody_promoted')
        if zero and (payload.get('economic_tuning_input_allowed') is not False
            or economic.get('selected') is not None or any(economic.get(key) is not None for key in (
                'incumbent_ev_pct','candidate_ev_pct','delta_ev_pct','mean_day_delta_krw',
                'delta_ev_lower_bound_pct','day_delta_lower_bound_krw'))):
            findings.append('cancel_wait_empty_economics_fabricated')
        if not payload.get('economic_tuning_input_allowed') and payload.get('scope_overrides') != payload['incumbent_source'].get('previous_scope_overrides', []):
            findings.append('cancel_wait_incumbent_carry_mapping_invalid')
        if policy is not None:
            from src.utils.market_day import next_krx_trading_date as _next_trading_date
            pub = policy.get('publication_date')
            allowed = payload.get('economic_tuning_input_allowed') is True
            if (not isinstance(pub, str) or pub > datetime.now(KST).date().isoformat()
                or policy.get('sha256') != _digest({k:v for k,v in policy.items() if k != 'sha256'})
                or policy.get('schema') != ECONOMIC_SCHEMA or policy.get('runtime_family') != RUNTIME_FAMILY
                or policy.get('source_date') != day or not day <= pub
                or policy.get('effective_date') != _next_trading_date(date.fromisoformat(pub)).isoformat()
                or policy.get('report_proof_sha256') != payload.get('proof_sha256')
                or policy.get('evaluation_status') != payload['evidence_summary']['state']
                or policy.get('previous_thresholds') != payload.get('previous_thresholds')
                or policy.get('scope_overrides') != payload.get('scope_overrides')
                or policy.get('disposition') != ('validated_scope_candidate' if allowed else 'incumbent_preserved')):
                findings.append('cancel_wait_policy_binding_invalid')
        cache_key = None
        if data_root is not None:
            generation = _reconciliation_metadata_generation(data_root,by_date)
            if sum(item[2] * (2 if item[0].endswith('.json') else 1) for item in generation) > MAX_RECONCILIATION_METADATA_BYTES:
                return {**result,'status':'source_invalid' if findings else 'unobservable',
                    'findings':sorted(set(findings)), 'reason':'bounded_reconciliation_metadata_required'}
            cache_key = (day,payload.get('proof_sha256'),_digest(policy),generation)
            if not findings and cache_key in _RECONCILIATION_VIEW_CACHE:
                return json.loads(json.dumps(_RECONCILIATION_VIEW_CACHE[cache_key]))
            reader = read_object or _bounded_semantic_json
            for d, row in by_date.items():
                binding = row.get('source_binding') or {}
                if not row['coverage_verified']:
                    continue
                from src.engine.pipeline_event_summary import producer_summary_paths
                _, path = producer_summary_paths(Path(data_root)/'pipeline_event_summaries', d)
                manifest, _ = reader(path)
                from src.engine.scalping.entry_split_order_plan import _canonical_sha256
                if binding.get('producer_manifest_sha256') != _canonical_sha256(manifest):
                    findings.append('cancel_wait_stale_source_generation')
                elif not _sealed_census_matches(data_root, d,
                        [e for e in state['source_events'] if e.get('emitted_date') == d], manifest):
                    findings.append('cancel_wait_history_source_binding_missing')
                if reader(path)[0] != manifest:
                    raise ValueError('semantic_generation_changed_during_read')
            # An unrelated append does not invalidate a verified ancestor tail.
            from src.trading.order.owner_custody_registry import OrderOwnerRegistry
            path = Path(data_root)/'runtime/order_owner_registry.jsonl'
            if path.is_symlink():
                raise ValueError('cancel_wait_registry_path_invalid')
            before = path.stat()
            registry = OrderOwnerRegistry(path).verified_events_snapshot()
            after = path.stat()
            if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
                raise ValueError('semantic_generation_changed_during_read')
            expected_unresolved = sorted(_digest(key) for key in _unresolved_prior_custody(
                day, registry, state['parents'], state['actual_outcomes']))
            if expected_unresolved != unresolved:
                findings.append('cancel_wait_false_historical_zero')
            tail = payload['source_contract']['registry'].get('tail_hash')
            hashes = [e.get('event_hash') for e in registry]
            if tail != '0'*64 and tail not in hashes:
                findings.append('cancel_wait_history_source_binding_missing')
            elif any(e.get('owner_type') == 'main_scalping' and e.get('side') == 'BUY'
                     and e.get('order_date', '9999') <= day for e in registry[(hashes.index(tail)+1) if tail in hashes else 0:]):
                findings.append('cancel_wait_stale_registry_generation')
        if data_root is not None and _reconciliation_metadata_generation(data_root,by_date) != generation:
            raise ValueError('semantic_generation_changed_during_read')
        result.update(status='source_invalid' if findings else 'candidate_selected' if payload.get('economic_tuning_input_allowed') else 'incumbent_carry',
            reconciliation_contract_version=RECONCILIATION_VERSION, report_proof_sha256=payload.get('proof_sha256'),
            daily_state=payload['evidence_summary'].get('daily_state'), daily_submitted_parent_count=count,
            daily_zero_is_verified=zero, historical_state=expected_status,
            historical_zero_is_verified=coverage and not unresolved, unresolved_prior_custody_count=total,
            unclassified_submission_count=len(unknown), known_unresolved_custody_count=len(unresolved),
            **(ledger.get('custody_counts') or {}),
            missing_dates=missing, evaluation_status=payload['evidence_summary']['state'],
            economic_tuning_input_allowed=payload['economic_tuning_input_allowed'])
        if cache_key is not None and not findings:
            if len(_RECONCILIATION_VIEW_CACHE) >= 8:
                _RECONCILIATION_VIEW_CACHE.pop(next(iter(_RECONCILIATION_VIEW_CACHE)))
            _RECONCILIATION_VIEW_CACHE[cache_key] = json.loads(json.dumps(result))
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OwnerRegistryError) as exc:
        if str(exc) == 'semantic_generation_changed_during_read':
            return {**result, 'status':'unobservable', 'findings':[], 'reason':str(exc)}
        findings.append('cancel_wait_reconciliation_ledger_invalid')
        result['error'] = str(exc)[:160]
    result['findings'] = sorted(set(findings))
    return result


def _without_registry_tail(payload):
    result=json.loads(json.dumps(payload))
    for key in ('generated_at','proof_sha256','preflight_fingerprint','input_fingerprint'):
        result.pop(key,None)
    result['source_contract']['registry'].pop('tail_hash',None)
    result['economic_state'].pop('sha256',None)
    for row in result['economic_state']['submission_reconciliation']['by_date'].values():
        if row.get('source_binding'):
            row['source_binding'].pop('registry_tail_hash',None)
    return result


def verify_report(payload, *, recompute=True):
    from src.engine.scalping.entry_cancel_wait_runtime import ECONOMIC_SCHEMA
    if payload.get('economic_schema')!=ECONOMIC_SCHEMA:return False,'cancel_wait_executable_schema_required'
    if payload.get('proof_sha256')!=_digest({k:v for k,v in payload.items() if k not in ('generated_at','proof_sha256')}):return False,'cancel_wait_report_hash_invalid'
    view=validated_reconciliation_view(payload)
    if view.get('findings'):return False,view['findings'][0]
    if recompute:
        current=build_report(payload['date'])
        if current['proof_sha256']!=payload['proof_sha256']:
            unrelated_append=(payload.get('economic_tuning_input_allowed') is False
                and current.get('economic_tuning_input_allowed') is False
                and payload.get('implementation_sha256s') == current.get('implementation_sha256s')
                and bool(payload.get('implementation_sha256s'))
                and payload['source_contract']['registry'].get('tail_hash') != current['source_contract']['registry'].get('tail_hash')
                and _without_registry_tail(payload) == _without_registry_tail(current))
            if not unrelated_append or validated_reconciliation_view(payload,data_root=DATA_DIR).get('status') != 'incumbent_carry':
                return False,'cancel_wait_source_or_metric_revalidation_failed'
    return True,None


def prepare_policy(payload, effective_date, *, publication_date=None):
    from src.engine.scalping.entry_cancel_wait_runtime import ECONOMIC_SCHEMA
    valid,reason=verify_report(payload)
    if not valid:raise ValueError(reason)
    from src.utils.market_day import next_krx_trading_date as _next_trading_date
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
    recorded_policy,physical_policy_sha=_bounded_semantic_json(policy_path)
    if recorded_policy != policy:raise ValueError('semantic_generation_changed_during_read')
    reconciliation=validated_reconciliation_view(payload,policy)
    if reconciliation.get('findings'):raise ValueError(reconciliation['findings'][0])
    return dict(reconciliation=reconciliation,source_date=payload['date'],publication_date=policy['publication_date'],effective_date=policy['effective_date'],
        evaluation_status=payload['evidence_summary']['state'],policy_disposition=policy['disposition'],
        report_proof_sha256=payload['proof_sha256'],policy_sha256=physical_policy_sha,
        previous_thresholds=payload['previous_thresholds'],scope_overrides=policy['scope_overrides'],
        economic_tuning_input_allowed=payload['economic_tuning_input_allowed'],
        delta_ev_pct=payload['economic_evaluation'].get('delta_ev_pct'),mean_day_delta_krw=payload['economic_evaluation'].get('mean_day_delta_krw'),
        actual_pid_consumed=False,whole_native_chain_done_claimed=False,owner='KiwoomCommonHealthOpportunityCostAcceptance0917')


def load_handoff_view(target_date, report_dir):
    directory=report_dir/'entry_cancel_wait_tuning'
    rp=directory/f'entry_cancel_wait_tuning_{target_date}.json';pp=directory/f'entry_cancel_wait_policy_{target_date}.json'
    if not rp.is_file():return None
    payload,_=_bounded_semantic_json(rp)
    if payload.get('schema_version')!=2:return None
    policy,_=_bounded_semantic_json(pp)
    return handoff_view(payload,policy,pp)


def checklist_handoff(view):
    return '\n'.join(['<!-- entry_cancel_wait_handoff:start -->',
        '<!-- entry_cancel_wait_handoff_sha256:'+_digest(view)+' -->','','## Entry cancel-wait 장후 handoff','',
        f"- 평가 {view['source_date']}; 발행 {view['publication_date']}; 적용 {view['effective_date']}. `{view['evaluation_status']}` / `{view['policy_disposition']}`.",
        '- 당일/과거 대사: `'+json.dumps(view.get('reconciliation'),sort_keys=True)+'`.',
        '- common timeout `'+json.dumps(view['previous_thresholds'],sort_keys=True)+'` 보존; ΔEV `%p` / 평균 일별 순익 차이 `원/일`: `'+json.dumps([view['delta_ev_pct'],view['mean_day_delta_krw']])+'`.',
        '- 자연 원천/model/미사용 holdout·정규 PREOPEN/PID·비용 후 성과는 기존 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`의 Acceptance다. 전체 native DONE/PID 소비를 주장하지 않는다.','',
        '<!-- entry_cancel_wait_handoff:end -->'])


def upsert_checklist_handoff(content, source_date, target_date, report_dir):
    view = load_handoff_view(source_date, report_dir)
    if view is None or view['effective_date'] != target_date:
        return content
    start, end = '<!-- entry_cancel_wait_handoff:start -->', '<!-- entry_cancel_wait_handoff:end -->'
    if content.count(start) != content.count(end) or content.count(start) > 1:
        raise ValueError('cancel_wait_checklist_block_invalid')
    if start not in content:
        return content.rstrip() + '\n\n' + checklist_handoff(view) + '\n'
    a, b = content.index(start), content.index(end) + len(end)
    if b <= a:
        raise ValueError('cancel_wait_checklist_block_invalid')
    return content[:a] + checklist_handoff(view) + content[b:]


def verify_handoff(target_date, *, require_summary=True):
    issues=[]
    try:
        payload=json.loads(report_paths(target_date)[0].read_text())
        valid,reason=verify_report(payload)
        if not valid:issues.append(reason)
        path=REPORT_DIR/f'entry_cancel_wait_policy_{target_date}.json'
        policy=json.loads(path.read_text())
        from src.utils.market_day import next_krx_trading_date as _next_trading_date
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
            summary=_bounded_semantic_json(DATA_DIR/'report/runtime_approval_summary'/f'runtime_approval_summary_{target_date}.json')[0]
            summary_view=(((summary.get('sources') or {}).get('entry_cancel_wait') or {}).get('economic_evidence') or {}).get('cancel_wait_reconciliation')
            if payload.get('reconciliation_contract_version') and summary_view != view['reconciliation']:
                issues.append('cancel_wait_runtime_summary_projection_invalid')
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
        from src.utils.market_day import next_krx_trading_date as _next_trading_date
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
