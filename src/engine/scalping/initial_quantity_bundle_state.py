"""Durable compare-and-swap custody for a sequential initial BUY bundle.

This journal owns a single attempted bundle. It never submits or cancels an
order. A persisted submit intent without a broker order number is deliberately
unexecutable after restart and must be reconciled outside this module.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from src.engine.scalping.initial_quantity_timeout import (
    _terminal_proof_valid, next_bundle_timeout_action, timeout_schedule_valid,
)

SCHEMA = "initial_quantity_bundle_state_v1"
SCHEMA_DYNAMIC_PRICE = "initial_quantity_bundle_state_v2"
TARGET_INDEX_SCHEMA = "initial_quantity_bundle_target_index_v1"
_STATES = {"NOT_SUBMITTED", "SUBMIT_INTENT", "OPEN", "PARTIAL",
           "CANCEL_REQUESTED", "TERMINAL_FILLED", "TERMINAL_CANCELLED",
           "TERMINAL_SKIPPED", "UNCERTAIN"}
_TERMINAL = {"TERMINAL_FILLED", "TERMINAL_CANCELLED", "TERMINAL_SKIPPED"}
_TRANSITIONS = {
    "NOT_SUBMITTED": {"SUBMIT_INTENT", "TERMINAL_SKIPPED"},
    "SUBMIT_INTENT": {"OPEN", "UNCERTAIN"},
    "UNCERTAIN": {"OPEN", "PARTIAL", "CANCEL_REQUESTED"},
    "OPEN": {"PARTIAL", "CANCEL_REQUESTED", "TERMINAL_FILLED"},
    "PARTIAL": {"CANCEL_REQUESTED", "TERMINAL_FILLED"},
    "CANCEL_REQUESTED": {"TERMINAL_FILLED", "TERMINAL_CANCELLED"},
}


def _digest(body: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(
        body, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest()


def bundle_state_path(base_dir: Path, attempt_id: str) -> Path:
    """Use a digest path so an attempt identifier cannot escape its owner root."""
    if (not isinstance(attempt_id, str) or not 1 <= len(attempt_id) <= 160
            or not attempt_id.isascii() or not attempt_id.isprintable()):
        raise ValueError("initial_bundle_attempt_id_invalid")
    return Path(base_dir) / (hashlib.sha256(attempt_id.encode()).hexdigest() + ".json")


def bundle_target_index_path(base_dir: Path, code: str, target_id: str) -> Path:
    """Address one live target without trusting either identifier as a path."""
    if (not isinstance(code, str) or not re.fullmatch(r"[0-9]{6}", code)
            or not isinstance(target_id, str) or not target_id
            or len(target_id) > 160 or not target_id.isascii()
            or not target_id.isprintable()):
        raise ValueError("initial_bundle_target_identity_invalid")
    key = hashlib.sha256(f"{code}:{target_id}".encode()).hexdigest()
    return Path(base_dir) / "target_index" / f"{key}.json"


def bundle_state_valid(state: Any) -> bool:
    if not isinstance(state, dict):
        return False
    try:
        body = {key: value for key, value in state.items()
                if key != "bundle_content_sha256"}
        schedule = state["schedule"]
        legs = state["planned_legs"]
        statuses = state["leg_states"]
        requested = state["requested_qty"]
        if (set(state) != {"schema", "attempt_id", "code", "target_id",
                            "policy_sha256", "schedule", "schedule_sha256",
                            "planned_legs", "requested_qty", "leg_states",
                            "generation", "parent_content_sha256",
                            "bundle_content_sha256"}
                or state["schema"] not in {SCHEMA, SCHEMA_DYNAMIC_PRICE}
                or not timeout_schedule_valid(schedule)
                or state["schedule_sha256"] != schedule["schedule_sha256"]
                or state["policy_sha256"] != schedule["policy_sha256"]
                or not re.fullmatch(r"[0-9]{6}", state["code"])
                or not isinstance(state["target_id"], str)
                or not state["target_id"]
                or bundle_state_path(Path("/"), state["attempt_id"]).suffix != ".json"
                or type(requested) is not int or requested <= 0
                or not isinstance(legs, list)
                or not isinstance(statuses, list)
                or len(legs) != schedule["leg_count"]
                or len(statuses) != len(legs)
                or (state["generation"] == 0 and any(
                    item.get("state") != "NOT_SUBMITTED"
                    for item in statuses if isinstance(item, dict)))
                or sum(leg["qty"] for leg in legs) != requested
                or type(state["generation"]) is not int or state["generation"] < 0
                or (state["generation"] == 0)
                != (state["parent_content_sha256"] is None)
                or (state["generation"] > 0 and not re.fullmatch(
                    r"[0-9a-f]{64}", state["parent_content_sha256"]))
                or state["bundle_content_sha256"] != _digest(body)):
            return False
        for index, (leg, status) in enumerate(zip(legs, statuses)):
            if (not isinstance(leg, dict)
                    or set(leg) != {"leg_index", "qty", "price", "route", "tag"}
                    or leg["leg_index"] != index
                    or type(leg["qty"]) is not int or leg["qty"] <= 0
                    or type(leg["price"]) is not int
                    or (state["schema"] == SCHEMA and leg["price"] < 0)
                    or (state["schema"] == SCHEMA_DYNAMIC_PRICE
                        and leg["price"] != 0)
                    or leg["route"] not in {"KRX", "NXT", "SOR"}
                    or not isinstance(leg["tag"], str) or not leg["tag"]
                    or (leg["tag"] == "initial_quantity_probe_0"
                        and (state["schema"] != SCHEMA_DYNAMIC_PRICE
                             or index != 0 or leg["qty"] != 1))
                    or not isinstance(status, dict)
                    or status.get("state") not in _STATES):
                return False
            if state["schema"] == SCHEMA_DYNAMIC_PRICE:
                submitted = status["state"] not in {
                    "NOT_SUBMITTED", "TERMINAL_SKIPPED",
                }
                bound_price = status.get("submit_price")
                client_intent = status.get("owner_client_intent_id")
                if (submitted and (type(bound_price) is not int
                                   or bound_price <= 0
                                   or not isinstance(client_intent, str)
                                   or not 1 <= len(client_intent) <= 240
                                   or any(char in client_intent for char in "\r\n\t"))) or (
                        not submitted and ("submit_price" in status
                                           or "owner_client_intent_id" in status)):
                    return False
            elif "submit_price" in status or "owner_client_intent_id" in status:
                return False
            if status["state"] != "NOT_SUBMITTED" and index > 0 and not all(
                    prior.get("state") in _TERMINAL
                    and prior["terminal_confirmed_at_epoch"] <=
                    schedule["slots"][prior_index]["terminal_confirm_by_epoch"]
                    for prior_index, prior in enumerate(statuses[:index])):
                return False
            order_no = status.get("broker_order_no")
            if (status["state"] in {"OPEN", "PARTIAL", "CANCEL_REQUESTED",
                                   "TERMINAL_FILLED", "TERMINAL_CANCELLED"}
                    and (not isinstance(order_no, str)
                         or not re.fullmatch(r"[0-9]{7}", order_no))):
                return False
            if status["state"] in {"NOT_SUBMITTED", "SUBMIT_INTENT",
                                   "TERMINAL_SKIPPED"} and order_no:
                return False
            if status["state"] not in {"NOT_SUBMITTED", "TERMINAL_SKIPPED"}:
                intent_at = status.get("submit_intent_at_epoch")
                slot = schedule["slots"][index]
                if (not isinstance(intent_at, (int, float))
                        or isinstance(intent_at, bool)
                        or not math.isfinite(intent_at)
                        or not slot["slot_start_epoch"] <= intent_at
                        < slot["cancel_request_by_epoch"]):
                    return False
            if status["state"] in _TERMINAL:
                confirmed = status.get("terminal_confirmed_at_epoch")
                if (not isinstance(confirmed, (int, float))
                        or isinstance(confirmed, bool)
                        or (status["state"] != "TERMINAL_SKIPPED"
                            and status.get("ordered_qty") != leg["qty"])
                        or (status["state"] != "TERMINAL_SKIPPED"
                            and confirmed < status["submit_intent_at_epoch"])
                        or not _terminal_proof_valid(
                            status, status["state"], schedule["slots"][index],
                            confirmed)):
                    return False
        return True
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        return False


def new_bundle_state(*, attempt_id: str, code: str, target_id: str,
                     schedule: dict[str, Any], planned_legs: list[dict[str, Any]],
                     requested_qty: int, schema: str = SCHEMA) -> dict[str, Any]:
    body = {"schema": schema, "attempt_id": attempt_id, "code": code,
            "target_id": target_id, "policy_sha256": schedule["policy_sha256"],
            "schedule": schedule, "schedule_sha256": schedule["schedule_sha256"],
            "planned_legs": planned_legs, "requested_qty": requested_qty,
            "leg_states": [{"state": "NOT_SUBMITTED"} for _ in planned_legs],
            "generation": 0, "parent_content_sha256": None}
    state = {**body, "bundle_content_sha256": _digest(body)}
    if not bundle_state_valid(state):
        raise ValueError("initial_bundle_state_invalid")
    return state


def _transition_valid(previous: dict[str, Any], next_state: dict[str, Any]) -> bool:
    immutable = ("schema", "attempt_id", "code", "target_id", "policy_sha256",
                 "schedule", "schedule_sha256", "planned_legs", "requested_qty")
    if (any(previous[key] != next_state[key] for key in immutable)
            or next_state["generation"] != previous["generation"] + 1
            or next_state["parent_content_sha256"] !=
            previous["bundle_content_sha256"]):
        return False
    changed = [(index, old, new) for index, (old, new) in enumerate(zip(
        previous["leg_states"], next_state["leg_states"])) if old != new]
    if len(changed) != 1:
        return False
    index, old, new = changed[0]
    old_state = old["state"]
    new_state = new["state"]
    if old_state in _TERMINAL:
        return False
    if (old.get("broker_order_no")
            and new.get("broker_order_no") != old["broker_order_no"]):
        return False
    if (previous["schema"] == SCHEMA_DYNAMIC_PRICE
            and old_state not in {"NOT_SUBMITTED", "TERMINAL_SKIPPED"}
            and (new.get("submit_price") != old.get("submit_price")
                 or new.get("owner_client_intent_id") !=
                 old.get("owner_client_intent_id"))):
        return False
    if new_state == old_state:
        return bool(old_state in {"OPEN", "PARTIAL", "CANCEL_REQUESTED", "UNCERTAIN"}
                    and old.get("broker_order_no") == new.get("broker_order_no")
                    and old.get("submit_intent_at_epoch") ==
                    new.get("submit_intent_at_epoch"))
    if new_state == "SUBMIT_INTENT":
        return bool(old_state == "NOT_SUBMITTED" and all(
            prior.get("state") in _TERMINAL
            and prior["terminal_confirmed_at_epoch"] <=
            previous["schedule"]["slots"][prior_index]["terminal_confirm_by_epoch"]
            for prior_index, prior in enumerate(previous["leg_states"][:index])
        ))
    if old_state != "NOT_SUBMITTED" and new_state != "TERMINAL_SKIPPED":
        if (old.get("submit_intent_at_epoch") !=
                new.get("submit_intent_at_epoch")):
            return False
    return new_state in _TRANSITIONS.get(old_state, ())


def next_bundle_state(previous: dict[str, Any], leg_index: int,
                      leg_state: dict[str, Any]) -> dict[str, Any]:
    if (not bundle_state_valid(previous) or type(leg_index) is not int
            or not 0 <= leg_index < len(previous["leg_states"])
            or not isinstance(leg_state, dict)):
        raise ValueError("initial_bundle_transition_input_invalid")
    states = [dict(item) for item in previous["leg_states"]]
    states[leg_index] = dict(leg_state)
    body = {key: value for key, value in previous.items()
            if key != "bundle_content_sha256"}
    body.update(leg_states=states, generation=previous["generation"] + 1,
                parent_content_sha256=previous["bundle_content_sha256"])
    successor = {**body, "bundle_content_sha256": _digest(body)}
    if not bundle_state_valid(successor) or not _transition_valid(previous, successor):
        raise ValueError("initial_bundle_transition_invalid")
    return successor


def read_bundle_state(path: Path) -> dict[str, Any] | None:
    try:
        state = json.loads(Path(path).read_bytes())
    except (OSError, ValueError, UnicodeError):
        return None
    return (state if bundle_state_valid(state)
            and Path(path).name == bundle_state_path(
                Path(path).parent, state["attempt_id"]).name else None)


def recover_bundle_state(
    path: Path, observed: dict[str, Any], *, indexed_journal_authority: bool = False,
) -> tuple[dict[str, Any] | None, str]:
    """Reconcile a restored in-memory bundle with its durable CAS journal.

    Only the journal may advance memory. A missing, corrupt, older, or different
    plan blocks the caller; it must never cause a fresh BUY submission.
    """
    if not bundle_state_valid(observed):
        return None, "observed_bundle_invalid"
    try:
        expected_path = bundle_state_path(Path(path).parent, observed["attempt_id"])
    except ValueError:
        return None, "observed_bundle_invalid"
    if Path(path) != expected_path:
        return None, "bundle_path_mismatch"
    persisted = read_bundle_state(path)
    if persisted is None:
        return None, "bundle_journal_missing_or_invalid"
    immutable = ("schema", "attempt_id", "code", "target_id", "policy_sha256",
                 "schedule", "schedule_sha256", "planned_legs", "requested_qty")
    if any(persisted[key] != observed[key] for key in immutable):
        return None, "bundle_identity_or_plan_mismatch"
    if indexed_journal_authority is True:
        indexed, index_status = read_bundle_for_target(
            Path(path).parent, observed["code"], observed["target_id"])
        if (index_status not in {"target_bundle_loaded", "target_bundle_terminal"}
                or indexed != persisted):
            return None, "bundle_target_index_invalid"
    if persisted["generation"] < observed["generation"]:
        return None, "bundle_journal_behind_memory"
    if persisted["generation"] == observed["generation"]:
        if persisted != observed:
            return None, "bundle_same_generation_conflict"
        return persisted, "bundle_journal_current"
    if (persisted["generation"] > observed["generation"] + 1
            and indexed_journal_authority is not True):
        return None, "bundle_history_gap"
    if (persisted["generation"] == observed["generation"] + 1
            and persisted["parent_content_sha256"] != observed["bundle_content_sha256"]):
        return None, "bundle_parent_conflict"
    return persisted, "bundle_journal_ahead"


def save_bundle_state_cas(path: Path, state: dict[str, Any], *,
                          expected_parent_sha256: str | None) -> str:
    """Persist exactly one monotonic transition; fail closed on stale writers."""
    path = Path(path)
    if not bundle_state_valid(state):
        raise ValueError("initial_bundle_state_invalid")
    if path.name != bundle_state_path(path.parent, state["attempt_id"]).name:
        raise ValueError("initial_bundle_path_invalid")
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(".lock")
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        prior = read_bundle_state(path) if path.exists() else None
        if path.exists() and prior is None:
            raise ValueError("initial_bundle_current_corrupt")
        if prior is None:
            if expected_parent_sha256 is not None or state["generation"] != 0:
                raise ValueError("initial_bundle_parent_mismatch")
        elif (expected_parent_sha256 != prior["bundle_content_sha256"]
              or not _transition_valid(prior, state)):
            raise ValueError("initial_bundle_parent_or_transition_invalid")
        encoded = (json.dumps(state, ensure_ascii=True, sort_keys=True,
                              separators=(",", ":")) + "\n").encode()
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".bundle.",
                                             suffix=".tmp", delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return state["bundle_content_sha256"]


def persist_dynamic_leg_submit_intent(
    base_dir: Path, observed: dict[str, Any], *, leg_index: int,
    submit_price: int, owner_client_intent_id: str, now_epoch: float,
) -> dict[str, Any]:
    """Commit P1's final price before the one permitted broker call."""
    if (not bundle_state_valid(observed)
            or observed["schema"] != SCHEMA_DYNAMIC_PRICE
            or type(leg_index) is not int
            or type(submit_price) is not int or submit_price <= 0
            or isinstance(now_epoch, bool)
            or not isinstance(now_epoch, (int, float))
            or not math.isfinite(now_epoch)):
        raise ValueError("initial_bundle_submit_intent_input_invalid")
    indexed, status = read_bundle_for_target(
        base_dir, observed["code"], observed["target_id"])
    if status != "target_bundle_loaded" or indexed != observed:
        raise ValueError("initial_bundle_submit_intent_index_conflict")
    decision = next_bundle_timeout_action(
        observed["schedule"], observed["leg_states"], now_epoch=now_epoch)
    if decision.get("action") != "SUBMIT" or decision.get("leg_index") != leg_index:
        raise ValueError("initial_bundle_submit_intent_slot_closed")
    successor = next_bundle_state(observed, leg_index, {
        "state": "SUBMIT_INTENT",
        "submit_intent_at_epoch": now_epoch,
        "submit_price": submit_price,
        "owner_client_intent_id": owner_client_intent_id,
    })
    save_bundle_state_cas(
        bundle_state_path(base_dir, observed["attempt_id"]), successor,
        expected_parent_sha256=observed["bundle_content_sha256"],
    )
    return successor


