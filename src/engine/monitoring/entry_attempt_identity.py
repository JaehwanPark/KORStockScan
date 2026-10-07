"""Call-local submit telemetry; never an order, lifecycle or policy identity.

Monitoring owns this surface. Context-local fields do not mutate stock state,
cross threads implicitly, or grant execution authority.
"""

from contextvars import ContextVar
from functools import wraps
import logging
import re
from uuid import uuid4

_ATTEMPT = ContextVar("entry_submit_observation_attempt", default=None)

_MACHINE_LINEAGE_FIELDS = frozenset(
    {
        "entry_primary_decision_owner",
        "evaluation_attempt_id",
        "scanner_promotion_id",
        "watch_origin",
        "watch_admission_id",
        "watch_generation_id",
        "machine_observation_sha256",
        "machine_capture_status",
        "machine_revision_schema",
        "effective_venue",
        "market_session_bucket",
        "policy_bundle_hash",
        "entry_mechanistic_action",
        "entry_ai_screen_status",
        "entry_ai_screen_pass",
        "entry_mechanistic_policy_version",
    }
)


def observe_submit_attempt(function=None, *, on_finish=None):
    if function is None:
        return lambda target: observe_submit_attempt(target, on_finish=on_finish)

    @wraps(function)
    def wrapped(stock, code, *args, **kwargs):
        try:
            identity = {
                "record_id": str(stock.get("id") or ""),
                "code": str(code),
                "attempt_id": uuid4().hex,
                "promotion_id": _promotion_id(stock),
                "watch_identity": _watch_identity(stock),
                "machine_lineage": {},
                "broker_submit_accepted": False,
                "return_outcome": "not_returned",
            }
        except Exception as exc:
            identity = None
            logging.getLogger(__name__).warning(
                "Submit identity telemetry failed: %s", type(exc).__name__
            )
        token = _ATTEMPT.set(identity)
        outcome = "raised"
        try:
            result = function(stock, code, *args, **kwargs)
            return_outcome = (
                "returned_true"
                if result is True
                else "returned_false" if result is False else "returned_other"
            )
            current = _ATTEMPT.get()
            if isinstance(current, dict):
                current = {**current, "return_outcome": return_outcome}
                _ATTEMPT.set(current)
                outcome = (
                    "broker_accepted"
                    if current.get("broker_submit_accepted") is True
                    else return_outcome
                )
            else:
                outcome = return_outcome
            return result
        except Exception:
            current = _ATTEMPT.get()
            if isinstance(current, dict):
                current = {**current, "return_outcome": "raised"}
                _ATTEMPT.set(current)
                if current.get("broker_submit_accepted") is True:
                    outcome = "broker_accepted"
            raise
        finally:
            try:
                if on_finish is not None:
                    on_finish(stock, code, outcome)
            except Exception as exc:
                # Telemetry failure cannot change order execution or its result.
                logging.getLogger(__name__).warning(
                    "Submit completion telemetry failed: %s", type(exc).__name__
                )
            finally:
                _ATTEMPT.reset(token)

    return wrapped


def _promotion_id(stock):
    value = str(stock.get("scanner_promotion_id") or "").strip()
    return "" if value.lower() in {"none", "null", "unknown", "-", "0"} else value


def _watch_identity(stock):
    return tuple(str(stock.get(key) or "").strip() for key in
                 ("watch_origin", "watch_admission_id", "watch_generation_id"))


