"""Bounded report-only incident reconciliation; no producer or trading calls."""
from __future__ import annotations

import hashlib
import json

STAGE_HOOKS = {
    "legacy_machine_report": "machine_result_semantics",
    "main_machine_policy": "machine_result_semantics",
    "main_auxiliary_policy": "auxiliary_result_semantics",
    "postclose_handoff": "postclose_handoff_semantics",
    "entry_cancel_wait_tuning": "entry_cancel_wait_result_semantics",
    "samsung_frozen_validation": "samsung_frozen_validation_semantics",
    "holding_profit_exit": "holding_profit_exit_semantics",
    "initial_quantity": "initial_quantity_semantics",
    "main_stop_confirmation": "main_stop_confirmation_semantics",
}
RECOVERY_STATES = frozenset({
    "pass", "warning", "source_gap", "review_required", "incumbent_carry",
    "candidate_selected", "cumulative_winrate_selected", "done",
    "operator_initial_registered", "verified_carried", "published_policy",
    "valid_empty", "policy_selected", "journal_terminal_observed",
    "pending_submit", "pending_terminal",
})
NATIVE_BOUND_STATES = frozenset({
    "operator_initial_registered", "verified_carried", "published_policy",
    "cumulative_winrate_selected",
})
IDENTITY_KEYS = ("source_date", "target_date", "stage", "scope", "reason")
METRIC_CONTRACT = dict(
    metric_role="source_quality_gate", decision_authority="report_only",
    window_policy="native_exact_date_generation_and_existing_bounded_window",
    sample_floor="expected_source_contract_no_statistical_floor",
    primary_decision_metric="exact_binding_delivery_recovery_findings",
    source_quality_gate="native_validator_and_complete_observation",
    forbidden_uses=["trading_mutation", "policy_mutation", "provider_mutation",
                    "missing_as_zero_ev", "unobserved_execution_success"],
)


def fingerprint(incident):
    # An owner transfer is not a new incident. Missing hashes keep a stable
    # expected-path identity; observation time and run ID never enter this key.
    fields = [incident.get(k) for k in IDENTITY_KEYS]
    fields += [incident.get("generation"), incident.get("artifact")]
    return hashlib.sha256(json.dumps(fields, separators=(",", ":")).encode()).hexdigest()


def bound_observation(details, incident, report_date):
    observed = next((r.get("semantics") or {} for r in details.get("semantic_observations", [])
                     if isinstance(r, dict) and r.get("stage") == incident.get("stage")
                     and (r.get("semantics") or {}).get("source_date") == incident.get("source_date")),
                    details.get(STAGE_HOOKS.get(incident.get("stage"))) or {})
    bound = any(isinstance(b, dict) and b.get("as_of_date") == report_date
                and b.get("stage") == incident.get("stage")
                and all(b.get(k) == observed.get(k) for k in ("source_date", "target_date", "status"))
                and b.get("generation") == observed.get("report_sha256")
                for b in details.get("semantic_source_bindings", []))
    return observed, bound


def closure_verified(incident, observed, bound):
    if (observed.get("source_date") != incident.get("source_date")
            or observed.get("status") not in RECOVERY_STATES
            or (incident.get("target_date") is not None
                and observed.get("target_date") != incident.get("target_date"))
            or not observed.get("report_sha256")
            or observed.get("observation_complete") is False
            or observed.get("generation_changed")
            or (observed.get("status") in NATIVE_BOUND_STATES and not bound)):
        return False
    if incident.get("stage") in {"holding_profit_exit", "initial_quantity", "main_stop_confirmation"} and (
            not bound or observed.get("native_validated") is not True):
        return False
    scope = incident.get("scope")
    if scope not in {None, "report"} and scope not in (observed.get("scopes") or {}):
        return False
    scoped = (observed.get("scopes") or {}).get(scope, observed)
    reason = str(incident.get("reason") or "")
    if scoped.get("findings"):
        return False
    scope_verified = (scope not in {None, "report"} and scoped is not observed
        and scoped.get("observation_complete") is True
        and scoped.get("native_validated") is True
        and scoped.get("report_sha256") == observed.get("report_sha256"))
    if observed.get("findings") and not scope_verified:
        return False  # A partial native check cannot prove a missing reason fixed.
    comparison_gap = (observed.get("policy_states") or {}).get("comparison_state") == "source_gap"
    if comparison_gap and any(word in reason for word in ("source", "comparison", "population", "label", "economic", "paired")):
        return False
    if observed.get("status") in {"source_gap", "review_required"} and not comparison_gap and not scope_verified:
        return False
    if incident.get("stage") == "entry_cancel_wait_tuning":
        if reason == "cancel_wait_consumer_projection_invalid" and (observed.get("consumers") or {}).get("status") != "verified":
            return False
        if reason in {"cancel_wait_execution_failed", "cancel_wait_completed_report_missing"} and (observed.get("execution") or {}).get("command_status") != "succeeded":
            return False
    return True


def reconcile(state, details, report_date, incoming, *, source_matches):
    unresolved, history = {}, list(state.get("historical_semantic_incidents") or [])
    for incident in (state.get("semantic_incidents") or {}).values():
        if not isinstance(incident, dict):
            continue
        key = fingerprint(incident)
        observed, bound = bound_observation(details, incident, report_date)
        stale_generation = any(all(old.get(k) == incident.get(k) for k in IDENTITY_KEYS)
            and old.get('generation') == observed.get('report_sha256')
            and old.get('disposition') == 'superseded_generation_unrecovered' for old in history)
        native_date = incident.get("source_date") if bound or source_matches(incident) else report_date
        if incident.get("source_date") != native_date:
            history.append(dict(incident, disposition="historical_unrecovered"))
        elif (bound and observed.get("status") in {"off", "historical_diagnostic", "retired"}
              and observed.get("report_sha256")):
            history.append(dict(incident, disposition=observed["status"] + "_unrecovered"))
        elif not stale_generation and closure_verified(incident, observed, bound):
            history.append(dict(incident, disposition="native_recovered",
                                recovery_generation=observed["report_sha256"]))
        else:
            unresolved[key] = incident
    for incident in incoming:
        for key, previous in list(unresolved.items()):
            if all(previous.get(k) == incident.get(k) for k in IDENTITY_KEYS) and fingerprint(previous) != fingerprint(incident):
                history.append(dict(previous, disposition="superseded_generation_unrecovered"))
                del unresolved[key]
        unresolved[fingerprint(incident)] = incident
    overflow = dict(state.get("semantic_overflow") or {})
    for name, rows in (("unresolved", list(unresolved.values())[:-128]), ("history", history[:-128])):
        if rows:
            overflow[name + "_omitted_count"] = int(overflow.get(name + "_omitted_count", 0)) + len(rows)
            overflow[name + "_last_examples"] = [
                {k: row.get(k) for k in (*IDENTITY_KEYS, "artifact", "generation")} for row in rows[-8:]]
    state.update(semantic_incidents=dict(list(unresolved.items())[-128:]),
                 historical_semantic_incidents=history[-128:], semantic_overflow=overflow,
                 semantic_state_complete=not bool(overflow), semantic_state_schema=2)
    return state