def persist_dynamic_leg_submit_response(
    base_dir: Path, observed_intent: dict[str, Any], *,
    leg_index: int, broker_order_no: str | None,
    owner_exact: bool,
) -> dict[str, Any]:
    """Seal exact owner ACK or an uncertain result; never create retry power."""
    if (not bundle_state_valid(observed_intent)
            or observed_intent["schema"] != SCHEMA_DYNAMIC_PRICE
            or type(leg_index) is not int
            or not 0 <= leg_index < len(observed_intent["leg_states"])
            or observed_intent["leg_states"][leg_index]["state"] != "SUBMIT_INTENT"
            or type(owner_exact) is not bool):
        raise ValueError("initial_bundle_submit_response_input_invalid")
    indexed, status = read_bundle_for_target(
        base_dir, observed_intent["code"], observed_intent["target_id"])
    if status != "target_bundle_loaded" or indexed != observed_intent:
        raise ValueError("initial_bundle_submit_response_index_conflict")
    state = dict(observed_intent["leg_states"][leg_index])
    exact_number = bool(isinstance(broker_order_no, str)
                        and re.fullmatch(r"[0-9]{7}", broker_order_no))
    state["state"] = "OPEN" if owner_exact and exact_number else "UNCERTAIN"
    if exact_number:
        state["broker_order_no"] = broker_order_no
    successor = next_bundle_state(observed_intent, leg_index, state)
    save_bundle_state_cas(
        bundle_state_path(base_dir, observed_intent["attempt_id"]), successor,
        expected_parent_sha256=observed_intent["bundle_content_sha256"],
    )
    return successor


