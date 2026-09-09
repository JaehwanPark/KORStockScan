"""Owner-loop dependencies, not a policy issuer or a second order owner.

Launchers must supply independently reviewed authority, lock and safety checks.
Persisted sessions alone never enable broker I/O. This module does not install
those services or enroll a position in an exit policy.
"""

from dataclasses import dataclass
from typing import Callable

from .models import Clock, Snapshot
from .runtime import OwnerSession, RegisteredOwnerExitPort
from .terminal import terminal_receipt
from .arbitration import SCHEMA as FINAL_EXIT_SCHEMA
from src.trading.config.machine_adaptive_exit_policy import canonical_sha256

SESSION_KEY = "adaptive_exit_session"


@dataclass(frozen=True)
class OwnerLoopServices:
    lock_held: Callable[[], bool]
    authorize_binding: Callable[[dict], bool]
    owner_guard: Callable
    snapshot_loader: Callable[[OwnerSession, Clock], Snapshot | None]
    clock_loader: Callable[[OwnerSession, int], Clock]
    # Independent validation of the original owner's frozen source-EXIT
    # policy, not another user approval or authority from a raw signal/hash.
    authorize_final_exit: Callable[[dict], bool] | None = None


def manager_required(records) -> bool:
    """Invalid custody is not a completed manager; retain it for recovery."""
    for record in records:
        try:
            if OwnerSession.from_payload(record).manager_required:
                return True
        except (ValueError, TypeError, KeyError):
            return True
    return False


def step_session(
    *,
    session,
    services,
    adapter_factory,
    persist_record,
    clock,
    persist_terminal=None,
    final_exit_requested=False,
    final_exit_request=None,
):
    if not isinstance(services, OwnerLoopServices):
        return "owner_loop_services_missing"
    if type(final_exit_requested) is not bool:
        return "final_exit_authority_invalid"
    if services.lock_held() is not True:
        return "original_owner_lock_required"
    if final_exit_requested and (
        not isinstance(final_exit_request, dict)
        or not callable(services.authorize_final_exit)
    ):
        return "adaptive_final_exit_policy_authority_missing"
    if final_exit_requested and (
        final_exit_request.get("schema") != FINAL_EXIT_SCHEMA
        or final_exit_request.get("scope_key") != session.policy.scope_key
        or final_exit_request.get("position_id") != session.context.position_id
        or not isinstance(final_exit_request.get("session_bindings"), list)
        or session.binding_hash not in final_exit_request["session_bindings"]
        or final_exit_request.get("canonical_sha256")
        != canonical_sha256(final_exit_request)
    ):
        return "adaptive_final_exit_receipt_binding_invalid"

    def authorized(binding):
        return services.authorize_binding(binding) is True and (
            not final_exit_requested
            or services.authorize_final_exit(final_exit_request) is True
        )

    # Check before even constructing a gateway adapter or loading market data.
    if not authorized(session.binding):
        return "frozen_policy_authority_missing"
    verified_clock = services.clock_loader(session, clock.now_ms)
    if not isinstance(verified_clock, Clock) or verified_clock.now_ms != clock.now_ms:
        return "owner_loop_verified_clock_missing"
    port = RegisteredOwnerExitPort(
        session=session,
        adapter_factory=adapter_factory,
        persist_record=persist_record,
        lock_held=services.lock_held,
        owner_guard=services.owner_guard,
        authorize_binding=authorized,
    )
    snapshot = (
        services.snapshot_loader(port.session, verified_clock)
        if port.session.manager_required
        else None
    )
    updated = port.step(
        snapshot=snapshot,
        clock=verified_clock,
        final_exit_requested=final_exit_requested,
    )
    if not updated.manager_required and persist_terminal is not None:
        if services.lock_held() is not True:
            raise PermissionError("original_owner_lock_required")
        if not authorized(updated.binding):
            return "frozen_policy_authority_missing"
        receipt = terminal_receipt(
            session=updated, adapter=port._adapter, observed_at_ms=clock.now_ms
        )
        if services.lock_held() is not True:
            raise PermissionError("original_owner_lock_required")
        persist_terminal(receipt)
    return updated.driver.alert_reason or "owner_loop_step_completed"
