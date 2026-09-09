"""Durable original-widget final EXIT binding; no signal or broker authority.

The owner must validate the producer signal and its frozen execution policy
before issuing this receipt. It survives source disappearance after acceptance,
but cannot move across episodes, lots or policy versions. BUY/merged-target
recovery remains with the original owner, not an implicit side effect here.
"""

from src.trading.config.machine_adaptive_exit_policy import canonical_sha256

FINAL_EXIT_KEY = "adaptive_exit_final_exit_request"
SCHEMA = "machine_adaptive_exit_original_final_exit_v1"


def _binding(sessions, entry_signal_id, execution_policy):
    if (
        not sessions
        or not isinstance(entry_signal_id, str)
        or not entry_signal_id
        or not isinstance(execution_policy, dict)
        or not isinstance(execution_policy.get("policy_id"), str)
        or not execution_policy["policy_id"]
        or execution_policy.get("source_final_exit_action")
        != "sell_own_filled_quantity"
    ):
        raise ValueError("adaptive_final_exit_explicit_source_policy_required")
    for s in sessions:
        s.validate()
    scope = sessions[0].policy.scope_key
    episode = sessions[0].context.position_id
    if any(
        s.context.owner_type != "widget_auto_trade"
        or s.policy.scope_key != scope
        or s.context.position_id != episode
        for s in sessions
    ) or len({s.binding_hash for s in sessions}) != len(sessions):
        raise ValueError("adaptive_final_exit_scope_or_episode_conflict")
    return {
        "schema": SCHEMA,
        "scope_key": scope,
        "position_id": episode,
        "entry_signal_id": entry_signal_id,
        "execution_policy_hash": canonical_sha256(execution_policy),
        "session_bindings": sorted(s.binding_hash for s in sessions),
    }


def make_final_exit_request(
    *,
    sessions,
    entry_signal_id,
    execution_policy,
    signal_id,
    source_hash,
    observed_at_ms,
    accepted_at_ms,
    route,
    source_session,
):
    payload = _binding(sessions, entry_signal_id, execution_policy) | {
        "signal_id": signal_id,
        "source_hash": source_hash,
        "observed_at_ms": observed_at_ms,
        "accepted_at_ms": accepted_at_ms,
        "route": route,
        "source_session": source_session,
    }
    payload["canonical_sha256"] = canonical_sha256(payload)
    validate_final_exit_request(
        payload,
        sessions=sessions,
        entry_signal_id=entry_signal_id,
        execution_policy=execution_policy,
        now_ms=accepted_at_ms,
    )
    return payload


def validate_final_exit_request(
    payload,
    *,
    sessions,
    entry_signal_id,
    execution_policy,
    now_ms,
):
    expected = _binding(sessions, entry_signal_id, execution_policy)
    if not isinstance(payload, dict):
        raise ValueError("adaptive_final_exit_receipt_missing")
    fields = {
        "signal_id",
        "source_hash",
        "observed_at_ms",
        "accepted_at_ms",
        "route",
        "source_session",
        "canonical_sha256",
    }
    if (
        set(payload) != set(expected) | fields
        or any(payload.get(k) != v for k, v in expected.items())
        or payload.get("canonical_sha256") != canonical_sha256(payload)
        or not isinstance(payload.get("signal_id"), str)
        or not payload["signal_id"]
        or not isinstance(payload.get("source_hash"), str)
        or len(payload["source_hash"]) != 64
        or any(c not in "0123456789abcdef" for c in payload["source_hash"])
        or type(payload.get("observed_at_ms")) is not int
        or type(payload.get("accepted_at_ms")) is not int
        or type(now_ms) is not int
        or not max(s.position.first_fill_at_ms for s in sessions)
        <= payload["observed_at_ms"]
        <= payload["accepted_at_ms"]
        <= now_ms
        or payload.get("route") not in {"KRX", "NXT"}
        or expected["scope_key"].split("|")[3] not in {"SOR", payload.get("route")}
        or expected["scope_key"].split("|")[4] != payload.get("source_session")
    ):
        raise ValueError("adaptive_final_exit_receipt_binding_invalid")