def _target_index_valid(index: Any, *, code: str, target_id: str) -> bool:
    if not isinstance(index, dict):
        return False
    try:
        body = {key: value for key, value in index.items()
                if key != "index_content_sha256"}
        return bool(
            set(index) == {"schema", "phase", "code", "target_id", "attempt_id",
                           "policy_sha256", "schedule_sha256",
                           "initial_bundle_content_sha256", "index_content_sha256"}
            and index["schema"] == TARGET_INDEX_SCHEMA
            and index["phase"] in {"active", "terminal"}
            and index["code"] == code and index["target_id"] == target_id
            and bundle_state_path(Path("/"), index["attempt_id"]).suffix == ".json"
            and all(re.fullmatch(r"[0-9a-f]{64}", index[key])
                    for key in ("policy_sha256", "schedule_sha256",
                                "initial_bundle_content_sha256"))
            and index["index_content_sha256"] == _digest(body)
        )
    except (KeyError, TypeError, ValueError):
        return False


def read_bundle_for_target(base_dir: Path, code: str,
                           target_id: str) -> tuple[dict[str, Any] | None, str]:
    """Recover the exact journal for a target after in-memory state is lost."""
    try:
        index_path = bundle_target_index_path(base_dir, code, target_id)
    except ValueError:
        return None, "target_identity_invalid"
    try:
        index = json.loads(index_path.read_bytes())
    except FileNotFoundError:
        return None, "target_index_absent"
    except (OSError, ValueError, UnicodeError):
        return None, "target_index_unreadable"
    if not _target_index_valid(index, code=code, target_id=target_id):
        return None, "target_index_invalid"
    bundle = read_bundle_state(bundle_state_path(base_dir, index["attempt_id"]))
    if (bundle is None or bundle["code"] != code
            or bundle["target_id"] != target_id
            or bundle["attempt_id"] != index["attempt_id"]
            or bundle["policy_sha256"] != index["policy_sha256"]
            or bundle["schedule_sha256"] != index["schedule_sha256"]
            or (bundle["generation"] == 0 and
                bundle["bundle_content_sha256"] !=
                index["initial_bundle_content_sha256"])):
        return None, "target_bundle_identity_or_journal_invalid"
    if index["phase"] == "terminal" and any(
            item["state"] not in _TERMINAL for item in bundle["leg_states"]):
        return None, "target_terminal_index_journal_not_terminal"
    return bundle, ("target_bundle_terminal" if index["phase"] == "terminal"
                    else "target_bundle_loaded")


