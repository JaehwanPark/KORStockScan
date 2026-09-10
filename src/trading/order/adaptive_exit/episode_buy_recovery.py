"""Bounded terminal-only recovery for an already-journaled episode BUY.

This does not extend the original cancel/write deadline. Independent launcher
authority must supply all read bounds; there are no automatic defaults or new
broker methods. The existing dated/current proof parser remains authoritative.
"""

from copy import deepcopy
from dataclasses import dataclass
from typing import Callable

from src.trading.config.machine_adaptive_exit_policy import canonical_sha256

KEY = "terminal_recovery"
SCHEMA = "episode_buy_terminal_recovery_v1"


class TerminalRecoveryReloadRequired(ValueError):
    """Published state differs: report without writing the older memory image."""


def require_durable_recovery_state(machine, leg, journal_key):
    """Protect late-read accounting before clock, schema or consumer checks."""
    stored = next(
        (
            row
            for row in machine._load_state().get("legs", [])
            if row.get("leg_id") == leg.get("leg_id")
        ),
        None,
    )
    journals = (leg.get(journal_key), (stored or {}).get(journal_key))
    if any(isinstance(j, dict) and KEY in j for j in journals) and stored != leg:
        raise TerminalRecoveryReloadRequired("terminal_recovery_durable_state_mismatch")


@dataclass(frozen=True)
class TerminalRecoveryServices:
    maximum_observations: int
    minimum_interval_ms: int
    window_ms: int
    authorize: Callable[[dict], bool]

    def __post_init__(self):
        if (
            any(
                type(v) is not int or v <= 0
                for v in (
                    self.maximum_observations,
                    self.minimum_interval_ms,
                    self.window_ms,
                )
            )
            or self.minimum_interval_ms > self.window_ms
            or not callable(self.authorize)
        ):
            raise ValueError("explicit_terminal_recovery_read_bounds_required")

    @property
    def bounds(self):
        return {
            k: getattr(self, k)
            for k in ("maximum_observations", "minimum_interval_ms", "window_ms")
        }


def validate_record(journal):
    """Validate historic read accounting at projection and its direct consumer."""
    record = journal.get(KEY)
    if KEY not in journal:
        return
    if not isinstance(record, dict):
        raise ValueError("terminal_recovery_record_invalid")
    contract = record.get("contract")
    if not isinstance(contract, dict):
        raise ValueError("terminal_recovery_contract_invalid")
    bounds = contract.get("bounds")
    if not isinstance(bounds, dict):
        raise ValueError("terminal_recovery_bounds_invalid")
    try:
        services = TerminalRecoveryServices(**bounds, authorize=lambda _: False)
    except TypeError as exc:
        raise ValueError("terminal_recovery_bounds_invalid") from exc
    expected = {
        "schema": SCHEMA,
        "action_id": journal["action_id"],
        "original_deadline_ms": journal["deadline_ms"],
        "deadline_ms": journal["deadline_ms"] + services.window_ms,
        "bounds": services.bounds,
        "terminal_only": True,
    }
    starts = record.get("observation_starts_ms")
    if (
        contract != expected
        or contract.get("terminal_only") is not True
        or record.get("canonical_sha256") != canonical_sha256(record)
        or not isinstance(starts, list)
        or not 1 <= len(starts) <= services.maximum_observations
        or any(
            type(t) is not int
            or not journal["deadline_ms"] <= t < expected["deadline_ms"]
            for t in starts
        )
        or any(b - a < services.minimum_interval_ms for a, b in zip(starts, starts[1:]))
    ):
        raise ValueError("terminal_recovery_accounting_invalid")


def recover(pending):
    services = getattr(pending.services, "terminal_recovery", None)
    if not isinstance(services, TerminalRecoveryServices):
        return "pending_buy_confirmation_deadline_requires_recovery"
    return _Recovery(pending, services).run()


class _Recovery:
    def __init__(self, pending, services):
        self.p, self.services = pending, services
        validate_record(pending.journal)
        self.contract = {
            "schema": SCHEMA,
            "action_id": pending.journal["action_id"],
            "original_deadline_ms": pending.journal["deadline_ms"],
            # Never anchored to restart or first late observation time.
            "deadline_ms": pending.journal["deadline_ms"] + services.window_ms,
            "bounds": services.bounds,
            "terminal_only": True,
        }
        old = pending.journal.get(KEY)
        if old is not None and old["contract"] != self.contract:
            raise ValueError("terminal_recovery_frozen_bounds_changed")
        self.starts = list(old["observation_starts_ms"]) if old else []

    def allowed(self):
        p = self.p

        def clock_now():
            return p.reader._transport.now_ms() if p.reader else p.now_ms

        now = clock_now()
        state, digest = p.m._state, canonical_sha256(p.m._state)
        journal_hash = canonical_sha256(p.journal)
        request = {
            "schema": SCHEMA,
            "action": "RECONCILE_TERMINAL_ONLY",
            "binding": deepcopy(p.binding),
            "contract": deepcopy(self.contract),
            "journal": deepcopy(p.journal),
        }
        return (
            getattr(p.services, "terminal_recovery", None) is self.services
            and self.contract["original_deadline_ms"]
            <= now
            < self.contract["deadline_ms"]
            and (not self.starts or now >= self.starts[-1])
            and self.services.authorize(request) is True
            and getattr(p.m.adaptive_exit_services, "pending_buy", None) is p.services
            and getattr(p.services, "terminal_recovery", None) is self.services
            and p.m._adaptive_authority_current()
            and p.m._state is state
            and canonical_sha256(p.m._state) == digest
            and canonical_sha256(p.journal) == journal_hash
            and now <= clock_now() < self.contract["deadline_ms"]
        )

    def durable(self):
        p = self.p
        stored = next(
            (
                r
                for r in p.m._load_state().get("legs", [])
                if r.get("leg_id") == p.leg["leg_id"]
            ),
            None,
        )
        if stored != p.leg:
            raise TerminalRecoveryReloadRequired(
                "terminal_recovery_durable_state_mismatch"
            )

    def run(self):
        p = self.p
        # Even a terminal wait/budget status must not cause the owner loop to
        # persist stale memory over a previously published reservation/proof.
        self.durable()
        if p.now_ms >= self.contract["deadline_ms"]:
            return "terminal_recovery_window_exhausted"
        if self.starts and p.now_ms < self.starts[-1]:
            return "terminal_recovery_clock_regression"
        if len(self.starts) >= self.services.maximum_observations:
            return "terminal_recovery_observation_budget_exhausted"
        if (
            self.starts
            and p.now_ms - self.starts[-1] < self.services.minimum_interval_ms
        ):
            return "terminal_recovery_interval_wait"
        p.terminal_recovery = self
        if not p.authorized():
            raise PermissionError("terminal_recovery_independent_authority_required")
        # A published-but-failed save must be reloaded, never overwritten by
        # the caller's older in-memory observation budget.
        self.durable()
        record = {
            "contract": self.contract,
            "observation_starts_ms": self.starts + [p.now_ms],
        }
        record["canonical_sha256"] = canonical_sha256(record)
        p.save({**p.journal, KEY: record})
        self.starts = record["observation_starts_ms"]
        self.durable()
        if not p.authorized():
            raise PermissionError("terminal_recovery_independent_authority_required")
        p.build_reader()
        # Reconciliation has no cancel/replacement branch, even if the source
        # is still open. Each bounded read is charged before the first I/O.
        return p._step_with_reader(terminal_only=True)
