"""Thin adapters: existing owners retain signal, order and custody authority."""

from datetime import datetime, timedelta, time
import hashlib
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.trade_pause_control import is_buy_side_paused
from src.trading.config.machine_entry_timing_policy import (
    resolve_entry_confirmation_policy,
)
from src.trading.order import entry_adverse_guard as guard

KST = ZoneInfo("Asia/Seoul")
EVENT_ROOT_ENV = "KORSTOCKSCAN_ENTRY_ADVERSE_EVENT_ROOT"


def record(holder):
    """Append a changed receipt under the existing owner, no new scheduler."""
    try:
        _record_receipt(holder)
        holder.pop(guard.KEY + "_receipt_error", None)
    except (OSError, TypeError, ValueError, KeyError) as exc:
        # The owner's durable state owns submit safety. Diagnostic disk errors
        # must not interrupt broker-result binding or existing exit management.
        holder[guard.KEY + "_receipt_error"] = type(exc).__name__


def terminalize_original_owner_guard(holder, reason):
    """Close diagnostic state after the original owner has already blocked BUY.

    This does not make or change an entry decision.  It only prevents a
    lifecycle that is already ``NO_FILL`` from leaving the optional adverse
    flow receipt in ``WAIT`` or ``CONTINUE``.
    """

    state = holder.get(guard.KEY)
    if not isinstance(state, dict) or guard.terminal(state):
        return False
    guard._skip(state, "SKIP_ORIGINAL_OWNER_GUARD")
    state["original_owner_guard_reason"] = str(reason or "unspecified")
    record(holder)
    return True


def _record_receipt(holder):
    import fcntl

    state = holder.get(guard.KEY)
    if not isinstance(state, dict):
        return
    raw = json.dumps(state, sort_keys=True, separators=(",", ":"), allow_nan=False)
    digest = hashlib.sha256(raw.encode()).hexdigest()
    if holder.get(guard.KEY + "_last_receipt_hash") == digest:
        return
    root = Path(
        os.getenv(EVENT_ROOT_ENV)
        or Path(__file__).resolve().parents[3] / "data/report/entry_adverse_flow_events"
    )
    signal_at = datetime.fromisoformat(state["signal_at"])
    if signal_at.utcoffset() is None:
        raise ValueError("receipt_clock_invalid")
    day = signal_at.date().isoformat()
    root.mkdir(parents=True, exist_ok=True)
    payload = dict(
        schema="entry_adverse_flow_receipt_v1",
        target_date=day,
        receipt_sha256=digest,
        state=state,
    )
    with (root / f"entry_adverse_flow_{day}.jsonl").open(
        "a", encoding="utf-8"
    ) as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    holder[guard.KEY + "_last_receipt_hash"] = digest


def now():
    return datetime.now(KST)


def expire_pending(machine, holder, observed):
    state = holder.get(guard.KEY)
    if not isinstance(state, dict) or guard.terminal(state):
        return
    if type(state.get("deadline_ms")) is not int:
        guard._skip(state, "SKIP_STATE_INVALID")
    elif int(observed.timestamp() * 1000) > state["deadline_ms"]:
        guard._skip(state, "SKIP_DEADLINE")
    else:
        return
    record(holder)
    machine._save()


def _timing(scope, entry_state="UNSPECIFIED"):
    return resolve_entry_confirmation_policy(
        target_date=now().date(),
        owner=scope["owner"],
        scope_id=scope["scope_id"],
        symbol=scope["symbol"],
        session=scope["session"],
        entry_state=entry_state,
    )


def _prepare(machine, holder, identity, signal_at, scope, entry_state, observed):
    # No policy or source work on the default OFF path.
    from src.trading.config.machine_entry_adverse_policy import PATH_ENV, HASH_ENV

    if (
        not os.getenv(PATH_ENV)
        and not os.getenv(HASH_ENV)
        and guard.KEY not in holder
        and guard.KEY + "_history" not in holder
    ):
        return True
    previous = holder.get(guard.KEY)
    if (
        isinstance(previous, dict)
        and previous.get("identity") == identity
        and previous.get("signal_at")
    ):
        try:
            signal_at = datetime.fromisoformat(previous["signal_at"])
            if signal_at.utcoffset() is None:
                raise ValueError("naive_signal_clock")
        except (TypeError, ValueError):
            guard._skip(previous, "SKIP_STATE_INVALID")
            machine._save()
            return False
    timing = _timing(scope, entry_state)
    allowed = guard.prepare(
        holder=holder,
        identity=identity,
        signal_at=signal_at,
        now=observed,
        scope=scope,
        timing_mode=timing["mode"],
        policy_hash=timing["provenance"].get("policy_hash"),
    )
    state = holder.get(guard.KEY)
    if isinstance(previous, dict) and previous.get("identity") != identity:
        record({guard.KEY: previous})
    if isinstance(state, dict) and not getattr(
        machine.gateway, "entry_adverse_transport_supported", False
    ):
        allowed = guard._skip(state, "SKIP_TRANSPORT_HOOK_UNAVAILABLE")
    record(holder)
    machine._save()
    return allowed