def bind_submit_attempt_machine_lineage(stock, code, source, *, replace_existing=False):
    """Bind trusted diagnostic lineage to the current submit invocation only.

    The binding is telemetry-only and cannot grant submit authority.  A caller
    may supply only the existing machine provenance allowlist; incomplete
    identity is rejected rather than partially projected downstream.
    """

    value = _ATTEMPT.get()
    if (
        not isinstance(value, dict)
        or value.get("record_id") != str(stock.get("id") or "")
        or value.get("code") != str(code)
        or not isinstance(source, dict)
    ):
        return False
    if replace_existing:
        # A real in-call AI retry is a new evaluation. Incomplete retry
        # provenance must never borrow the prior evaluation's terminal.
        value = {**value, "machine_lineage": {}}
        _ATTEMPT.set(value)
    lineage = {
        key: source[key]
        for key in _MACHINE_LINEAGE_FIELDS
        if source.get(key) not in (None, "", "-", "unknown", "UNKNOWN")
    }
    required = {
        "entry_primary_decision_owner",
        "evaluation_attempt_id",
        "effective_venue",
        "market_session_bucket",
        "policy_bundle_hash",
        "entry_mechanistic_action",
        "entry_ai_screen_status",
        "entry_ai_screen_pass",
    }
    if not required <= lineage.keys():
        return False
    fixed = value.get("watch_identity", ("",))[0] == "MAIN_FIXED_WATCH"
    if fixed:
        parent = value["watch_identity"]
        if (_watch_identity(source) != parent or _watch_identity(stock) != parent
                or not re.fullmatch(r"[0-9a-f]{64}", parent[2])
                or not re.match(r"FIXED-\d{4}-\d{2}-\d{2}-" + re.escape(str(code)[:6]) + "-", parent[1])
                or str(stock.get("code") or "")[:6] != str(code)[:6]
                or str(source.get("effective_venue")).upper() != str(stock.get("effective_venue")).upper()
                or source.get("market_session_bucket") != stock.get("market_session_bucket")):
            return False
        if (lineage.get("machine_capture_status") != "captured"
                or not re.fullmatch(r"[0-9a-f]{64}", str(lineage.get("machine_observation_sha256") or ""))):
            return False
        # A fixed watch is admitted by its native watch ID, never a fabricated
        # scanner promotion. Reject ambiguous simultaneous origin claims.
        if _promotion_id(source) or _promotion_id(stock):
            return False
        lineage.pop("scanner_promotion_id", None)
    elif (_watch_identity(source)[0] == "MAIN_FIXED_WATCH"
          or not _promotion_id(source)):
        return False
    if (
        str(lineage["entry_primary_decision_owner"]) != "mechanistic_entry_adjudicator"
        or str(lineage["effective_venue"]).upper()
        not in {"KRX", "NXT", "PREMARKET_KRX_LIKE", "KRX_NXT_INTEGRATED"}
        or ":" in str(lineage["market_session_bucket"])
        or str(lineage["entry_mechanistic_action"]).upper()
        not in {"ENTER_NOW", "RECHECK", "BLOCK", "SOURCE_INVALID"}
        or (
            str(lineage["entry_mechanistic_action"]).upper() == "ENTER_NOW"
            and lineage.get("entry_ai_screen_pass") is not True
        )
    ):
        return False
    expected_parent = _promotion_id(stock) if replace_existing else value.get("promotion_id")
    if not fixed and expected_parent and str(lineage["scanner_promotion_id"]) != str(expected_parent):
        return False
    updated = {**value, "machine_lineage": lineage}
    if not fixed and not updated.get("promotion_id"):
        updated["promotion_id"] = str(lineage["scanner_promotion_id"])
    _ATTEMPT.set(updated)
    return True


def submit_attempt_machine_lineage(stock, code):
    """Return the validated machine receipt bound to this submit call."""

    value = _ATTEMPT.get()
    if (
        not isinstance(value, dict)
        or value.get("record_id") != str(stock.get("id") or "")
        or value.get("code") != str(code)
        or not isinstance(value.get("machine_lineage"), dict)
    ):
        return {}
    return dict(value["machine_lineage"])


def mark_submit_attempt_broker_accepted(stock, code):
    """Mark a broker-acknowledged submit without changing function control flow."""

    value = _ATTEMPT.get()
    if (
        not isinstance(value, dict)
        or value.get("record_id") != str(stock.get("id") or "")
        or value.get("code") != str(code)
    ):
        return False
    _ATTEMPT.set({**value, "broker_submit_accepted": True})
    return True


def submit_attempt_fields(stock, code):
    value = _ATTEMPT.get()
    if (
        not isinstance(value, dict)
        or value.get("record_id") != str(stock.get("id") or "")
        or value.get("code") != str(code)
    ):
        return {}
    # The scanner may refresh the stock's promotion while this call waits.
    # Preserve that live metadata, but bind submit telemetry to one parent.
    # Late hydration may supply the first known parent before the first event.
    if not value.get("promotion_id") and value.get("watch_identity", ("",))[0] != "MAIN_FIXED_WATCH":
        parent = _promotion_id(stock)
        if parent:
            value = {**value, "promotion_id": parent}
            _ATTEMPT.set(value)
    fields = {
        "entry_submit_attempt_schema": "call_local_submit_attempt_v1",
        "entry_submit_attempt_id": value["attempt_id"],
        "entry_submit_attempt_authority": "observation_only",
        "entry_submit_attempt_broker_accepted": bool(
            value.get("broker_submit_accepted")
        ),
        "entry_submit_attempt_return_outcome": str(
            value.get("return_outcome") or "not_returned"
        ),
        **value.get("machine_lineage", {}),
    }
    if value.get("promotion_id"):
        fields["entry_submit_attempt_parent_promotion_id"] = value["promotion_id"]
    if value.get("watch_identity", ("",))[0] == "MAIN_FIXED_WATCH":
        fields["entry_submit_attempt_parent_watch_admission_id"] = value["watch_identity"][1]
        fields["entry_submit_attempt_parent_watch_generation_id"] = value["watch_identity"][2]
    return fields
