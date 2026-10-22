"""Pure, advisory postclose projection, as-of joins and paired statistics.

No runtime evaluator, provider, broker, publisher or notification transport is
called here. Missing identities, listing metadata and outcomes remain missing.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import hashlib
import json
import math
import random
import sqlite3
import tempfile
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.market_panic_breadth_collector import (
    market_weakness_observation_contract_errors,
)
from src.engine.risk.market_weakness_state import advance_market_latch
from src.engine.risk.market_weakness_threshold_policy import observation_thresholds

KST = ZoneInfo("Asia/Seoul")
VERSION = "main_market_weakness_research_v1"
REPAIR_VERSION = "effective_registry_confirmed_cohort_v3"
LABEL = dict(
    target_net_pct=0.4, stop_net_pct=-3.0, cost_rate=0.0023, horizon_seconds=1800
)
AUTH = dict(
    decision_authority="postclose_research_advisory_only",
    runtime_effect=False,
    allowed_runtime_apply=False,
    actual_order_submitted=False,
    broker_order_forbidden=True,
)
FEATURES = ("volume_ratio_60s", "drawdown_5m_pct")
DELAYS = (0, 60, 180)


class ResearchBudgetExceeded(RuntimeError):
    pass


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def seal(value):
    value = {k: v for k, v in value.items() if k != "artifact_content_sha256"}
    return dict(value, artifact_content_sha256=digest(value))


def number(value):
    if isinstance(value, bool):
        return None
    try:
        n = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return n if math.isfinite(n) else None


def timestamp(value):
    """Research timestamps require an explicit offset; never guess naive KST."""
    try:
        t = datetime.fromisoformat(str(value))
        return t.astimezone(KST) if t.tzinfo is not None else None
    except (ValueError, TypeError, OverflowError):
        return None


def scope_key(row):
    contract = row.get("cohort_contract")
    if isinstance(contract, dict) and contract.get("verified") is True:
        return digest(
            dict(
                contract=contract,
                symbol=row.get("symbol"),
                listing_market=row.get("listing_market"),
                session=row.get("session"),
                route=row.get("route"),
                policy_scope=row.get("policy_scope"),
                decision_origin=row.get("decision_origin"),
                classification_kind=row.get("classification_kind"),
                outcome_kind=row.get("outcome_kind"),
                label_contract=LABEL,
                auxiliary_binding=row.get("auxiliary_binding"),
                **(
                    {
                        "effective_auxiliary_verified": row.get(
                            "auxiliary_binding_status"
                        )
                        == "verified"
                    }
                    if row.get("auxiliary_registry_declared")
                    else {}
                ),
            )
        )
    return digest(
        {
            k: row.get(k)
            for k in (
                "symbol",
                "listing_market",
                "session",
                "route",
                "machine_hash",
                "auxiliary_hash",
                "decision_origin",
                "classification_kind",
                "outcome_kind",
                "policy_scope",
                "scope_parent_machine_payload_sha256",
            )
        }
    )


def native_digest(value):
    """The capture writer hashes sanitized UTF-8 JSON, not research ASCII JSON."""
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode()
    ).hexdigest()


def project_native_observation(raw, source_date):
    if raw.get("schema") != "mechanistic_entry_observation_v1":
        return None, "not_native_observation"
    body = {k: v for k, v in raw.items() if k != "machine_observation_sha256"}
    context, source, receipt = (
        raw.get("label_context") or {},
        raw.get("source") or {},
        raw.get("runtime_consumption") or {},
    )
    native = receipt.get("continuous_reversal") or {}
    assessment, payload = (
        source.get("assessment") or {},
        source.get("exact_payload") or {},
    )
    captured = timestamp(raw.get("captured_at"))
    symbol, attempt = context.get("stock_code"), context.get("evaluation_attempt_id")
    if not (
        captured
        and captured.date().isoformat() == source_date
        and symbol
        and attempt
        and type(raw.get("redacted")) is bool
        and raw.get("provider_called") is False
        and all(raw.get(k) == v for k, v in AUTH.items() if k != "decision_authority")
        and raw.get("machine_observation_sha256") == native_digest(body)
        and payload.get("stock_code") == symbol
        and payload.get("evaluation_attempt_id") == attempt
        and native.get("exact_payload_sha256") == native_digest(payload)
        and native.get("assessment_sha256") == native_digest(assessment)
        and native.get("bundle_sha256")
        == receipt.get("bundle_sha256")
        == raw.get("bundle_sha256")
        and native.get("pid") == receipt.get("pid")
        and native.get("process_start_ticks") == receipt.get("process_start_ticks")
        and native.get("captured_at") == raw.get("captured_at")
    ):
        return None, "native_observation_binding_invalid"
    # Capture-wide redaction includes nonessential signal_token. Only consume
    # independently hashed fields needed for this projection; never reconstruct
    # a hidden field or treat the sanitized request as an eligible AI input.
    required_text = [
        symbol,
        attempt,
        native.get("bundle_sha256"),
        native.get("process_start_ticks"),
        assessment.get("action"),
    ]
    if any(not isinstance(v, str) or not v or "[REDACTED" in v for v in required_text):
        return None, "native_required_field_redacted_or_missing"
    if type(native.get("pid")) is not int or native["pid"] <= 0:
        return None, "native_pid_invalid"
    event = assessment.get("event")
    if not event:
        if (
            assessment.get("action") == "BLOCK"
            and assessment.get("reason") == "no_current_operating_signal"
        ):
            event = None
        else:
            return None, "native_event_missing"
    else:
        at, epoch = timestamp(event.get("at")), number(event.get("epoch"))
        clock, observed = number(native.get("snapshot_read_at")), number(
            payload.get("entry_machine_input_as_of")
        )
        event_text = [event.get(k) for k in ("event_id", "symbol", "session", "venue")]
        if any(not isinstance(v, str) or not v or "[REDACTED" in v for v in event_text):
            return None, "native_event_required_field_redacted_or_missing"
        if not (
            at
            and at.date().isoformat() == source_date
            and epoch is not None
            and abs(at.timestamp() - epoch) < 0.001
            and event.get("symbol") == symbol
            and native.get("event_id")
            == assessment.get("event_id")
            == event.get("event_id")
            and clock is not None
            and observed is not None
            and observed <= clock <= captured.timestamp()
            and 0 <= clock - epoch <= 5
            and number(event.get("entry_ask")) is not None
            and number(event.get("entry_ask")) > 0
        ):
            return None, "native_event_scope_or_clock_invalid"
        event = {
            k: event.get(k)
            for k in (
                "at",
                "epoch",
                "symbol",
                "event_id",
                "session",
                "venue",
                "source_item",
                "native_epoch",
                "native_sequence",
                "entry_ask",
                "canonical_opportunity_id",
                *FEATURES,
            )
        }
    native = {
        k: native.get(k)
        for k in (
            "bundle_sha256",
            "pid",
            "process_start_ticks",
            "captured_at",
            "event_id",
            "exact_payload_sha256",
            "assessment_sha256",
            "machine_component_sha256",
            "auxiliary_component_sha256",
            "family_sha256",
            "snapshot_read_at",
        )
    }
    request_binding = {
        k: digest((source.get("auxiliary_request") or {}).get(k))
        for k in ("input", "prompt", "response_schema")
    }
    request_verified = all(
        request_binding[k] == receipt.get("continuous_reversal", {}).get(v)
        for k, v in (
            ("input", "input_sha256"),
            ("prompt", "prompt_sha256"),
            ("response_schema", "response_schema_sha256"),
        )
    )
    return (
        dict(
            observation_sha256=raw["machine_observation_sha256"],
            native_receipt=native,
            symbol=symbol,
            evaluation_attempt_id=attempt,
            captured_at=raw["captured_at"],
            event=event,
            action=assessment.get("action"),
            canonical_opportunity_id=assessment.get("opportunity_key")
            or assessment.get("canonical_opportunity_id")
            or (event or {}).get("canonical_opportunity_id"),
            cell_key=assessment.get("cell_key"),
            evaluation_role=raw.get("evaluation_role"),
            request_binding=request_binding,
            request_binding_verified=request_verified,
            auxiliary_registry_sha256=assessment.get("auxiliary_registry_sha256"),
            effective_auxiliary_binding=assessment.get("auxiliary_binding"),
            auxiliary_registry_declared=bool(
                assessment.get("auxiliary_registry_sha256")
                or assessment.get("auxiliary_overlay_sha256")
                or (assessment.get("auxiliary_binding") or {}).get("registry_sha256")
            ),
        ),
        None,
    )


def bind_native(row, observation):
    expected = row.get("native_receipt") or {}
    native = observation["native_receipt"]
    fields = (
        "bundle_sha256",
        "pid",
        "process_start_ticks",
        "captured_at",
        "event_id",
        "exact_payload_sha256",
        "assessment_sha256",
    )
    decision = timestamp(row.get("decision_ts"))
    if (
        row.get("evaluation_attempt_id") != observation["evaluation_attempt_id"]
        or row.get("symbol") != observation["symbol"]
        or not decision
        or timestamp(observation["captured_at"]) > decision
        or any(
            (expected.get(k) is None and k != "event_id")
            or expected.get(k) != native.get(k)
            for k in fields
        )
        or any(
            expected.get(k) != native.get(k)
            for k in (
                "machine_component_sha256",
                "auxiliary_component_sha256",
                "family_sha256",
                "snapshot_read_at",
            )
        )
        or (row.get("machine_hash") and row["machine_hash"] != native["bundle_sha256"])
        or (
            row.get("entry_ask") is not None
            and observation.get("event")
            and row["entry_ask"] != number(observation["event"].get("entry_ask"))
        )
        or (
            row.get("machine_observation_sha256")
            and row["machine_observation_sha256"] != observation["observation_sha256"]
        )
    ):
        row["native_binding_status"] = "native_trace_binding_mismatch"
        return
    event = observation.get("event")
    row.update(
        native_binding_status="verified",
        native_binding_ref=observation.get("source_ref"),
        native_policy_ref=observation.get("policy_source_ref"),
        machine_hash=native["bundle_sha256"],
        captured_machine_action=observation["action"],
    )
    if row.get("machine_action") is None:
        row["machine_action"] = observation["action"]
    if observation.get("evaluation_role") == "probe_observation":
        row["decision_origin"] = "probe_observation"
    if not event:
        row["outcome_reason"] = "no_current_operating_signal"
        return
    canonical = observation.get("canonical_opportunity_id")
    row.update(
        event_id=event["event_id"],
        machine_confirmed_at=event["at"],
        entry_ask=number(event["entry_ask"]),
        features={k: number(event.get(k)) for k in FEATURES},
        session=event.get("session"),
        route=event.get("venue"),
        source_item=event.get("source_item"),
        native_epoch=event.get("native_epoch"),
        native_sequence=event.get("native_sequence"),
    )
    if canonical:
        row.update(
            opportunity_id=canonical,
            canonical_alias=event.get("canonical_opportunity_id") or canonical,
            identity_grade="canonical",
        )
    for key in (
        "cohort_contract",
        "scope_parent_machine_payload_sha256",
        "policy_scope",
        "machine_axes",
        "auxiliary_binding",
    ):
        if key in observation:
            row[key] = observation[key]
    binding = observation.get("auxiliary_binding")
    if binding:
        row["original_auxiliary_component_sha256"] = row.get("auxiliary_hash")
        if (
            observation.get("request_binding_verified") is True
            and row.get("auxiliary_hash") == native.get("auxiliary_component_sha256")
            and (
                not observation.get("auxiliary_registry_declared")
                or (
                    observation.get("effective_auxiliary_status") == "verified"
                    and (
                        row.get("auxiliary_verdict") in {"not_called", "not_evaluated"}
                        or row.get("auxiliary_response_contract_verified") is True
                    )
                )
            )
            and (
                row.get("auxiliary_verdict") in {"not_called", "not_evaluated"}
                or row.get("auxiliary_version") == binding.get("prompt_version")
            )
        ):
            row["auxiliary_hash"] = digest(binding)
            row["auxiliary_binding_status"] = "verified"
        else:
            row["auxiliary_binding_status"] = "request_or_component_binding_unverified"
        if observation.get("auxiliary_registry_declared"):
            row["auxiliary_registry_declared"] = True
            row["auxiliary_registry_sha256"] = observation["auxiliary_registry_sha256"]
            row["auxiliary_binding_reason"] = observation.get(
                "effective_auxiliary_reason"
            ) or (
                (
                    "auxiliary_trace_version_mismatch"
                    if row.get("auxiliary_version") != binding.get("prompt_version")
                    else "auxiliary_response_or_component_unverified"
                )
                if row["auxiliary_binding_status"] != "verified"
                else None
            )


def project_trace(raw, source_date, listing_market=None):
    """Project actual ai_decision_trace_v1, including pre-provider non-entry."""
    if (
        raw.get("schema") != "ai_decision_trace_v1"
        or raw.get("decision_stage") != "entry_screen"
    ):
        return None, "not_entry_trace"
    at = timestamp(raw.get("decision_ts"))
    symbol = raw.get("stock_code")
    native = raw.get("continuous_reversal_consumption")
    native = native if isinstance(native, dict) else {}
    assessment = raw.get("entry_mechanistic_policy_decision")
    assessment = assessment if isinstance(assessment, dict) else {}
    event = assessment.get("event")
    event = event if isinstance(event, dict) else {}
    canonical = (
        assessment.get("canonical_opportunity_id")
        or native.get("canonical_opportunity_id")
        or event.get("canonical_opportunity_id")
    )
    trace_id, attempt = raw.get("decision_trace_id"), raw.get("evaluation_attempt_id")
    stage = raw.get("source_event_stage")
    if not (
        at
        and at.date().isoformat() == source_date
        and isinstance(symbol, str)
        and len(symbol) == 6
        and symbol.isdigit()
        and trace_id
        and attempt
        and stage
    ):
        return None, "trace_identity_or_time_invalid"
    identity = str(canonical) if canonical else digest([trace_id, attempt, stage])
    verdict = raw.get("entry_ai_risk_verdict")
    called = raw.get("provider_called") is True
    valid_ai = bool(
        called
        and raw.get("decision_evaluation_status") == "evaluated"
        and raw.get("result_source") in {"live", "prior_valid"}
        and raw.get("prompt_version")
        and (
            raw.get("entry_ai_component_sha256")
            or native.get("auxiliary_component_sha256")
        )
    )
    if not valid_ai:
        verdict = "not_called" if not called else "not_evaluated"
    elif verdict not in {"PASS", "VETO", "CAUTION", "INSUFFICIENT"}:
        verdict = "not_evaluated"
    features = {k: number(event.get(k)) for k in FEATURES}
    ask = number(event.get("entry_ask"))
    effective = raw.get("entry_ai_effective_assessment")
    malformed_effective = effective is not None and not isinstance(effective, dict)
    effective = effective if isinstance(effective, dict) else {}
    row = dict(
        opportunity_id=identity,
        identity_grade="canonical" if canonical else "trace_only",
        decision_trace_id=trace_id,
        evaluation_attempt_id=attempt,
        source_event_stage=stage,
        source_date=source_date,
        decision_ts=at.isoformat(),
        time_precision="exact",
        machine_confirmed_at=event.get("at"),
        auxiliary_completed_at=raw.get("response_completed_at"),
        submit_at=None,
        symbol=symbol,
        listing_market=listing_market,
        session=raw.get("session_bucket"),
        route=raw.get("market_data_route"),
        machine_hash=raw.get("machine_bundle_sha256"),
        auxiliary_hash=raw.get("entry_ai_component_sha256")
        or native.get("auxiliary_component_sha256"),
        auxiliary_version=raw.get("prompt_version"),
        auxiliary_registry_declared=str(raw.get("prompt_version", "")).startswith(
            "main_auxiliary_prompt_registry_"
        ),
        auxiliary_response_contract_verified=(
            raw.get("entry_auxiliary_response_contract_valid") is True
            and raw.get("entry_auxiliary_response_contract_errors") == []
        ),
        auxiliary_execution_status=(
            "rejected"
            if (
                raw.get("entry_ai_contract_valid") is False
                or raw.get("entry_post_response_execution_valid") is False
                or effective.get("contract_valid") is False
            )
            else (
                "verified"
                if raw.get("entry_ai_contract_valid") is True
                and not malformed_effective
                else "unverified"
            )
        ),
        auxiliary_execution_reasons=list(raw.get("entry_ai_contract_errors") or [])[:8],
        machine_action=raw.get("entry_mechanistic_action"),
        auxiliary_verdict=verdict,
        event_id=native.get("event_id") or assessment.get("event_id"),
        native_receipt=native,
        machine_observation_sha256=raw.get("machine_observation_sha256"),
        entry_ask=ask,
        features=features,
        decision_origin="natural_decision",
        outcome="U",
        outcome_reason="exact_label_binding_missing",
        outcome_kind="counterfactual_price_path",
        fill_kind="unobserved",
        cost_status="configured_label_cost",
        classification_time_basis=(
            "auxiliary_completion"
            if timestamp(raw.get("response_completed_at"))
            else "recorded_decision_proxy"
        ),
        **AUTH,
    )
    return row, None


def project_replay(record, event, source_date, parent_hash, listing_market=None):
    at = timestamp(event.get("at"))
    epoch = number(event.get("epoch"))
    ask = number(event.get("entry_ask"))
    if not (
        at
        and epoch is not None
        and abs(at.timestamp() - epoch) < 0.001
        and at.date().isoformat() == source_date
        and record.get("day") == source_date
        and event.get("symbol") == record.get("symbol")
        and record.get("opportunity_key")
        and record.get("native_alias") == event.get("canonical_opportunity_id")
    ):
        return None, "replay_identity_or_time_invalid"
    row = dict(
        opportunity_id=record["opportunity_key"],
        canonical_alias=record["native_alias"],
        identity_grade="canonical",
        policy_scope=record.get("scope"),
        source_date=source_date,
        decision_ts=at.isoformat(),
        time_precision="exact",
        machine_confirmed_at=at.isoformat(),
        auxiliary_completed_at=None,
        submit_at=None,
        symbol=event["symbol"],
        listing_market=listing_market,
        session=event.get("session"),
        route=event.get("venue"),
        machine_hash=parent_hash,
        auxiliary_hash=None,
        auxiliary_version=None,
        machine_action="ENTER_NOW",
        auxiliary_verdict="not_called",
        event_id=event.get("event_id"),
        source_item=event.get("source_item"),
        native_epoch=event.get("native_epoch"),
        native_sequence=event.get("native_sequence"),
        entry_ask=ask,
        features={k: number(event.get(k)) for k in FEATURES},
        decision_origin="confirmation_replay",
        outcome_kind="counterfactual_price_path",
        fill_kind="unobserved",
        cost_status="configured_label_cost",
        **AUTH,
    )
    row["outcome"], row["outcome_reason"] = label_value(
        record.get("outcome"), ask, LABEL
    )
    return row, None


def label_value(label, ask, contract):
    if contract != LABEL or ask is None or ask <= 0 or not isinstance(label, dict):
        return "U", "label_contract_or_actual_ask_missing"
    status = label.get("status")
    if status == "WIN":
        delay = number(label.get("delay_sec"))
        if delay is None or not 0 <= delay <= 1800:
            return "U", "target_time_unverified"
        return "W", None
    if status in {"FAIL_STOP", "FAIL_TIMEOUT"}:
        return "F", None
    return "U", label.get("reason") or "outcome_unresolved"


class ObservationIndex:
    """Validate the retained day once and search only the original 300-second window."""

    def __init__(self, observations):
        entries = []
        for o in observations:
            at = timestamp(o.get("as_of"))
            if at and not market_weakness_observation_contract_errors(o):
                entries.append((at, str(o["observation_id"]), o))
        self.entries = sorted(entries, key=lambda item: (item[0], item[1]))
        self.times = [entry[0] for entry in self.entries]

    def __len__(self):
        return len(self.entries)

    def window(self, at):
        low = bisect_left(self.times, at - timedelta(seconds=300))
        high = bisect_right(self.times, at)
        return (entry[2] for entry in self.entries[low:high])


def join_snapshot(row, observations, *, delay=0, basis="raw_market_snapshot"):
    """No future source or availability. Listing market and execution are separate."""
    at = timestamp(
        row.get("classification_at")
        or row.get("auxiliary_completed_at")
        or row.get("decision_ts")
    )
    market = row.get("listing_market")
    if not (
        at
        and market in {"KOSPI", "KOSDAQ"}
        and row.get("machine_hash")
        and row.get("session")
        and row.get("route")
    ):
        return dict(grade="U", reason="scope_or_listing_market_missing")
    if row.get("time_precision") == "minute":
        at = at.replace(second=0, microsecond=0)
    candidates = []
    index = (
        observations
        if isinstance(observations, ObservationIndex)
        else ObservationIndex(observations)
    )
    for o in index.window(at):
        t = timestamp(o.get("as_of"))
        if not t or t.date() != at.date():
            continue
        available = timestamp(o.get("observed_available_at"))
        available = max(t, available) if available else t + timedelta(seconds=delay)
        if available > at or not 0 <= (at - t).total_seconds() <= 300:
            continue
        known_delay = number(o.get("observed_source_delay_sec"))
        if known_delay is not None and known_delay > 180:
            continue
        candidates.append((t, available, o))
    if not candidates:
        return dict(grade="U", reason="source_unavailable_stale_or_future")
    t, available, o = max(candidates, key=lambda p: (p[0], str(p[2]["observation_id"])))
    raw = o["raw_state"]
    affected, recovered = o.get("affected_markets", []), o.get(
        "recovery_evidence_markets", []
    )
    state = (
        "WEAKNESS"
        if market in affected
        else ("RECOVERY" if market in recovered else "NEAR_WEAKNESS_BOUNDARY")
    )
    if raw == "UNKNOWN":
        state = "UNKNOWN"
    latch_basis = None
    if basis == "confirmed_latch":
        observed = o.get("observed_latch_active", {})
        if market in observed and o.get("availability_receipt_verified"):
            active, latch_basis = observed[market], "observed_confirmed_latch"
        else:
            active = (o.get("reconstructed_active") or {}).get(market)
            latch_basis = "reconstructed_confirmed_latch"
        if raw == "UNKNOWN" or o.get("reconstructed_health") is False or active is None:
            state = "UNKNOWN"
        elif active is True:
            state = "WEAKNESS"
        else:
            state = "RECOVERY" if market in recovered else "NEAR_WEAKNESS_BOUNDARY"
    grade = (
        "C"
        if row.get("time_precision") == "minute"
        else (
            "A"
            if o.get("availability_receipt_verified") is True
            and timestamp(o.get("observed_available_at")) is not None
            else "B"
        )
    )
    return dict(
        grade=grade,
        state=state,
        observation_id=o["observation_id"],
        as_of=t.isoformat(),
        available_at=available.isoformat(),
        availability_assumed=grade != "A",
        age_sec=(at - t).total_seconds(),
        index_change_pct=number(
            (o.get("evidence", {}).get("market_index_change_pct") or {}).get(market)
        ),
        episode_id=o.get("reconstructed_episode_ids", {}).get(market)
        or o["observation_id"],
        reconstructed_active=o.get("reconstructed_active", {}).get(market),
        policy_hash=(o.get("hysteresis_policy") or {}).get("policy_hash"),
        classification_kind=basis,
        latch_basis=latch_basis,
        legacy_research_metadata=(o.get("response_research_contract") or {}).get(
            "status"
        )
        != "source_only_observation_no_execution_bridge",
    )


def reconstruct_latches(observations):
    """Research reconstruction only; source policy changes break the lineage."""
    states, previous_key, previous_at, episode, seen = {}, None, None, {}, set()
    result = []
    for original in sorted(
        observations,
        key=lambda o: timestamp(o.get("as_of")) or datetime.min.replace(tzinfo=KST),
    ):
        o = dict(original)
        at = timestamp(o.get("as_of"))
        if not at or market_weakness_observation_contract_errors(o):
            continue
        if o["observation_id"] in seen:
            continue
        seen.add(o["observation_id"])
        activation, release, spacing = observation_thresholds(o)
        key = (
            o["target_date"],
            (o.get("hysteresis_policy") or {}).get("policy_hash"),
            activation,
            release,
        )
        if key != previous_key or (
            previous_at and (at - previous_at).total_seconds() > 300
        ):
            states, previous_at, episode = {}, None, {}
        if o.get("raw_state") == "UNKNOWN":
            states, episode = {}, {}
        if previous_at is None or (at - previous_at).total_seconds() >= spacing:
            for m in ("KOSPI", "KOSDAQ"):
                classification = (
                    "unknown"
                    if o.get("raw_state") == "UNKNOWN"
                    else (
                        "weak"
                        if m in o.get("affected_markets", [])
                        else (
                            "recovery"
                            if m in o.get("recovery_evidence_markets", [])
                            else "neutral"
                        )
                    )
                )
                before = states.get(m, {})
                if classification == "unknown":
                    # Missing acceptance history cannot prove continuity of a live latch.
                    states[m] = {}
                    episode.pop(m, None)
                    continue
                states[m] = advance_market_latch(
                    before, classification, activation=activation, release=release
                )
                if states[m].get("active") and not before.get("active"):
                    episode[m] = digest([key, m, o["observation_id"]])
                elif not states[m].get("active"):
                    episode.pop(m, None)
            previous_at = at
        o["reconstructed_active"] = {
            m: states.get(m, {}).get("active", False) for m in ("KOSPI", "KOSDAQ")
        }
        o["reconstructed_episode_ids"] = dict(episode)
        o["reconstructed_health"] = o.get("raw_state") != "UNKNOWN"
        result.append(o)
        previous_key = key
    return result


def attach_joins(row, observations):
    row = dict(
        row,
        joins={
            str(d): join_snapshot(row, observations, delay=d, basis="confirmed_latch")
            for d in DELAYS
        },
        raw_diagnostic_join=join_snapshot(row, observations),
        classification_kind="confirmed_latch",
    )
    row["original_scope_key"] = scope_key(
        dict(row, classification_kind="raw_market_snapshot", cohort_contract=None)
    )
    row["scope_key"] = scope_key(row)
    return row


def quantile(histogram, fraction):
    pairs = sorted((float(k), v) for k, v in histogram.items())
    count = sum(v for _, v in pairs)
    if not count:
        return None
    rank, passed = max(1, math.ceil(count * fraction)), 0
    for value, n in pairs:
        passed += n
        if passed >= rank:
            return value


def machine_capability(summary):
    axes = [
        a
        for a in summary.get("machine_axes", [])
        if a.get("verified") is True
        and a.get("role") in {"baseline_prior", "bounded_tunable"}
        and a.get("axis") in FEATURES
        and a.get("operator") in {"lt", "le", "gt", "ge"}
        and number(a.get("before")) is not None
    ]
    if not axes:
        return "role_unverified"
    filters = [a for a in axes if not a.get("changes_confirmation")]
    if not filters:
        return "confirmation_replay_unavailable"
    hist = summary.get("feature_histograms", {})
    features_available = False
    for axis in filters:
        for q in (0.25, 0.5, 0.75):
            after = quantile(hist.get(axis["axis"], {}), q)
            index = quantile(hist.get("index_change_pct", {}), q)
            if after is None or index is None:
                continue
            features_available = True
            before = number(axis["before"])
            if index <= 0 and (
                (axis["operator"] in {"lt", "le"} and after < before)
                or (axis["operator"] in {"gt", "ge"} and after > before)
            ):
                return "supported"
    return "no_tightening_cutpoint" if features_available else "feature_missing"


def freeze_candidates(previous_daily, source_generation):
    """Use outcome-independent previous sealed feature histograms; no cross product."""
    scopes = {}
    for sid, summary in previous_daily.get("scopes", {}).items():
        candidates = []
        hist = summary.get("feature_histograms", {})
        axes = summary.get("machine_axes") or []
        machine_candidates = []
        for axis in axes:
            if (
                axis.get("role") not in {"baseline_prior", "bounded_tunable"}
                or axis.get("axis") not in FEATURES
                or axis.get("verified") is not True
            ):
                continue
            if axis.get("changes_confirmation"):
                continue  # Full FSM reconstruction cannot be inferred from confirmation rows.
            before = number(axis.get("before"))
            if before is None or axis.get("operator") not in {"lt", "le", "gt", "ge"}:
                continue
            for q in (0.25, 0.5, 0.75):
                after = quantile(hist.get(axis["axis"], {}), q)
                x = quantile(hist.get("index_change_pct", {}), q)
                if after is None or x is None or x > 0 or after == before:
                    continue
                # A confirmation filter supports tightening, never invented new signals.
                if (axis["operator"] in {"lt", "le"} and after > before) or (
                    axis["operator"] in {"gt", "ge"} and after < before
                ):
                    continue
                d = dict(
                    kind="machine_confirmation_filter_cf",
                    axis=axis["axis"],
                    before=before,
                    after=after,
                    unit=axis["unit"],
                    operator=axis["operator"],
                    role=axis["role"],
                    axis_contract=axis,
                    weakness_index_max_pct=x,
                    weakness_basis="confirmed_latch",
                    parent_hash=summary["scope"].get("machine_hash"),
                    policy_scope=summary.get("policy_scope"),
                    scope_parent_machine_payload_sha256=summary.get(
                        "scope_parent_machine_payload_sha256"
                    ),
                )
                d["cohort_contract"] = summary.get("cohort_contract")
                machine_candidates.append(dict(candidate_id=digest(d), definition=d))
        for feature in (
            FEATURES if summary.get("scope", {}).get("auxiliary_hash") else ()
        ):
            for q in (0.25, 0.5, 0.75):
                x = quantile(hist.get("index_change_pct", {}), q)
                y = quantile(hist.get(feature, {}), q)
                if x is None or y is None or x > 0:
                    continue
                definition = dict(
                    kind="post_auxiliary_withhold_cf",
                    weakness_basis="confirmed_latch",
                    axis=feature,
                    weakness_index_max_pct=x,
                    feature_max_exclusive=y,
                    before="no_additional_withhold",
                    after=y,
                    unit="ratio" if feature == "volume_ratio_60s" else "pct",
                    operator="lt",
                    parent_hash=summary["scope"].get("machine_hash"),
                    auxiliary_hash=summary["scope"].get("auxiliary_hash"),
                    policy_scope=summary.get("policy_scope"),
                    scope_parent_machine_payload_sha256=summary.get(
                        "scope_parent_machine_payload_sha256"
                    ),
                    auxiliary_binding=summary.get("auxiliary_binding"),
                    cohort_contract=summary.get("cohort_contract"),
                )
                if definition not in [c["definition"] for c in candidates]:
                    candidates.append(
                        dict(candidate_id=digest(definition), definition=definition)
                    )
        # Reserve half the bounded grid for each supported kind.
        candidates = (
            machine_candidates[:3] + candidates[: (3 if machine_candidates else 6)]
        )
        scopes[sid] = dict(
            scope=summary["scope"],
            candidates=candidates[:6],
            fixed_after_source_date=previous_daily["source_date"],
            seed_source_generation=source_generation,
            machine_status=(
                "supported"
                if machine_candidates
                else "numeric_adjustment_unidentifiable"
            ),
            machine_reason=(
                machine_capability(summary) if not machine_candidates else None
            ),
        )
    return seal(
        dict(
            schema=VERSION + ":fixed_candidates",
            fixed_after_source_date=previous_daily["source_date"],
            seed_source_generation=source_generation,
            scopes=scopes,
            **AUTH,
        )
    )


def selection(row, candidate, join):
    if join.get("grade") not in {"A", "B"} or row.get("identity_grade") != "canonical":
        return None
    d = candidate["definition"]
    kind = d["kind"]
    if kind not in {
        "post_auxiliary_withhold_cf",
        "machine_confirmation_filter_cf",
    }:
        # There is no full FSM/confirmation/ask replay producer. A row-local
        # verified boolean cannot establish replay lineage or new outcomes.
        return None
    if kind == "post_auxiliary_withhold_cf" and (
        row.get("auxiliary_verdict") != "PASS"
        or not row.get("auxiliary_hash")
        or row.get("auxiliary_execution_status") == "rejected"
        or (
            row.get("auxiliary_registry_declared")
            and row.get("auxiliary_execution_status") != "verified"
        )
    ):
        return None
    if (
        kind == "post_auxiliary_withhold_cf"
        and (
            row.get("auxiliary_registry_declared")
            or (
                row.get("native_binding_status") == "verified"
                and row.get("cohort_contract")
            )
        )
        and row.get("auxiliary_binding_status") != "verified"
    ):
        return None
    if (
        d.get("weakness_basis") == "confirmed_latch"
        and join.get("classification_kind") != "confirmed_latch"
    ):
        return None
    if kind == "machine_confirmation_filter_cf":
        contract = d.get("axis_contract") or {}
        if (
            row.get("machine_action") != "ENTER_NOW"
            or contract.get("verified") is not True
            or contract.get("role") not in {"baseline_prior", "bounded_tunable"}
            or contract.get("axis") != d["axis"]
        ):
            return None
    if join.get("state") != "WEAKNESS":
        return True  # An inactive overlay does not require its feature.
    value, index = number(row.get("features", {}).get(d["axis"])), number(
        join.get("index_change_pct")
    )
    if value is None or index is None:
        return None
    if kind == "machine_confirmation_filter_cf":
        if index > d["weakness_index_max_pct"]:
            return True
        operator = d.get("operator")
        after = number(d.get("after"))
        contract = d.get("axis_contract") or {}
        if (
            after is None
            or contract.get("verified") is not True
            or contract.get("role") not in {"baseline_prior", "bounded_tunable"}
            or contract.get("axis") != d["axis"]
        ):
            return None
        return {
            "lt": value < after,
            "le": value <= after,
            "gt": value > after,
            "ge": value >= after,
        }.get(operator)
    withhold = (
        join.get("state") == "WEAKNESS"
        and index <= d["weakness_index_max_pct"]
        and value < d["feature_max_exclusive"]
    )
    return not withhold


def metric(counts):
    w, f, u = (counts.get(k, 0) for k in ("W", "F", "U"))
    return dict(
        W=w, F=f, U=u, resolved=w + f, raw_win_rate=w / (w + f) if w + f else None
    )


def pair_delta(counts, *, worst_u=False):
    selected, excluded, added = (
        counts["selected"],
        counts["excluded"],
        counts.get("added", {}),
    )
    baseline = Counter(selected) + Counter(excluded)
    candidate = Counter(selected) + Counter(added)
    if worst_u:
        base_n = sum(baseline.get(k, 0) for k in ("W", "F", "U"))
        selected_n = sum(candidate.get(k, 0) for k in ("W", "F", "U"))
        if not base_n or not selected_n:
            return None
        return min(
            (candidate.get("W", 0) + x) / selected_n
            - (baseline.get("W", 0) + excluded.get("U", 0) + x) / base_n
            for x in (0, selected.get("U", 0))
        )
    else:
        b, c = metric(baseline)["raw_win_rate"], metric(candidate)["raw_win_rate"]
    return c - b if b is not None and c is not None else None


def subtract_pairs(total, part):
    return {
        field: {
            k: total.get(field, {}).get(k, 0) - part.get(field, {}).get(k, 0)
            for k in ("W", "F", "U")
        }
        for field in ("selected", "excluded", "added", "neither")
    }


def merge_pairs(pairs):
    result = dict(
        selected=Counter(), excluded=Counter(), added=Counter(), neither=Counter()
    )
    for p in pairs:
        for field in result:
            result[field].update(p.get(field, {}))
    return result


class Aggregator:
    """Consume compact rows once; retain per-day/episode counts, never AI bodies."""

    def __init__(self, candidates=None, *, scratch_root=None):
        self.candidates = candidates or {}
        self.census, self.scopes = Counter(), {}
        self.pairs = defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(
                    lambda: defaultdict(
                        lambda: dict(
                            selected=Counter(),
                            excluded=Counter(),
                            added=Counter(),
                            neither=Counter(),
                        )
                    )
                )
            )
        )
        self.historical_pairs = defaultdict(
            lambda: defaultdict(
                lambda: dict(
                    selected=Counter(),
                    excluded=Counter(),
                    added=Counter(),
                    neither=Counter(),
                )
            )
        )
        self.conflicts = set()
        self.conflict_scopes = set()
        self._temp = None
        if scratch_root is not None:
            Path(scratch_root).mkdir(parents=True, exist_ok=True)
            self._temp = tempfile.TemporaryDirectory(
                prefix="aggregate-", dir=scratch_root
            )
        self.db = sqlite3.connect(
            str(Path(self._temp.name) / "dedup.sqlite") if self._temp else ":memory:"
        )
        self.db.execute("PRAGMA cache_size=-2048")
        self.db.execute(
            "CREATE TABLE identities(identity TEXT PRIMARY KEY,scope TEXT,binding TEXT,row TEXT,conflict INTEGER)"
        )
        self._finished = False

    def close(self):
        self.db.close()
        if self._temp:
            self._temp.cleanup()

    def add(self, row):
        if self._finished:
            raise ValueError("aggregate_already_finalized")
        self.census["projected_rows"] += 1
        self.census[
            "origin_"
            + str(row.get("decision_origin"))
            + "_"
            + str(row.get("response_origin", "no_stored_auxiliary"))
        ] += 1
        self.census["attempt_machine_" + str(row.get("machine_action"))] += 1
        self.census["attempt_auxiliary_" + str(row.get("auxiliary_verdict"))] += 1
        sid = row["scope_key"]
        identity = digest([row.get("decision_origin"), row.get("opportunity_id"), sid])
        # Retry/response timestamps are attempt evidence, not new outcome units.
        binding = digest(
            {
                k: row.get(k)
                for k in (
                    "event_id",
                    "machine_confirmed_at",
                    "entry_ask",
                    "features",
                    "outcome",
                )
            }
        )
        old = self.db.execute(
            "SELECT binding,row,conflict FROM identities WHERE identity=?", (identity,)
        ).fetchone()
        if old:
            self.census["duplicate_rows"] += 1
            if old[0] != binding:
                self.conflicts.add(identity)
                self.conflict_scopes.add(sid)
                self.db.execute(
                    "UPDATE identities SET conflict=1 WHERE identity=?", (identity,)
                )
            elif not old[2]:
                first = json.loads(old[1])
                # The first actually evaluated response is deterministic and label independent.
                if first.get("auxiliary_verdict") in {
                    "not_called",
                    "not_evaluated",
                } and row.get("auxiliary_verdict") not in {
                    "not_called",
                    "not_evaluated",
                }:
                    self.db.execute(
                        "UPDATE identities SET row=? WHERE identity=?",
                        (json.dumps(row, sort_keys=True), identity),
                    )
            return
        self.db.execute(
            "INSERT INTO identities VALUES(?,?,?,?,0)",
            (identity, sid, binding, json.dumps(row, sort_keys=True)),
        )

    def finalize(self):
        if not self._finished:
            for (raw,) in self.db.execute(
                "SELECT row FROM identities WHERE conflict=0 ORDER BY identity"
            ):
                self._add(json.loads(raw))
            self.census["quarantined_conflicts"] = len(self.conflicts)
            self._finished = True

    def merge(self, aggregate):
        self.finalize()
        self.census.update(aggregate["census"])
        self.conflict_scopes.update(aggregate.get("conflict_scopes", []))
        for sid, source in aggregate["scopes"].items():
            if sid not in self.scopes:
                self.scopes[sid] = dict(
                    scope=source["scope"],
                    counts=Counter(),
                    feature_histograms=defaultdict(Counter),
                    policy_scope=source.get("policy_scope"),
                    auxiliary_binding=source.get("auxiliary_binding"),
                    cohort_contract=source.get("cohort_contract"),
                    machine_axes=source.get("machine_axes", []),
                    scope_parent_machine_payload_sha256=source.get(
                        "scope_parent_machine_payload_sha256"
                    ),
                )
            self.scopes[sid]["counts"].update(source["counts"])
            for k, h in source["feature_histograms"].items():
                self.scopes[sid]["feature_histograms"][k].update(h)
        for sid, cid, pair in aggregate.get("historical_pairs", []):
            target = self.historical_pairs[sid][cid]
            for k in target:
                target[k].update(pair.get(k, {}))
        for sid, cid, delay, cluster, pair in aggregate.get("pairs", []):
            target = self.pairs[sid][cid][delay][tuple(cluster)]
            for k in target:
                target[k].update(pair.get(k, {}))

    def export(self):
        self.finalize()
        pairs = [
            [sid, cid, delay, list(cluster), pair]
            for sid, cs in self.pairs.items()
            for cid, ds in cs.items()
            for delay, clusters in ds.items()
            for cluster, pair in clusters.items()
        ]
        return dict(
            census=dict(self.census),
            scopes=self.scopes,
            pairs=pairs,
            conflict_scopes=sorted(self.conflict_scopes),
            historical_pairs=[
                [sid, cid, pair]
                for sid, cs in self.historical_pairs.items()
                for cid, pair in cs.items()
            ],
        )

    def _add(self, row):
        sid = row["scope_key"]
        if sid not in self.scopes:
            self.scopes[sid] = dict(
                scope={
                    k: row.get(k)
                    for k in (
                        "symbol",
                        "listing_market",
                        "session",
                        "route",
                        "machine_hash",
                        "auxiliary_hash",
                        "decision_origin",
                        "classification_kind",
                        "outcome_kind",
                    )
                },
                counts=Counter(),
                feature_histograms=defaultdict(Counter),
                policy_scope=row.get("policy_scope"),
                auxiliary_binding=row.get("auxiliary_binding"),
                cohort_contract=row.get("cohort_contract"),
                machine_axes=row.get("machine_axes", []),
                scope_parent_machine_payload_sha256=row.get(
                    "scope_parent_machine_payload_sha256"
                ),
            )
        summary = self.scopes[sid]
        join = row["joins"]["0"]
        summary["counts"]["rows"] += 1
        if row.get("native_binding_status"):
            summary["counts"]["native_binding_" + row["native_binding_status"]] += 1
        if row.get("auxiliary_binding_status"):
            summary["counts"][
                "auxiliary_binding_" + row["auxiliary_binding_status"]
            ] += 1
        if row.get("auxiliary_binding_reason"):
            summary["counts"][
                "auxiliary_binding_reason_" + row["auxiliary_binding_reason"]
            ] += 1
        summary["counts"]["join_" + join["grade"]] += 1
        summary["counts"]["identity_" + str(row.get("identity_grade"))] += 1
        if join["grade"] == "U":
            summary["counts"]["join_U_reason_" + str(join.get("reason"))] += 1
        if row["outcome"] == "U":
            summary["counts"]["outcome_U_reason_" + str(row.get("outcome_reason"))] += 1
        summary["counts"]["machine_" + str(row.get("machine_action"))] += 1
        summary["counts"]["auxiliary_" + str(row.get("auxiliary_verdict"))] += 1
        if row.get("auxiliary_verdict") == "PASS" and row.get(
            "auxiliary_execution_status"
        ):
            summary["counts"]["execution_" + row["auxiliary_execution_status"]] += 1
            for reason in row.get("auxiliary_execution_reasons", []):
                summary["counts"]["execution_reason_" + str(reason)] += 1
        summary["counts"]["outcome_" + row["outcome"]] += 1
        summary["counts"]["state_" + join.get("state", "UNKNOWN")] += 1
        summary["counts"][
            "cohort_" + str(row.get("auxiliary_verdict")) + "_" + row["outcome"]
        ] += 1
        summary["counts"][
            "state_" + join.get("state", "UNKNOWN") + "_" + row["outcome"]
        ] += 1
        for delay in DELAYS:
            summary["counts"][
                "delay_" + str(delay) + "_join_" + row["joins"][str(delay)]["grade"]
            ] += 1
        if (
            join["grade"] in {"A", "B"}
            and row.get("identity_grade") == "canonical"
            and (
                not row.get("auxiliary_registry_declared")
                or row.get("auxiliary_binding_status") == "verified"
            )
        ):
            for key, value in dict(
                row.get("features", {}), index_change_pct=join.get("index_change_pct")
            ).items():
                value = number(value)
                if key in (*FEATURES, "index_change_pct") and value is not None:
                    summary["feature_histograms"][key][str(value)] += 1
        candidates = (
            self.candidates.get("scopes", {}).get(sid, {}).get("candidates", [])
        )
        if not candidates:
            return
        groups = defaultdict(list)
        for c in candidates:
            groups[c["definition"]["kind"]].append(c)
        for kind, group in groups.items():
            if (
                kind == "post_auxiliary_withhold_cf"
                and row.get("auxiliary_verdict") != "PASS"
            ):
                continue
            if (
                kind == "post_auxiliary_withhold_cf"
                and row.get("auxiliary_execution_status") == "rejected"
            ):
                summary["counts"]["existing_execution_rejected"] += 1
                continue
            if (
                kind == "post_auxiliary_withhold_cf"
                and row.get("auxiliary_registry_declared")
                and row.get("auxiliary_execution_status") != "verified"
            ):
                summary["counts"]["execution_unverified_excluded"] += 1
                continue
            decisions = {
                c["candidate_id"]: {
                    str(delay): selection(row, c, row["joins"][str(delay)])
                    for delay in DELAYS
                }
                for c in group
            }
            if any(v is None for values in decisions.values() for v in values.values()):
                summary["counts"]["candidate_common_range_gap"] += 1
                continue
            # Both supported kinds can only withhold original opportunities.
            baseline = True
            summary["counts"]["candidate_common_range"] += 1
            prospective = row["source_date"] > self.candidates.get("scopes", {}).get(
                sid, {}
            ).get("fixed_after_source_date", "9999")
            if prospective:
                summary["counts"]["prospective_common_range"] += 1
            for c in group:
                for delay in DELAYS:
                    selected = decisions[c["candidate_id"]][str(delay)]
                    field = (
                        "selected"
                        if baseline and selected
                        else (
                            "excluded"
                            if baseline
                            else "added" if selected else "neither"
                        )
                    )
                    if delay == 0:
                        self.historical_pairs[sid][c["candidate_id"]][field][
                            row["outcome"]
                        ] += 1
                    if prospective:
                        join = row["joins"][str(delay)]
                        episode = (
                            join.get("episode_id")
                            if join.get("state") == "WEAKNESS"
                            else "nonweak:" + row["source_date"]
                        )
                        self.pairs[sid][c["candidate_id"]][str(delay)][
                            (row["source_date"], episode)
                        ][field][row["outcome"]] += 1

    def diagnostics(self):
        result = {}
        for sid, summary in self.scopes.items():
            counts = summary["counts"]
            total = metric({k: counts.get("outcome_" + k, 0) for k in ("W", "F", "U")})
            passed = metric(
                {k: counts.get("cohort_PASS_" + k, 0) for k in ("W", "F", "U")}
            )
            result[sid] = dict(
                all_opportunities=total,
                auxiliary_PASS=passed,
                nonPASS_missed_W=sum(
                    counts.get("cohort_" + v + "_W", 0)
                    for v in (
                        "VETO",
                        "CAUTION",
                        "INSUFFICIENT",
                        "not_called",
                        "not_evaluated",
                    )
                ),
                PASS_remaining_F=counts.get("cohort_PASS_F", 0),
                states={
                    state: metric(
                        {
                            k: counts.get("state_" + state + "_" + k, 0)
                            for k in ("W", "F", "U")
                        }
                    )
                    for state in (
                        "WEAKNESS",
                        "RECOVERY",
                        "NEAR_WEAKNESS_BOUNDARY",
                        "UNKNOWN",
                    )
                },
            )
        return result

    def daily(self, source_date):
        self.finalize()
        return seal(
            dict(
                schema=VERSION + ":daily",
                source_date=source_date,
                scopes=self.scopes,
                diagnostic_metrics=self.diagnostics(),
                census=dict(self.census),
                conflicting_identities=sorted(self.conflicts),
                conflict_scopes=sorted(self.conflict_scopes),
                **AUTH,
            )
        )

    def comparison(self, generation, *, checkpoint=None, gate=lambda: True):
        self.finalize()
        results = []
        for sid, declared in self.candidates.get("scopes", {}).items():
            local = []
            for c in declared["candidates"]:
                if not gate():
                    raise ResearchBudgetExceeded("comparison_wall_budget")
                cached = (
                    checkpoint(sid, c["candidate_id"], None) if checkpoint else None
                )
                if cached:
                    local.append(dict(cached, generation=generation))
                    continue
                clusters = self.pairs[sid][c["candidate_id"]]["0"]
                totals = merge_pairs(clusters.values())
                baseline = Counter(totals["selected"]) + Counter(totals["excluded"])
                delta = pair_delta(totals)
                dates = sorted({day for day, _ in clusters})
                day_pairs = {
                    day: merge_pairs(p for (d, _), p in clusters.items() if d == day)
                    for day in dates
                }
                seed = digest([declared, sid, VERSION, "cluster1000"])
                rng = random.Random(seed)
                draws = []
                cluster_deltas = {pair_delta(p) for p in clusters.values()}
                if (
                    len(dates) > 1
                    and len(cluster_deltas - {None}) >= 2
                    and (
                        sum(totals["excluded"].values()) + sum(totals["added"].values())
                    )
                ):
                    for draw_index in range(1000):
                        if draw_index % 25 == 0 and not gate():
                            raise ResearchBudgetExceeded("comparison_wall_budget")
                        value = pair_delta(
                            merge_pairs(day_pairs[rng.choice(dates)] for _ in dates)
                        )
                        if value is not None:
                            draws.append(value)
                lower = sorted(draws)[49] if len(draws) == 1000 else None
                leave_dates = [
                    pair_delta(subtract_pairs(totals, p)) for p in day_pairs.values()
                ]
                leave_episodes = [
                    pair_delta(subtract_pairs(totals, p)) for p in clusters.values()
                ]
                delayed = {
                    str(d): pair_delta(
                        merge_pairs(self.pairs[sid][c["candidate_id"]][str(d)].values())
                    )
                    for d in (60, 180)
                }
                u_delta = pair_delta(totals, worst_u=True)
                changes = sum(totals["excluded"].values()) + sum(
                    totals["added"].values()
                )
                cluster_deltas = {pair_delta(p) for p in clusters.values()}
                status = "hold_observation"
                if sid in self.conflict_scopes:
                    status = "source_gap"
                elif delta is None or lower is None or len(cluster_deltas - {None}) < 2:
                    status = "uncertainty_unresolved"
                elif any(v is None or v <= 0 for v in delayed.values()):
                    status = "join_sensitive"
                elif u_delta is None or u_delta <= 0:
                    status = "outcome_sensitive"
                elif (
                    changes
                    and delta > 0
                    and lower > 0
                    and leave_dates
                    and leave_episodes
                    and all(
                        v is not None and v > 0 for v in leave_dates + leave_episodes
                    )
                ):
                    status = "eligible_advisory"
                local.append(
                    dict(
                        scope_key=sid,
                        scope=declared["scope"],
                        candidate_id=c["candidate_id"],
                        definition=c["definition"],
                        status=status,
                        baseline=metric(baseline),
                        prospective_after_source_date=declared[
                            "fixed_after_source_date"
                        ],
                        full_cumulative_descriptive_delta=pair_delta(
                            self.historical_pairs[sid][c["candidate_id"]]
                        ),
                        full_cumulative_baseline=metric(
                            Counter(
                                self.historical_pairs[sid][c["candidate_id"]][
                                    "selected"
                                ]
                            )
                            + Counter(
                                self.historical_pairs[sid][c["candidate_id"]][
                                    "excluded"
                                ]
                            )
                        ),
                        full_cumulative_candidate=metric(
                            Counter(
                                self.historical_pairs[sid][c["candidate_id"]][
                                    "selected"
                                ]
                            )
                            + Counter(
                                self.historical_pairs[sid][c["candidate_id"]]["added"]
                            )
                        ),
                        candidate=metric(
                            Counter(totals["selected"]) + Counter(totals["added"])
                        ),
                        delta_raw_win_rate=delta,
                        excluded_opportunities=sum(totals["excluded"].values()),
                        added_opportunities=sum(totals["added"].values()),
                        mask_counts={
                            name: dict(totals[field])
                            for name, field in (
                                ("K", "selected"),
                                ("R", "excluded"),
                                ("A", "added"),
                                ("N", "neither"),
                            )
                        },
                        missed_W=totals["excluded"].get("W", 0),
                        removed_F=totals["excluded"].get("F", 0),
                        source_dates=dates,
                        episode_count=sum(
                            1
                            for _, episode in clusters
                            if episode and not episode.startswith("nonweak:")
                        ),
                        bootstrap_iterations=1000,
                        bootstrap_valid_iterations=len(draws),
                        bootstrap_seed=seed,
                        empirical_lower_5pct_delta=lower,
                        statistical_95pct_guarantee=False,
                        delayed_common_range_delta=delayed,
                        worst_outcome_U_delta=u_delta,
                        leave_date_delta=leave_dates,
                        leave_episode_delta=leave_episodes,
                        join_counts=dict(self.scopes.get(sid, {}).get("counts", {})),
                        comparison_complete=True,
                        generation=generation,
                        **AUTH,
                    )
                )
                if checkpoint:
                    checkpoint(sid, c["candidate_id"], local[-1])
            winners = {}
            for kind in {r["definition"]["kind"] for r in local}:
                eligible = [
                    r
                    for r in local
                    if r["status"] == "eligible_advisory"
                    and r["definition"]["kind"] == kind
                ]
                winners[kind] = max(
                    eligible,
                    key=lambda r: (r["delta_raw_win_rate"], r["candidate_id"]),
                    default=None,
                )
            for r in local:
                winner = winners[r["definition"]["kind"]]
                r["winner_group"] = digest([sid, r["definition"]["kind"]])
                r["scope_winner"] = bool(
                    winner and r["candidate_id"] == winner["candidate_id"]
                )
            results += local
        return seal(
            dict(
                schema=VERSION + ":comparison",
                generation=generation,
                census=dict(self.census),
                scope_observations=self.scopes,
                diagnostic_metrics=self.diagnostics(),
                candidate_manifest_sha256=self.candidates.get(
                    "artifact_content_sha256"
                ),
                comparisons=results,
                candidate_count=len(results),
                capability_by_scope={
                    sid: dict(
                        machine=(
                            "supported"
                            if any(
                                r["scope_key"] == sid
                                and r["definition"]["kind"]
                                != "post_auxiliary_withhold_cf"
                                for r in results
                            )
                            else machine_capability(s)
                        ),
                        post_auxiliary=(
                            "auxiliary_not_observed"
                            if not s["counts"].get("auxiliary_PASS")
                            else (
                                "join_or_feature_missing"
                                if not s.get("feature_histograms")
                                else "supported"
                            )
                        ),
                    )
                    for sid, s in self.scopes.items()
                },
                **AUTH,
            )
        )