def _write_target_index_atomic(path: Path, index: dict[str, Any]) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
                dir=path.parent, prefix=".target.", suffix=".tmp",
                delete=False) as handle:
            temporary = Path(handle.name)
            handle.write((json.dumps(index, sort_keys=True,
                                     separators=(",", ":")) + "\n").encode())
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def create_indexed_bundle(base_dir: Path, initial: dict[str, Any]) -> Path:
    """Persist an initial plan and its recovery pointer before any BUY intent."""
    if not bundle_state_valid(initial) or initial["generation"] != 0:
        raise ValueError("initial_indexed_bundle_invalid")
    base_dir = Path(base_dir)
    index_path = bundle_target_index_path(
        base_dir, initial["code"], initial["target_id"])
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.with_suffix(".lock").open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        if index_path.exists():
            observed, status = read_bundle_for_target(
                base_dir, initial["code"], initial["target_id"])
            if status == "target_bundle_loaded" and observed == initial:
                return bundle_state_path(base_dir, initial["attempt_id"])
            if status != "target_bundle_terminal":
                raise ValueError("initial_bundle_target_already_active_or_invalid")
        bundle_path = bundle_state_path(base_dir, initial["attempt_id"])
        if bundle_path.exists():
            # A crash can land after the first durable journal write and
            # before the target pointer. Only that exact generation-zero
            # journal is safe to finish indexing; no broker intent exists yet.
            if read_bundle_state(bundle_path) != initial:
                raise ValueError("initial_bundle_orphan_journal_conflict")
        else:
            save_bundle_state_cas(
                bundle_path, initial, expected_parent_sha256=None)
        body = {
            "schema": TARGET_INDEX_SCHEMA,
            "phase": "active",
            "code": initial["code"],
            "target_id": initial["target_id"],
            "attempt_id": initial["attempt_id"],
            "policy_sha256": initial["policy_sha256"],
            "schedule_sha256": initial["schedule_sha256"],
            "initial_bundle_content_sha256": initial["bundle_content_sha256"],
        }
        index = {**body, "index_content_sha256": _digest(body)}
        _write_target_index_atomic(index_path, index)
        if read_bundle_for_target(base_dir, initial["code"], initial["target_id"]) != (
                initial, "target_bundle_loaded"):
            raise ValueError("initial_bundle_target_readback_invalid")
        return bundle_path


def retire_indexed_bundle(base_dir: Path, terminal: dict[str, Any]) -> bool:
    """Keep a durable terminal tombstone across a stock-state handoff crash."""
    if (not bundle_state_valid(terminal)
            or any(item["state"] not in _TERMINAL
                   for item in terminal["leg_states"])):
        raise ValueError("initial_bundle_not_terminal")
    base_dir = Path(base_dir)
    index_path = bundle_target_index_path(
        base_dir, terminal["code"], terminal["target_id"])
    if not index_path.exists():
        return False
    with index_path.with_suffix(".lock").open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        observed, status = read_bundle_for_target(
            base_dir, terminal["code"], terminal["target_id"])
        if status not in {"target_bundle_loaded", "target_bundle_terminal"} or observed != terminal:
            raise ValueError("initial_bundle_target_terminal_mismatch")
        if status == "target_bundle_terminal":
            return False
        index = json.loads(index_path.read_bytes())
        body = {key: value for key, value in index.items()
                if key != "index_content_sha256"}
        body["phase"] = "terminal"
        _write_target_index_atomic(
            index_path, {**body, "index_content_sha256": _digest(body)})
        return True