def _episode_scope(machine, leg):
    morning = getattr(machine, "strategy_name", "") == "morning"
    route = (
        str(leg.get("route", ""))
        if morning
        else str(getattr(machine.policy, "route", "SOR"))
    )
    return dict(
        owner=machine.entry_timing_owner,
        scope_id=machine.entry_timing_scope_id,
        symbol=str(machine.policy.symbol),
        route=route,
        session=(
            ("NXT_PREMARKET" if route == "NXT" else "KRX_REGULAR")
            if morning
            else machine.entry_timing_session
        ),
    )


def episode_prepare(machine, leg, observed):
    from src.trading.config.machine_entry_adverse_policy import (
        PATH_ENV,
        HASH_ENV,
        load_policy,
    )

    if (
        not os.getenv(PATH_ENV)
        and not os.getenv(HASH_ENV)
        and guard.KEY not in leg
        and guard.KEY + "_history" not in leg
    ):
        return True
    scope = _episode_scope(machine, leg)
    if guard.KEY not in leg and guard.KEY + "_history" not in leg:
        try:
            if load_policy(scope=scope, now=observed, signal_at=observed) is None:
                return True  # Unselected owner retains its original source contract.
        except (ValueError, OSError, TypeError, KeyError):
            pass  # Active malformed authority remains fail-closed below.
    features = machine._state.get("signal_features") or {}
    try:
        signal_at = datetime.fromisoformat(features["signal_decision_at"])
        if signal_at.utcoffset() is None:
            raise ValueError("naive_signal_clock")
    except (KeyError, TypeError, ValueError):
        leg["status"] = "NO_FILL"
        machine._record(
            observed, "entry_adverse_signal_time_missing", leg_id=leg["leg_id"]
        )
        machine._save()
        return False
    source_id = features.get("source_entry_event_id")
    identity = f"{source_id}:{leg['leg_id']}" if source_id else ""
    allowed = _prepare(
        machine, leg, identity, signal_at, scope, "UNSPECIFIED", observed
    )
    state = leg.get(guard.KEY)
    if isinstance(state, dict):
        if guard.terminal(state) and state["action"] != "TRANSPORT_STARTED":
            leg["status"] = "NO_FILL"
        machine._record(
            observed,
            "entry_adverse_flow_decision",
            leg_id=leg["leg_id"],
            entry_adverse_flow=dict(state),
        )
    return allowed


def regular_episode_deadline(policy, signal_bar, observed):
    bar = datetime.fromisoformat(signal_bar)
    if bar.utcoffset() is None:
        raise ValueError("naive_signal_bar")
    return min(
        datetime.combine(observed.date(), policy.scan_last_bar, tzinfo=KST) + timedelta(minutes=1),
        bar + timedelta(minutes=int(policy.entry_valid_completed_bars) + 1),
    )


def episode_callback(machine, leg):
    state = leg.get(guard.KEY)
    if not isinstance(state, dict):
        return None

    def validate():
        timing = _timing(state["scope"])
        current = now()
        features = machine._state.get("signal_features") or {}
        if getattr(machine, "strategy_name", "") == "morning":
            owner_end = datetime.combine(
                current.date(),
                machine._window(state["scope"]["route"]).deadline,
                tzinfo=KST,
            )
        else:
            try:
                owner_end = regular_episode_deadline(machine.policy, machine._state["signal_bar"], current)
            except ValueError:
                return False
        state["owner_deadline_ms"] = int(owner_end.timestamp() * 1000)
        return bool(
            current.date().isoformat() == state["signal_at"][:10]
            and state["identity"]
            == f"{features.get('source_entry_event_id')}:{leg['leg_id']}"
            and state["scope"] == _episode_scope(machine, leg)
            and state["scope"]["symbol"] == str(machine.policy.symbol)
            and str(
                (machine._state.get("signal_features") or {}).get(
                    "runtime_policy_hash", ""
                )
            )
            == str(machine.policy.runtime_policy_hash)
            and current < owner_end
            and not is_buy_side_paused()
            and timing["mode"] == "baseline_immediate"
            and timing["provenance"].get("policy_hash") == state["timing_policy_hash"]
            and machine._market_weakness_allows_new_buys(
                now=current, signal_bar=machine._state.get("signal_bar", "")
            )
        )

    def check():
        try:
            guard.final_check(
                holder=leg, clock=now, validate_owner=validate, save=machine._save
            )
        except guard.EntryNotSent:
            record(leg)
            raise

    return check
