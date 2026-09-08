"""Call-local submit telemetry; never an order, lifecycle or policy identity.

Monitoring owns this surface. Context-local fields do not mutate stock state,
cross threads implicitly, or grant execution authority.
"""

from contextvars import ContextVar
from functools import wraps
import logging
from uuid import uuid4

_ATTEMPT = ContextVar("entry_submit_observation_attempt", default=None)


def observe_submit_attempt(function=None, *, on_finish=None):
    if function is None:
        return lambda target: observe_submit_attempt(target, on_finish=on_finish)

    @wraps(function)
    def wrapped(stock, code, *args, **kwargs):
        try:
            identity = (
                str(stock.get("id") or ""),
                str(code),
                uuid4().hex,
                _promotion_id(stock),
            )
        except Exception as exc:
            identity = None
            logging.getLogger(__name__).warning(
                "Submit identity telemetry failed: %s", type(exc).__name__
            )
        token = _ATTEMPT.set(identity)
        outcome = "raised"
        try:
            result = function(stock, code, *args, **kwargs)
            outcome = (
                "returned_true"
                if result is True
                else "returned_false" if result is False else "returned_other"
            )
            return result
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


def submit_attempt_fields(stock, code):
    value = _ATTEMPT.get()
    if value is None or value[:2] != (str(stock.get("id") or ""), str(code)):
        return {}
    # The scanner may refresh the stock's promotion while this call waits.
    # Preserve that live metadata, but bind submit telemetry to one parent.
    # Late hydration may supply the first known parent before the first event.
    if not value[3]:
        parent = _promotion_id(stock)
        if parent:
            value = (*value[:3], parent)
            _ATTEMPT.set(value)
    fields = {
        "entry_submit_attempt_schema": "call_local_submit_attempt_v1",
        "entry_submit_attempt_id": value[2],
        "entry_submit_attempt_authority": "observation_only",
    }
    if value[3]:
        fields["entry_submit_attempt_parent_promotion_id"] = value[3]
    return fields
