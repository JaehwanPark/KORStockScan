"""One original reversal budget; no admission, policy or order authority."""

from dataclasses import dataclass
from collections.abc import Mapping
import hashlib
import json
import math
import os
import time

LEGACY_SIGNAL_MAX_AGE_SEC = 5.0


def validate_lifetime_policy(policy):
    """A family-owned finite lifetime; never a queue/load-derived timeout."""
    if (
        not isinstance(policy, Mapping)
        or not isinstance(policy.get("version"), str)
        or not policy["version"].isascii()
        or not 0 < len(policy["version"]) <= 128
    ):
        raise ValueError("entry_signal_lifetime_policy_invalid")
    schema = policy.get("schema")
    if schema == "entry_signal_lifetime_policy_v1":
        if set(policy) != {"schema", "version", "max_signal_age_sec"}:
            raise ValueError("entry_signal_lifetime_policy_invalid")
        ages = [policy["max_signal_age_sec"]]
    elif schema == "entry_signal_lifetime_policy_v2":
        if set(policy) != {
            "schema",
            "version",
            "default_max_signal_age_sec",
            "branch_max_signal_age_sec",
        }:
            raise ValueError("entry_signal_lifetime_policy_invalid")
        branches = policy["branch_max_signal_age_sec"]
        if (
            not isinstance(branches, Mapping)
            or not branches
            or len(branches) > 128
            or any(
                not isinstance(k, str) or not k.isascii() or not k or len(k) > 256
                for k in branches
            )
            or policy["default_max_signal_age_sec"] != LEGACY_SIGNAL_MAX_AGE_SEC
            or type(policy["default_max_signal_age_sec"]) not in (int, float)
        ):
            raise ValueError("entry_signal_lifetime_policy_invalid")
        ages = [policy["default_max_signal_age_sec"], *branches.values()]
    else:
        raise ValueError("entry_signal_lifetime_policy_invalid")
    if any(
        type(age) not in (int, float) or not math.isfinite(age) or age <= 0
        for age in ages
    ):
        raise ValueError("entry_signal_lifetime_policy_invalid")
    validated = dict(policy)
    if schema == "entry_signal_lifetime_policy_v2":
        validated["branch_max_signal_age_sec"] = dict(branches)
    return validated


