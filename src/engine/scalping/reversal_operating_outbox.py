"""Consumer-only durable opportunity custody, separate from offline replay.

Reservation is committed before transmission. An uncertain transmission is
never retried automatically. Broker order custody remains in the native journal.
"""

from __future__ import annotations
import fcntl
import json
from pathlib import Path
from src.engine.scalping.continuous_reversal_postclose import digest
from src.engine.scalping.initial_quantity_bundle_state import (
    _write_target_index_atomic,
    reserve_reversal_signal,
)


class OperatingOpportunityError(ValueError):
    """Local opportunity custody failure, never a provider transport failure."""


def advance(data_root, opportunity_key, state, *, binding=None):
    try:
        return _advance(data_root, opportunity_key, state, binding=binding)
    except OSError as exc:
        raise OperatingOpportunityError("operating_outbox_io_error") from exc


def _advance(data_root, opportunity_key, state, *, binding=None):
    if (
        not isinstance(opportunity_key, str)
        or len(opportunity_key) != 64
        or any(c not in "0123456789abcdef" for c in opportunity_key)
    ):
        raise OperatingOpportunityError("operating_opportunity_key_invalid")
    allowed = {
        "reserved": {"transmission_uncertain"},
        "transmission_uncertain": {"response_received"},
        "response_received": {"intent_assigned"},
        "intent_assigned": {"submission_reconciliation"},
        "submission_reconciliation": {"reconciled"},
    }
    base = Path(data_root) / "runtime/initial_quantity/operating_opportunities"
    base.mkdir(parents=True, exist_ok=True)
    path = base / (opportunity_key + ".json")
    with (base / (opportunity_key + ".lock")).open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        exists = path.exists()
        try:
            previous = json.loads(path.read_text()) if exists else None
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise OperatingOpportunityError("operating_outbox_corrupt") from exc
        if exists and (
            not isinstance(previous, dict)
            or previous.get("schema") != "main_operating_opportunity_outbox_v1"
            or previous.get("opportunity_key") != opportunity_key
            or not isinstance(previous.get("state"), str)
            or previous.get("state") not in {*allowed, "reconciled"}
            or not isinstance(previous.get("history"), list)
            or previous.get("sha256")
            != digest({k: v for k, v in previous.items() if k != "sha256"})
        ):
            raise OperatingOpportunityError("operating_outbox_corrupt")
        if previous and state not in allowed.get(previous["state"], set()):
            raise OperatingOpportunityError(
                "operating_opportunity_already_reserved_or_transition_invalid"
            )
        if not previous and state != "reserved":
            raise OperatingOpportunityError("operating_outbox_reservation_missing")
        value = dict(
            schema="main_operating_opportunity_outbox_v1",
            opportunity_key=opportunity_key,
            state=state,
            history=(previous or {}).get("history", [])
            + [dict(state=state, binding=binding or {})],
        )
        value["sha256"] = digest(value)
        _write_target_index_atomic(path, value)
        return value


def reserve(data_root, assessment, request_identity):
    key = assessment["opportunity_key"]
    advance(
        data_root,
        key,
        "reserved",
        binding=dict(
            request_sha256=request_identity,
            scope_execution_hash=assessment["scope_execution_hash"],
            signal_set_hash=assessment["signal_set_hash"],
            matched_policy_refs=assessment["matched_policy_refs"],
            native_signal_id=assessment["signal_id"],
        ),
    )
    # Bridge old unresolved provider/intent custody. A collision fails closed;
    # no family/arm refresh turns the old opportunity into permission to retry.
    try:
        reserve_reversal_signal(
            Path(data_root) / "runtime/initial_quantity/reversal_signals",
            signal_id=assessment["signal_id"],
            stage="provider_request",
            identity=request_identity,
            binding=dict(opportunity_key=key, request_sha256=request_identity),
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise OperatingOpportunityError("reversal_signal_journal_invalid") from exc
    except OSError as exc:
        raise OperatingOpportunityError("reversal_signal_journal_io_error") from exc
    except ValueError as exc:
        if str(exc) not in {
            "reversal_signal_already_reserved:provider_request",
            "reversal_signal_journal_invalid",
            "reversal_signal_reservation_invalid",
        }:
            raise
        raise OperatingOpportunityError(str(exc)) from exc
    return advance(data_root, key, "transmission_uncertain")
