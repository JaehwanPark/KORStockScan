"""Consumer-only durable opportunity custody, separate from offline replay.

Reservation is committed before transmission. An uncertain transmission is
never retried automatically. Broker order custody remains in the native journal.
"""
from __future__ import annotations
import fcntl
import json
from pathlib import Path
from src.engine.scalping.continuous_reversal_postclose import digest
from src.engine.scalping.initial_quantity_bundle_state import _write_target_index_atomic, reserve_reversal_signal


def advance(data_root, opportunity_key, state, *, binding=None):
    if len(opportunity_key)!=64 or any(c not in '0123456789abcdef' for c in opportunity_key):
        raise ValueError('operating_opportunity_key_invalid')
    allowed = {'reserved':{'transmission_uncertain'},'transmission_uncertain':{'response_received'},
               'response_received':{'intent_assigned'},'intent_assigned':{'submission_reconciliation'},
               'submission_reconciliation':{'reconciled'}}
    base = Path(data_root)/'runtime/initial_quantity/operating_opportunities'
    base.mkdir(parents=True,exist_ok=True)
    path = base/(opportunity_key+'.json')
    with (base/(opportunity_key+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        previous = json.loads(path.read_text()) if path.exists() else None
        if previous and previous.get('sha256') != digest({k:v for k,v in previous.items() if k!='sha256'}):
            raise ValueError('operating_outbox_corrupt')
        if previous and state not in allowed.get(previous['state'],set()):
            raise ValueError('operating_opportunity_already_reserved_or_transition_invalid')
        if not previous and state!='reserved':
            raise ValueError('operating_outbox_reservation_missing')
        value = dict(schema='main_operating_opportunity_outbox_v1',opportunity_key=opportunity_key,
                     state=state,history=(previous or {}).get('history',[])+[dict(state=state,binding=binding or {})])
        value['sha256']=digest(value)
        _write_target_index_atomic(path,value)
        return value


def reserve(data_root, assessment, request_identity):
    key=assessment['opportunity_key']
    advance(data_root,key,'reserved',binding=dict(request_sha256=request_identity,
        scope_execution_hash=assessment['scope_execution_hash'],signal_set_hash=assessment['signal_set_hash'],
        matched_policy_refs=assessment['matched_policy_refs'],native_signal_id=assessment['signal_id']))
    # Bridge old unresolved provider/intent custody. A collision fails closed;
    # no family/arm refresh turns the old opportunity into permission to retry.
    reserve_reversal_signal(Path(data_root)/'runtime/initial_quantity/reversal_signals',
        signal_id=assessment['signal_id'],stage='provider_request',identity=request_identity,
        binding=dict(opportunity_key=key,request_sha256=request_identity))
    return advance(data_root,key,'transmission_uncertain')