def _policy_hash(policy):
    return hashlib.sha256(
        json.dumps(
            policy, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def _event_branch_ids(event):
    """Use the immutable original lineage even if live checks filter a branch."""
    lineage = event.get("anchor_lineage")
    signals = event.get("branch_signals")
    if lineage is not None:
        if not isinstance(lineage, Mapping) or not lineage:
            raise ValueError("entry_signal_lifetime_branches_invalid")
        ids = list(lineage)
        if (
            not isinstance(signals, Mapping)
            or not signals
            or not set(signals).issubset(ids)
        ):
            raise ValueError("entry_signal_lifetime_branches_invalid")
    elif signals is not None:
        if not isinstance(signals, Mapping) or not signals:
            raise ValueError("entry_signal_lifetime_branches_invalid")
        ids = list(signals)
    else:
        branch = event.get("extended_definition_id") or event.get("branch_id")
        ids = [branch] if branch is not None else []
    if any(not isinstance(b, str) or not b.isascii() or not b for b in ids):
        raise ValueError("entry_signal_lifetime_branches_invalid")
    return sorted(ids)


def _event_lifetime(policy, event):
    if policy["schema"] == "entry_signal_lifetime_policy_v1":
        return policy["max_signal_age_sec"], None
    ids = _event_branch_ids(event)
    values = policy["branch_max_signal_age_sec"]
    default = policy["default_max_signal_age_sec"]
    # Every branch present at confirmation must permit the longer budget.
    return min((values.get(b, default) for b in ids), default=default), ids


def bind_signal_lifetime(event, policy, *, live_clock=False):
    """Issue once at confirmation. Legacy evidence keeps its original bytes."""
    if policy is None:
        return
    policy = validate_lifetime_policy(policy)
    if "entry_signal_lifetime" in event:
        signal_deadline_epoch(event)
        if event["entry_signal_lifetime"]["policy"] != policy:
            raise ValueError("entry_signal_lifetime_already_issued")
        return
    epoch = event.get("epoch")
    if type(epoch) not in (int, float) or not math.isfinite(epoch):
        raise ValueError("entry_signal_confirmation_invalid")
    max_age, branch_ids = _event_lifetime(policy, event)
    event["entry_signal_lifetime"] = dict(
        schema=(
            "entry_signal_lifetime_v2"
            if branch_ids is not None
            else "entry_signal_lifetime_v1"
        ),
        policy=policy,
        policy_sha256=_policy_hash(policy),
        signal_id=event["signal_id"],
        generation=event["registry_generation"],
        confirmed_epoch=epoch,
        deadline_epoch=epoch + max_age,
    )
    if branch_ids is not None:
        event["entry_signal_lifetime"]["branch_ids"] = branch_ids
    if live_clock:
        # Bind before claim/admission. Wall-clock rollback must not renew the
        # original confirmation's remaining real processing time.
        perf, stamp = time.perf_counter(), time.time()
        event["entry_signal_lifetime"]["clock"] = dict(
            pid=os.getpid(),
            issued_epoch=stamp,
            issued_perf=perf,
            deadline_perf=perf + (epoch + max_age - stamp),
        )
    signal_deadline_epoch(event)


def signal_deadline_epoch(event):
    """Read the issued lifetime, or the dated legacy contract, without renewal."""
    epoch = event["epoch"]
    if type(epoch) not in (int, float) or not math.isfinite(epoch):
        raise ValueError("entry_signal_confirmation_invalid")
    issued = event.get("entry_signal_lifetime")
    if issued is None:
        return epoch + LEGACY_SIGNAL_MAX_AGE_SEC
    if not isinstance(issued, Mapping):
        raise ValueError("entry_signal_lifetime_invalid")
    policy = validate_lifetime_policy(issued.get("policy"))
    max_age, branch_ids = _event_lifetime(policy, event)
    expected = epoch + max_age
    if (
        issued.get("schema")
        != (
            "entry_signal_lifetime_v2"
            if branch_ids is not None
            else "entry_signal_lifetime_v1"
        )
        or (branch_ids is not None and issued.get("branch_ids") != branch_ids)
        or issued.get("signal_id") != event.get("signal_id")
        or issued.get("generation") != event.get("registry_generation")
        or issued.get("confirmed_epoch") != epoch
        or issued.get("policy_sha256") != _policy_hash(policy)
        or type(issued.get("deadline_epoch")) not in (int, float)
        or issued["deadline_epoch"] != expected
        or not math.isfinite(expected)
        or expected <= epoch
    ):
        raise ValueError("entry_signal_lifetime_invalid")
    clock = issued.get("clock")
    if clock is not None and (
        not isinstance(clock, Mapping)
        or type(clock.get("pid")) is not int
        or clock["pid"] <= 0
        or any(
            type(clock.get(k)) not in (int, float) or not math.isfinite(clock[k])
            for k in ("issued_epoch", "issued_perf", "deadline_perf")
        )
        or clock["deadline_perf"]
        != clock["issued_perf"] + (expected - clock["issued_epoch"])
    ):
        raise ValueError("entry_signal_lifetime_clock_invalid")
    return expected


def signal_is_current(event, now, *, live_clock=False):
    # One exclusive upper boundary, shared with the physical send guard.
    current = (
        type(now) in (int, float)
        and math.isfinite(now)
        and event["epoch"] <= now < signal_deadline_epoch(event)
    )
    if live_clock and event.get("entry_signal_lifetime") is not None:
        clock = event["entry_signal_lifetime"].get("clock")
        return bool(
            current
            and clock
            and clock["pid"] == os.getpid()
            and clock["issued_perf"] <= time.perf_counter() < clock["deadline_perf"]
        )
    return current


def claim_deadline_epoch(claim):
    if claim is None:
        return None
    try:
        return signal_deadline_epoch(claim["snapshot"][0])
    except (KeyError, TypeError, IndexError, ValueError, OverflowError):
        return 0.0  # Malformed input cannot acquire a renewed budget.


@dataclass(frozen=True)
class EntryDeadline:
    epoch: float
    perf: float

    @classmethod
    def create(cls, claim=None, caller_epoch=None, caller_perf=None):
        native_deadline = claim_deadline_epoch(claim)
        values = [v for v in (native_deadline, caller_epoch) if v is not None]
        if not values:
            return None
        if any(isinstance(v, bool) or not math.isfinite(float(v)) for v in values):
            raise ValueError("entry_machine_input_deadline_invalid")
        epoch = min(map(float, values))
        now = time.time()
        # Source wall-clock validity remains the native validator's job.
        perf = time.perf_counter() + max(0.0, epoch - now)
        if native_deadline is not None and native_deadline > 0:
            event = claim["snapshot"][0]
            clock = (event.get("entry_signal_lifetime") or {}).get("clock")
            if clock is not None:
                if clock["pid"] != os.getpid():
                    raise ValueError("entry_signal_lifetime_pid_changed")
                perf = min(perf, clock["deadline_perf"])
        if caller_perf is not None:
            if isinstance(caller_perf, bool) or not math.isfinite(float(caller_perf)):
                raise ValueError("entry_machine_input_deadline_invalid")
            perf = min(perf, float(caller_perf))
        return cls(epoch, perf)

    def remaining(self):
        return max(0.0, min(self.epoch - time.time(), self.perf - time.perf_counter()))

    def require(self):
        if self.remaining() <= 0:
            raise ValueError("entry_machine_input_deadline_expired")

    def transport_ms(self, existing_ms, reserve_sec=0.0, *, facts=None):
        # No minimum timeout may enlarge the remaining claim budget.
        remaining = self.remaining()
        value = int(min(float(existing_ms), (remaining - reserve_sec) * 1000))
        if facts is not None:
            facts.update(
                budget_before_transport_ms=remaining * 1000,
                response_reserve_ms=reserve_sec * 1000,
                configured_transport_limit_ms=float(existing_ms),
                timeout_override_ms=value,
                original_deadline_epoch=self.epoch,
                original_deadline_perf=self.perf,
            )
        if value < 1:
            raise ValueError("entry_machine_input_deadline_expired")
        return value
