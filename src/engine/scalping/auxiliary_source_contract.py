"""Source-only auxiliary provenance and census; never grants policy authority.

Lives beside the Main scalping producers/consumers. No broker, provider, state
mutation, default stop reconstruction, or policy publication belongs here.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime
import hashlib
import json
import math
import re

CONTRACT = "auxiliary_source_capsule_and_partition_v1"
DIAGNOSTIC_AUTHORITY = dict(
    metric_role="source_quality_diagnostic", decision_authority="report_only",
    window_policy="exact_frozen_source_manifest", sample_floor="not_applicable_source_census",
    primary_decision_metric="source_identity_and_stage_coverage",
    source_quality_gate="sealed_projection_and_exact_provenance",
    forbidden_uses=["live_promotion", "broker_authority", "realized_profit_claim", "missing_input_imputation"],
)
PARTITIONS = ("all", "samsung", "non_samsung", "unknown")
IDENTITY = (
    "source_date", "decision_ts", "stock_code", "effective_venue", "session_bucket",
    "broker_route", "evaluation_attempt_id", "decision_trace_id", "scanner_promotion_id",
    "watch_origin", "watch_admission_id", "watch_generation_id",
    "machine_observation_sha256", "machine_revision_parent_sha256", "machine_bundle_sha256",
    "machine_policy_sha256", "payload_sha256", "request_envelope_sha256", "prompt_sha256",
    "schema_sha256", "system_prompt_sha256", "provider_actual", "model",
)


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def partition(row):
    code = row.get("stock_code")
    if not isinstance(code, str) or not re.fullmatch(r"[0-9]{6}", code):
        return "unknown"
    return "samsung" if code == "005930" else "non_samsung"


def selected(row, scope):
    if scope not in PARTITIONS:
        raise ValueError("auxiliary_partition_invalid")
    return scope == "all" or partition(row) == scope


def unpack(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return {}
    return value if isinstance(value, dict) else {}


def identity_equal(key, left, right):
    if key in {"effective_venue", "session_bucket"} and isinstance(left, str) and isinstance(right, str):
        return left.upper() == right.upper()
    return left == right


def capsule(fields, *, producer, clock, references=None):
    """Lossless nullable identity + references to already persisted exact input.

    Hashes are content identity, not proof that an append succeeded. A receipt is
    external to the body it acknowledges; pre-AI observation and response clocks
    remain distinct. Never derive a missing historical field from today's state.
    """
    identity = {key: deepcopy(fields.get(key)) for key in IDENTITY}
    body = dict(schema=CONTRACT, producer=producer, producer_clock=clock,
        identity=identity, references=deepcopy(references or {}),
        missing_reasons={key: "not_recorded_at_this_stage" for key, value in identity.items()
                         if value is None or value == ""},
        runtime_effect=False, allowed_runtime_apply=False, broker_order_forbidden=True)
    return {**body, "sha256": digest(body)}


def capsule_errors(value, row=None):
    value = unpack(value)
    if not value:
        return ["capsule_absent"]
    try:
        if value.get("schema") != CONTRACT or value.get("sha256") != digest(
                {k: v for k, v in value.items() if k != "sha256"}):
            return ["capsule_hash_or_contract_invalid"]
    except (ValueError, TypeError):
        return ["capsule_hash_or_contract_invalid"]
    identity = value.get("identity") or {}
    errors = []
    if row:
        for key in IDENTITY:
            expected = row.get("evaluation_key") if key == "decision_trace_id" else row.get(key)
            if expected is not None and identity.get(key) is not None and not identity_equal(key, identity[key], expected):
                errors.append("capsule_identity_conflict:" + key)
    if value.get("runtime_effect") is not False or value.get("allowed_runtime_apply") is not False:
        errors.append("capsule_authority_invalid")
    references = value.get("references") or {}
    pre = unpack(references.get("pre_ai_capsule"))
    if pre:
        errors.extend("pre_ai:" + error for error in capsule_errors(pre))
        before = pre.get("identity") or {}
        for key in ("stock_code", "evaluation_attempt_id", "effective_venue", "session_bucket", "machine_bundle_sha256", "machine_observation_sha256"):
            if before.get(key) is not None and identity.get(key) is not None and not identity_equal(key, before[key], identity[key]):
                errors.append("pre_ai_identity_conflict:" + key)
        receipt = unpack(references.get("pre_ai_append_receipt"))
        # The response trace preserves the capsule even when the economic
        # pipeline append failed. That failure is an operating diagnostic; it
        # must not erase an independently exact AI input/response/label.
        if receipt.get("capsule_sha256") != pre.get("sha256"):
            errors.append("pre_ai_append_receipt_identity_invalid")
        pre_clock, clock = time_seconds(pre.get("producer_clock")), time_seconds(value.get("producer_clock"))
        if pre_clock is None or clock is None or pre_clock > clock:
            errors.append("pre_ai_clock_invalid")
    return errors


def plan_state(row):
    """Diagnostic contract only: a conditional probe cannot become a fill plan."""
    probe = unpack(row.get("entry_economic_observation_probe_contract"))
    errors = []
    conditional = unpack(row.get('entry_economic_conditional_seed'))
    if conditional:
        from src.engine.scalping.entry_probe_conditional_replay import valid_seed
        if (not valid_seed(conditional)
                or conditional.get('plan_sha256') != row.get('entry_economic_plan_sha256')
                or conditional.get('plan_sha256') != row.get('entry_economic_writer_plan_sha256')
                or any(not identity_equal(k, conditional.get(k), row.get(k))
                       for k in ('stock_code','evaluation_attempt_id','scanner_promotion_id','effective_venue','session_bucket'))):
            return dict(state='source_gap', executable=False, stop_status='unproven',
                        errors=['conditional_exact_plan_identity_invalid'])
        return dict(state='conditional_plan_preserved', executable=False,
                    stop_status='frozen_native_exit_inputs_not_realized_exit', errors=[])
    if probe:
        body = {k: v for k, v in probe.items() if k != "sha256"}
        if (probe.get("schema") != "entry_pre_ai_conditional_probe_observation_v1"
                or probe.get("sha256") != digest(body)):
            errors.append("conditional_probe_hash_invalid")
        if probe.get("stock_code") != row.get("stock_code"):
            errors.append("conditional_probe_symbol_conflict")
        if probe.get("reservation_performed") is not False or probe.get("runtime_effect") is not False:
            errors.append("conditional_probe_authority_invalid")
        if not errors:
            return dict(state="conditional_on_unknown_fill", executable=False,
                        stop_status="not_proven_by_conditional_plan", errors=[])
    if errors:
        state = "source_gap"
    elif row.get("entry_economic_source_blocker") == "exact_broker_capacity_missing":
        state = "capacity_receipt_missing"
    elif row.get("entry_economic_guard_receipt"):
        guard = unpack(row["entry_economic_guard_receipt"])
        state = "guard_blocked" if guard.get("allowed") is False else "source_gap"
    elif row.get("entry_economic_writer_plan_sha256"):
        state = "plan_known_pre_ai"
    else:
        state = "source_gap"
    return dict(state=state, executable=False, stop_status="requires_exact_owner_replay", errors=errors)


def machine_record(payload):
    """Compact census projection from the existing sequential payload scan."""
    context = payload.get("label_context") or {}
    assessment = (payload.get("source") or {}).get("assessment") or {}
    fields = {**context, **{k: payload.get(k) for k in
        ("watch_origin", "watch_admission_id", "watch_generation_id", "scanner_promotion_id")}}
    body_sha = digest({k: v for k, v in payload.items() if k != "machine_observation_sha256"})
    return {**{k: fields.get(k) for k in IDENTITY},
        "machine_observation_sha256": payload.get("machine_observation_sha256"),
        "machine_bundle_sha256": payload.get("bundle_sha256"),
        "decision_ts": payload.get("captured_at"), "machine_action": assessment.get("action"),
        "record_kind": "machine", "source_body_sha256": body_sha,
        "source_identity_valid": body_sha == payload.get("machine_observation_sha256") and payload.get("redacted") is False}


def response_record(trace):
    return {**{k: trace.get(k) for k in IDENTITY}, "record_kind": "response",
        "machine_action": trace.get("entry_mechanistic_action"),
        "provider_called": trace.get("provider_called"),
        "response_received": any(bool(trace.get(k)) for k in
            ("entry_ai_raw_risk_verdict", "entry_ai_raw_risk_codes", "provider_response_id")),
        "result_source": trace.get("result_source"),
        "semantic_status": trace.get("semantic_validation_status"),
        "quality_status": trace.get("decision_quality_contract_status"),
        "source_body_sha256": digest(trace)}


def projected_response_record(row):
    """The frozen v9 producer admitted actual provider-called ENTER rows only.

    Preserve that provenance explicitly. This cannot establish a missing machine
    observation or recover any request hash absent from the historical row.
    """
    raw = row.get("raw_response") or {}
    trace = {**row, **(row.get("natural_contract_evidence") or {}),
        "decision_trace_id": row.get("evaluation_key"), "provider_called": True,
        "entry_mechanistic_action": "ENTER_NOW",
        "entry_ai_raw_risk_verdict": raw.get("risk_verdict"),
        "entry_ai_raw_risk_codes": raw.get("risk_codes")}
    return {**response_record(trace), "provenance_basis": "sealed_v9_actual_provider_filter_not_machine_anchor"}


def ledger(machines, responses, rows=(), *, scope="all", stage_keys=()):
    """Mutually exclusive reasons over records; exact attempts are separate.

    Machine anchors and response traces are different populations. Joining a
    response to an anchor requires an exact observation SHA, attempt, scope and
    bundle. Missing anchors never disappear and never count as machine misses.
    """
    records, duplicates, conflicts = {}, 0, set()
    for source in [*machines, *responses]:
        if not selected(source, scope):
            continue
        kind = source.get("record_kind")
        native = source.get("machine_observation_sha256") if kind == "machine" else source.get("decision_trace_id")
        key = str(kind) + ":" + str(native or "missing:" + digest(source))
        if key in records:
            if records[key] != source:
                conflicts.add(key)
            else:
                duplicates += 1
        records[key] = source
    by_trace = {r.get("evaluation_key"): r for r in rows}
    stage_keys = set(stage_keys)
    anchors = {r.get("machine_observation_sha256"): r for k, r in records.items()
               if r.get("record_kind") == "machine" and k not in conflicts and r.get("source_identity_valid") is not False}
    links, linked_anchors, reasons, stages, details = [], set(), Counter(), defaultdict(list), []
    for key, source in sorted(records.items()):
        if source.get("record_kind") != "response":
            continue
        anchor = anchors.get(source.get("machine_observation_sha256"))
        exact = bool(anchor and all(source.get(k) is not None and identity_equal(k, source[k], anchor.get(k))
            for k in ("evaluation_attempt_id", "stock_code", "effective_venue", "session_bucket", "machine_bundle_sha256")))
        if exact and key not in conflicts:
            links.append(dict(response=key, machine="machine:" + source["machine_observation_sha256"]))
            linked_anchors.add(source["machine_observation_sha256"])
    for key, source in sorted(records.items()):
        kind = source.get("record_kind")
        row = by_trace.get(source.get("decision_trace_id")) or {}
        axes = []
        if kind == "machine":
            stages["machine_observed"].append(key)
            if source.get("machine_action") == "ENTER_NOW":
                stages["machine_enter"].append(key)
            reason = ("not_called_by_machine" if source.get("machine_action") in {"BLOCK", "RECHECK"}
                      else "response_linked" if source.get("machine_observation_sha256") in linked_anchors
                      else "source_gap")
        else:
            if source.get("provider_called") is True:
                stages["provider_attempted"].append(key)
            if source.get("response_received") is True:
                stages["response_received"].append(key)
            semantic = source.get("semantic_status") == "pass" and source.get("quality_status") == "pass"
            if semantic:
                stages["semantic_valid"].append(key)
            stage_ok = source.get("decision_trace_id") in stage_keys and key not in conflicts and partition(source) != "unknown"
            if stage_ok:
                stages["stage_outcome_eligible"].append(key)
            if row.get("owner_replay"):
                stages["owner_replay_present"].append(key)
            axes = [r for r in (row.get("exclusion_reason"), row.get("entry_economic_source_blocker")) if r]
            if source.get("provider_called") is not True:
                reason = "provider_attempt_not_observed"
            elif source.get("response_received") is not True:
                reason = "transport_invalid" if source.get("result_source") in {"timeout", "transport_error", "error"} else "source_gap"
            elif not semantic:
                reason = "semantic_invalid"
            elif row.get("source_label_identity_reasons"):
                reason = "source_gap"
            elif stage_ok:
                reason = "stage_comparable"
            elif str(row.get("entry_economic_source_status")) == "unsupported_scope":
                reason = "unsupported_scope"
            elif (row.get("ai_stage_path") or {}).get("label_source_quality_status") == "pending_future_window":
                reason = "label_pending"
            else:
                reason = "source_gap"
        if key in conflicts or partition(source) == "unknown" or source.get("source_identity_valid") is False:
            reason = "source_gap"
            axes.append("exact_record_conflict" if key in conflicts else "machine_source_hash_invalid"
                        if source.get("source_identity_valid") is False else "stock_identity_missing")
        reasons[reason] += 1
        details.append(dict(key=key, attempt=source.get("evaluation_attempt_id"),
            primary_reason=reason, secondary_reasons=sorted(set(axes))))
    return dict(schema=CONTRACT, partition=scope, record_count=len(records), duplicate_count=duplicates,
        **DIAGNOSTIC_AUTHORITY,
        conflicting_keys=sorted(conflicts), primary_counts=dict(reasons), records=details,
        stages={k: dict(count=len(v), keys=v, sha256=digest(v)) for k, v in sorted(stages.items())},
        exact_links=links, missing_stage_keys=sorted(stage_keys - set(by_trace)),
        economics_authority="none_source_census", runtime_effect=False)


def time_seconds(value):
    if isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value):
        return float(value)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
            return parsed.timestamp() if parsed.tzinfo else None
        except ValueError:
            pass
    return None


def caution_lifecycle(rows):
    """Only exact native opportunity and generation; absence is not a loss."""
    from src.engine.scalping.postclose_entry_validation import opportunity_identity
    groups, invalid = defaultdict(list), []
    for row in rows:
        try:
            key = digest(opportunity_identity(row))
            clock = time_seconds(row.get("decision_ts"))
            if clock is None:
                raise ValueError("clock_missing")
            parent_hash = row.get("parent_auxiliary_soft_policy_sha256")
            if "parent_auxiliary_soft_policy" in row:
                parent = row["parent_auxiliary_soft_policy"]
                if parent is None and parent_hash in (None, digest(None)):
                    parent_hash = "explicit_no_soft_override:" + digest(None)
                elif parent_hash != digest(parent):
                    raise ValueError("parent_policy_hash_invalid")
            generation = (row.get("machine_bundle_sha256"), row.get("issued_prompt_sha256"), parent_hash)
            if not all(generation):
                raise ValueError("generation_missing")
            groups[(key, generation)].append((clock, row))
        except (ValueError, TypeError):
            invalid.append(row.get("evaluation_key"))
    results = []
    for (opportunity, generation), entries in sorted(groups.items()):
        entries.sort(key=lambda x: (x[0], str(x[1].get("evaluation_key"))))
        for index, (clock, row) in enumerate(entries):
            if row.get("incumbent_verdict") != "CAUTION":
                continue
            following = [(t, r) for t, r in entries[index+1:] if t > clock]
            next_row = following[0][1] if following else {}
            results.append(dict(trace=row.get("evaluation_key"), opportunity=opportunity,
                next_trace=next_row.get("evaluation_key"), next_verdict=next_row.get("incumbent_verdict"),
                status="subsequent_response_observed" if following else "followup_not_observed",
                next_response_contract=deepcopy(next_row.get("natural_contract_evidence")),
                terminal_status="not_proven_by_response", realized_net_profit=None))
    return dict(rows=results, identity_excluded_keys=sorted(invalid, key=str),
                new_prompt_status="not_evaluated_new_prompt_response_absent")
