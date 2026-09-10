"""Bounded pre-submit state owned by the existing widget/episode loop.

No orders, no policy publication, no extra broker reads. Local snapshot reads
are revalidated after I/O; broker transport stays outside this module.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from datetime import datetime
from types import SimpleNamespace

from src.trading.config.machine_entry_adverse_policy import load_policy
from src.trading.market.entry_adverse_flow import (
    CONTRACT,
    CHECKPOINTS_MS,
    MAX_LATE_MS,
    DEADLINE_MS,
    MAXIMUM_SOURCE_AGE_MS,
    evaluate_snapshot,
)
from src.trading.market.micro_confirmation import load_live_dynamic_confirmation_source

KEY = "entry_adverse_flow"
_TRANSPORT_CHECK = ContextVar("machine_entry_adverse_transport_check", default=None)


class EntryNotSent(Exception):
    """Raised only before session.post; never a broker rejection/ambiguity."""

    def __init__(self, reason):
        super().__init__(reason)
        self.result = SimpleNamespace(
            accepted=False,
            ambiguous=False,
            order_no="",
            return_code="ENTRY_ADVERSE_NOT_SENT",
            return_msg=str(reason),
        )


@contextmanager
def transport_check(callback=None):
    token = _TRANSPORT_CHECK.set(callback)
    try:
        yield
    finally:
        _TRANSPORT_CHECK.reset(token)


def before_transport(api_id):
    callback = _TRANSPORT_CHECK.get()
    if api_id == "kt10000" and callback is not None:
        callback()


def terminal(state):
    return (
        str(state.get("action", "")).startswith("SKIP_")
        or state.get("action") == "TRANSPORT_STARTED"
    )


def _skip(state, reason):
    state.update(action=reason, next_checkpoint_ms=None)
    return False


def _ms(now):
    if not isinstance(now, datetime) or now.utcoffset() is None:
        raise ValueError("entry_adverse_clock_invalid")
    return int(now.timestamp() * 1000)


def prepare(*, holder, identity, signal_at, now, scope, timing_mode, policy_hash=None):
    """Return original-path permission when OFF; never revive a terminal ID."""
    previous = holder.get(KEY)
    base = dict(
        contract=CONTRACT,
        identity=identity,
        scope=dict(scope),
        signal_at=signal_at.isoformat(),
    )
    history = holder.get(KEY + "_history") or {}
    if not isinstance(identity, str) or not isinstance(history, dict):
        holder[KEY] = dict(base, action="SKIP_STATE_INVALID")
        return False
    if identity in history:
        return False
    if isinstance(previous, dict) and previous.get("identity") != identity:
        if not terminal(previous):
            _skip(previous, "SKIP_IDENTITY_CHANGED")
        if not isinstance(previous.get("identity"), str):
            return _skip(previous, "SKIP_STATE_INVALID")
        holder.setdefault(KEY + "_history", {})[previous["identity"]] = deepcopy(
            previous
        )
        holder.pop(KEY, None)
        previous = None
    if (
        isinstance(previous, dict)
        and previous.get("identity") == identity
        and terminal(previous)
    ):
        return False
    try:
        selected = load_policy(scope=scope, now=now, signal_at=signal_at)
    except (ValueError, OSError, TypeError, KeyError) as exc:
        holder[KEY] = dict(base, action="SKIP_POLICY_INVALID", reason=str(exc))
        return False
    if selected is None:
        if isinstance(previous, dict) and previous.get("identity") == identity:
            return _skip(previous, "SKIP_POLICY_REVOKED")
        return True
    if timing_mode != "baseline_immediate":
        holder[KEY] = dict(base, action="SKIP_TIMING_CONFLICT")
        return False
    if not isinstance(identity, str) or not identity:
        holder[KEY] = dict(base, action="SKIP_IDENTITY_MISSING")
        return False
    if not isinstance(previous, dict) or previous.get("identity") != identity:
        previous = dict(
            contract=CONTRACT,
            identity=identity,
            signal_at=signal_at.isoformat(),
            t0_ms=_ms(signal_at),
            deadline_ms=_ms(signal_at) + DEADLINE_MS,
            scope=dict(scope),
            pin=selected["pin"],
            timing_policy_hash=policy_hash,
            action="WAIT",
            checkpoints={},
            next_checkpoint_ms=0,
        )
        holder[KEY] = previous
    if (
        type(previous.get("t0_ms")) is not int
        or previous.get("deadline_ms") != previous["t0_ms"] + DEADLINE_MS
        or previous["t0_ms"] != _ms(signal_at)
        or previous.get("next_checkpoint_ms") not in (*CHECKPOINTS_MS, None)
        or not isinstance(previous.get("checkpoints"), dict)
        or previous.get("action") not in ("WAIT", "CONTINUE")
        or type(previous.get("last_evaluated_ms", previous["t0_ms"])) is not int
        or (
            previous.get("action") == "WAIT"
            and previous.get("next_checkpoint_ms") is None
        )
    ):
        return _skip(previous, "SKIP_STATE_INVALID")
    if (
        previous.get("pin") != selected["pin"]
        or previous.get("scope") != scope
        or previous.get("timing_policy_hash") != policy_hash
    ):
        return _skip(previous, "SKIP_POLICY_CHANGED")
    now_ms = _ms(now)
    elapsed = now_ms - previous["t0_ms"]
    if (
        now_ms < previous.get("last_evaluated_ms", previous["t0_ms"])
        or elapsed > DEADLINE_MS
    ):
        return _skip(previous, "SKIP_DEADLINE")
    previous["last_evaluated_ms"] = now_ms
    if previous["action"] == "CONTINUE":
        return True
    next_cp = previous["next_checkpoint_ms"]
    due = [c for c in CHECKPOINTS_MS if c >= next_cp and c <= elapsed]
    if not due:
        return False
    cp = due[-1]
    for missed in due[:-1]:
        previous["checkpoints"][str(missed)] = dict(action="MISSED_CHECKPOINT")
    if elapsed - cp > MAX_LATE_MS:
        decision = dict(
            action="SOURCE_UNAVAILABLE", reason="checkpoint_deadline_missed"
        )
    else:
        snapshot, reason = load_live_dynamic_confirmation_source()
        decision = evaluate_snapshot(
            snapshot=snapshot,
            symbol=scope["symbol"],
            route=scope["route"],
            cutoff_ms=previous["t0_ms"] + cp,
        )
        if snapshot is None:
            decision["reason"] = reason
    previous["checkpoints"][str(cp)] = decision
    if decision.get("epoch") is not None:
        anchor = (decision["item"], decision["epoch"])
        if "anchor" in previous and tuple(previous["anchor"]) != anchor:
            return _skip(previous, "SKIP_ROUTE_EPOCH_CHANGED")
        previous["anchor"] = list(anchor)
    remaining = [c for c in CHECKPOINTS_MS if c > cp]
    previous["next_checkpoint_ms"] = remaining[0] if remaining else None
    previous["reason"] = decision["action"]
    if decision["action"] == "CONTINUE":
        previous["action"] = "CONTINUE"
        return True
    if not remaining:
        return _skip(
            previous,
            (
                "SKIP_ADVERSE_FLOW"
                if decision["action"] == "DEFER_ADVERSE_FLOW"
                else "SKIP_SOURCE_UNAVAILABLE"
            ),
        )
    previous["action"] = "WAIT"
    return False


def final_check(*, holder, clock, validate_owner, save):
    """Inspect freshest local evidence after gateway waits, before transport.

    Any exception is provably not sent here. Save failures must prevent send.
    """
    state = holder.get(KEY)
    if not isinstance(state, dict):
        return
    if state.get("action") == "TRANSPORT_STARTED":
        raise EntryNotSent("transport_already_started")
    try:
        now = clock()
        if state.get("action") != "CONTINUE" or _ms(now) > state["deadline_ms"]:
            _skip(state, "SKIP_DEADLINE")
            raise ValueError(state["action"])
        selected = load_policy(
            scope=state["scope"],
            now=now,
            signal_at=datetime.fromisoformat(state["signal_at"]),
        )
        if (
            selected is None
            or selected["pin"] != state["pin"]
            or validate_owner() is not True
        ):
            _skip(state, "SKIP_POLICY_OR_OWNER_CHANGED")
            raise ValueError(state["action"])
        snapshot, _ = load_live_dynamic_confirmation_source()
        now = clock()
        decision = evaluate_snapshot(
            snapshot=snapshot,
            symbol=state["scope"]["symbol"],
            route=state["scope"]["route"],
            cutoff_ms=_ms(now),
            require_latest=True,
        )
        state["pre_transport"] = decision
        if decision.get("epoch") is not None and list(
            (decision["item"], decision["epoch"])
        ) != state.get("anchor"):
            _skip(state, "SKIP_ROUTE_EPOCH_CHANGED")
            raise ValueError(state["action"])
        if decision["action"] != "CONTINUE":
            state["action"] = (
                "WAIT"
                if state.get("next_checkpoint_ms") is not None
                else "SKIP_FINAL_REVALIDATION"
            )
            raise ValueError(decision["action"])
        deadline = min(
            state["deadline_ms"], state.get("owner_deadline_ms", state["deadline_ms"])
        )
        if selected["policy"].get("valid_until"):
            deadline = min(
                deadline,
                _ms(datetime.fromisoformat(selected["policy"]["valid_until"])) - 1,
            )
        # Account for local validation/save latency without another API read.
        deadline = min(
            deadline,
            *(
                decision["feature"][key]["at_ms"] + MAXIMUM_SOURCE_AGE_MS
                for key in ("endpoint_depth", "endpoint_trade")
            ),
        )
        now_ms = _ms(clock())
        if now_ms < state["last_evaluated_ms"] or now_ms > deadline:
            _skip(state, "SKIP_DEADLINE")
            raise ValueError(state["action"])
        state.update(action="TRANSPORT_STARTED", transport_started_ms=now_ms)
        save()  # crash after this marker is ambiguous, never automatically retry
        if not now_ms <= _ms(clock()) <= deadline:
            _skip(state, "SKIP_DEADLINE")
            raise ValueError(state["action"])
    except Exception as exc:
        if not terminal(state) and state.get("action") != "WAIT":
            _skip(state, "SKIP_PRETRANSPORT_ERROR")
        elif state.get("action") == "TRANSPORT_STARTED":
            _skip(state, "SKIP_PRETRANSPORT_ERROR")
        raise EntryNotSent(str(exc)) from exc
