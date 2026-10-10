"""Observe Sentinel's exact machine funnel; notification has no trading authority."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.notify_error_detection_admin import (
    _load_state, _load_telegram_config, _send_telegram, _write_state,
)
from src.utils.constants import PROJECT_ROOT

SCHEMA = "submission_bottleneck_monitor_v1"
KST = ZoneInfo("Asia/Seoul")
# Diagnostic persistence only. Never used by a trading policy or guard.
WINDOW_SEC = 1800
GRACE_SEC = 600
PERSIST_SEC = 900
MIN_PROMOTIONS = 10
SOURCE_WINDOW_SEC = 600
SOURCE_TAIL_BYTES = 32 * 1024 * 1024
DELAY_STAGES = frozenset({"pre_submit_delay_committed", "pre_submit_delay_quote_observed",
                          "pre_submit_delay_intent_terminal"})
DELAY_RAW_BUDGET = 32 * 1024 * 1024
DELAY_WINDOW_SEC = 600
DELAY_SUMMARY_GRACE_SEC = 150


def stamp(value):
    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed.replace(tzinfo=KST) if parsed.tzinfo is None else parsed.astimezone(KST)
    except (ValueError, TypeError):
        return None


def _recent_source_rows(path, now, *, time_field, tail_bytes=SOURCE_TAIL_BYTES,
                        window_sec=SOURCE_WINDOW_SEC, allow_adjacent_date=False):
    """Read a bounded, complete JSONL suffix; never equate a partial tail to zero gaps."""
    source = {"status": "unobservable", "tail_truncated": False,
              "window_covered": False, "recent_count": 0}
    try:
        with path.open("rb") as stream:
            before = os.fstat(stream.fileno())
            if not before.st_size:
                source["reason"] = "empty_source"
                return [], source
            start = max(0, before.st_size - tail_bytes)
            stream.seek(start)
            payload = stream.read(before.st_size - start)
            after = path.stat()
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino) or after.st_size < before.st_size:
            source["reason"] = "source_generation_changed"
            return [], source
    except OSError as exc:
        source["reason"] = ('compressed_archive_not_current_bounded_source'
                            if path.with_suffix(path.suffix + '.gz').exists() else type(exc).__name__)
        return [], source
    if start:
        payload = payload.partition(b"\n")[2]
    lines = payload.split(b"\n")
    incomplete_last_line = bool(lines[-1])
    lines.pop()  # A concurrently appended final line has no complete receipt.
    rows, first_at, malformed = [], None, 0
    for line in lines:
        try:
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError("source_row_not_object")
            at = stamp(row.get(time_field))
            if at is None or (not allow_adjacent_date and at.date() != now.date()) or at > now:
                continue
            first_at = at if first_at is None else min(first_at, at)
            if (now - at).total_seconds() <= window_sec:
                rows.append(row)
        except (ValueError, UnicodeDecodeError, TypeError):
            malformed += 1
    covered = not start or (first_at is not None and (now - first_at).total_seconds() >= window_sec)
    source.update(status="complete" if covered and not malformed and not incomplete_last_line else "partial",
                  tail_truncated=bool(start), window_covered=covered,
                  recent_count=len(rows), malformed_rows=malformed,
                  incomplete_last_line=incomplete_last_line,
                  first_read_at=first_at.isoformat() if first_at else None)
    source.update(bytes_read=len(payload), read_count=1, source_size=before.st_size,
                  source_identity=dict(device=before.st_dev, inode=before.st_ino))
    return rows, source


def _reversal_provider_lineage(data_root, now, observations, *, tail_bytes):
    """Request preparation and raw responses are facts distinct from compose."""
    request_rows, requests = _recent_source_rows(
        data_root/'ai_decision_requests'/f'ai_decision_requests_{now.date()}.jsonl',
        now, time_field='captured_at', tail_bytes=tail_bytes, window_sec=WINDOW_SEC)
    actions = {row['machine_observation_sha256']: row['source']['assessment']['action'] for row in observations}
    if 'ENTER_NOW' in actions.values() or request_rows:
        trace_rows, traces = _recent_source_rows(
            data_root/'ai_decision_trace'/f'ai_decision_trace_{now.date()}.jsonl',
            now, time_field='created_at', tail_bytes=tail_bytes, window_sec=WINDOW_SEC)
    else:
        trace_rows, traces = [], dict(status='not_required_machine_nonentry', bytes_read=0, read_count=0)
    prepared, responded, noncall, issues = set(), set(), Counter(), Counter()
    for row in request_rows:
        binding = row.get('continuous_reversal_request_binding') or {}
        key = binding.get('machine_observation_sha256')
        if key not in actions:
            continue
        if actions[key] != 'ENTER_NOW':
            issues['reversal_provider_request_after_nonentry'] += 1
        if binding.get('binding_status') != 'matched':
            issues['reversal_provider_request_hash_mismatch'] += 1
        prepared.add(key)
    for row in trace_rows:
        key = row.get('machine_observation_sha256')
        if key not in actions:
            continue
        if row.get('ai_decision_trace_id') and row.get('entry_ai_raw_risk_verdict'):
            responded.add(key)
        if actions[key] == 'ENTER_NOW' and not row.get('entry_ai_raw_risk_verdict'):
            reason = row.get('entry_ai_screen_status') or row.get('ai_screen_status') or row.get('machine_contract_error')
            if reason:
                noncall[str(reason)] += 1
    return dict(status='review_required' if issues else 'observed' if prepared or responded else 'not_observed',
        request_prepared_count=len(prepared), raw_response_observed_count=len(responded),
        enter_without_request_observed=sum(action == 'ENTER_NOW' and key not in prepared for key, action in actions.items()),
        noncall_reasons=dict(noncall), issues=dict(issues), source_windows=dict(requests=requests, traces=traces),
        provider_called_metadata_used_as_fact=False, actual_order_submitted_assessed=False)


def _auxiliary_cost_receipt_valid(row):
    cost = row.get("entry_conservative_execution_cost_pct")
    return (row.get("entry_cost_source_status") == "exact_pre_provider_replay"
            and type(cost) in (int, float) and math.isfinite(cost) and cost >= 0
            and row.get("entry_cost_evaluation_attempt_id") == row.get("evaluation_attempt_id")
            and bool(row.get("evaluation_attempt_id"))
            and row.get("entry_cost_scope") == "counterfactual_friction_no_broker_fees"
            and row.get("entry_cost_basis") == "half_spread_plus_bounded_source_age_penalty"
            and all(isinstance(row.get(name), str) and len(row[name]) == 64
                    and all(char in "0123456789abcdef" for char in row[name])
                    for name in ("entry_cost_contract_sha256", "entry_cost_replay_context_sha256")))


def _reversal_lifecycle_diagnostic(row):
    """Only exact, intact rejection evidence can classify a normal lifecycle miss."""
    receipt = row.get("continuous_reversal_rejected_claim_receipt")
    if (row.get("provider_called") is not False or row.get("actual_order_submitted") is True
            or not isinstance(receipt, dict) or receipt.get("status") != "observed"
            or receipt.get("schema") not in {"continuous_reversal_claim_source_receipt_v1",
                                             "continuous_reversal_claim_source_receipt_v2",
                                             "continuous_reversal_claim_source_receipt_v3",
                                             "continuous_reversal_claim_source_receipt_v4"}
            or not row.get("evaluation_attempt_id")
            or receipt.get("evaluation_attempt_id") != row.get("evaluation_attempt_id")
            or not row.get("machine_bundle_sha256")
            or receipt.get("machine_bundle_sha256") != row.get("machine_bundle_sha256")
            or receipt.get("validation_error") != row.get("machine_contract_error")):
        return None
    try:
        snapshot = receipt["snapshot"]
        generation = receipt["stored_generation"]
        expired_registration = False
        if (receipt['schema'] == 'continuous_reversal_claim_source_receipt_v3'
                and receipt.get('registered_claim_present') is False):
            from src.engine.scalping.reversal_source_diagnostics import verified_registration
            proof = verified_registration(dict(token=receipt['claim_token'],
                generation=receipt['claim_generation'], snapshot=receipt['supplied_snapshot'],
                backend=receipt.get('claim_backend')),
                receipt.get('source_registration_receipt'))
            if (not proof or snapshot is not None or generation is not None
                    or receipt['scope'] != proof['scope']
                    or receipt['active_generation'] != receipt['requested_family_sha256']
                    or receipt['validation_epoch'] < proof['observed_epoch']
                    or row['machine_contract_error'] != 'reversal_signal_generation_changed'
                    or receipt.get('failure_cause') != 'reversal_signal_expired'):
                return None
            snapshot, generation = proof['snapshot'], proof['generation']
            expired_registration = True
        event = snapshot[0]
        scope = receipt["scope"]
        latest = receipt["latest_native_observation"]
        at = receipt["validation_epoch"]
        observed_at = (receipt["state_observed_epoch"]
                       if receipt["schema"] != "continuous_reversal_claim_source_receipt_v1"
                       else at)
        age = at - event["epoch"]
        family = receipt["requested_family_sha256"]
        operating = receipt['schema'] == 'continuous_reversal_claim_source_receipt_v4'
        if operating:
            from src.engine.scalping.reversal_source_diagnostics import verified_registration
            from src.engine.scalping.continuous_reversal import good_quote
            proof = verified_registration(dict(token=receipt['claim_token'],
                generation=receipt['claim_generation'], snapshot=receipt['supplied_snapshot'],
                backend=receipt.get('claim_backend')), receipt.get('source_registration_receipt'))
            if (receipt.get('claim_backend') not in {'operating_v5', 'operating_v6'}
                    or receipt.get('registered_claim_present') is not True
                    or not proof or scope != proof['scope']
                    or family != receipt.get('active_generation')
                    or family != receipt.get('stored_envelope_family_sha256')
                    or generation != receipt.get('state_generation')
                    or generation != receipt.get('active_scope_execution_hash')
                    or generation != event.get('registry_generation')
                    or at < proof['observed_epoch'] or not good_quote(latest)):
                return None
        encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode()
        snapshot_sha = hashlib.sha256(encoded).hexdigest()
        token = hashlib.sha256(json.dumps([generation, event["signal_id"], snapshot],
            sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()
        trace_at = stamp(row["decision_ts"]).timestamp()
        if ((not operating and family != generation) or generation != receipt["claim_generation"]
                or (not expired_registration and snapshot_sha != receipt["snapshot_sha256"])
                or snapshot_sha != receipt["supplied_snapshot_sha256"]
                or token != receipt["claim_token"] or age != receipt["signal_age_seconds"]
                or scope[0] != row.get("stock_code") or scope[2] != event["source_item"]
                or scope[1] != "SOR" or not scope[2].endswith("_AL")
                or row.get("market_data_route") != "krx_nxt_integrated"
                or latest[9] != scope[2] or not latest[8]
                or str(latest[1]) != event["event_id"].rsplit(":", 2)[-2]
                or latest[2] < int(event["event_id"].rsplit(":", 1)[-1])
                or not receipt["price_path_segment_start"] < event["epoch"]
                or not 0 <= observed_at-at <= 5
                or not 0 <= observed_at-latest[0] <= 5
                or not 0 <= trace_at-observed_at <= 5 or not 0 <= trace_at-at <= 5):
            return None
        cause = receipt.get("failure_cause")
        if (operating and cause == row['machine_contract_error'] == 'reversal_signal_path_changed'
                and 0 <= age <= 5 and receipt.get('registered_signal_ready') is False
                and event.get('decision_phase') == 'FIRST_UPTICK'
                and event.get('branch_signals')
                and all(s.get('decision_phase') == 'FIRST_UPTICK'
                        for s in event['branch_signals'].values())
                and receipt.get('current_turn_id') is None
                and latest[0] > event['epoch'] and latest[3] < event['confirmation_price']):
            return 'reversal_first_signal_invalidated'
        if (cause == "reversal_signal_expired" and age > 5
                and (row["machine_contract_error"] == "reversal_signal_expired_or_changed"
                     or expired_registration)):
            return cause
        if (cause == "reversal_first_signal_invalidated" and 0 <= age <= 5
                and event.get("decision_phase") == "FIRST_UPTICK"
                and receipt.get("current_turn_id") != event["event_id"]
                and row["machine_contract_error"] == cause):
            return cause
    except (KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError):
        pass
    return None


def source_gap_semantics(data_root, now, *, tail_bytes=SOURCE_TAIL_BYTES):
    """Observe source causes before and after machine assessment without trading authority."""
    now = stamp(now)
    day = now.date().isoformat()
    paths = {
        "probe": (data_root / "pipeline_events" / f"pipeline_events_{day}.jsonl", "emitted_at"),
        "trace": (data_root / "ai_decision_trace" / f"ai_decision_trace_{day}.jsonl", "decision_ts"),
        "pending": (data_root / "ai_decision_outcomes" / f"ai_decision_outcomes_{day}.jsonl", "decision_ts"),
    }
    sources, issues, diagnostics, observed = {}, Counter(), Counter(), Counter()
    issue_scopes, diagnostic_scopes, healthy_scopes = Counter(), Counter(), Counter()
    issue_examples, diagnostic_examples = [], []
    seen = set()
    probe_by_route, assessed_by_route = Counter(), Counter()

    def record(stage, reason, row, *, diagnostic=False, code=None, route=None, attempt=None):
        if stage == "machine_probe" and not attempt:
            fields = row.get("fields")
            probe_attempt = fields.get("evaluation_attempt_id") if isinstance(fields, dict) else None
            if isinstance(probe_attempt, str):
                normalized_attempt = probe_attempt.strip()
                if normalized_attempt.lower() not in {"", "-", "none", "null"}:
                    attempt = normalized_attempt
        reason = str(reason)
        if (len(reason) > 80 or not reason
                or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_:-"
                       for char in reason)):
            reason = "unclassified_source_gap"
        identity = (stage, attempt or row.get("decision_trace_id") or row.get("emitted_at"),
                    code or row.get("stock_code"), route or row.get("market_data_route"), reason)
        if identity in seen:
            return
        seen.add(identity)
        (diagnostics if diagnostic else issues)[f"{stage}:{reason}"] += 1
        scope = scope_for(stage, row, route)
        (diagnostic_scopes if diagnostic else issue_scopes)[f"{scope}|{stage}:{reason}"] += 1
        examples = diagnostic_examples if diagnostic else issue_examples
        if len(examples) < 3:
            examples.append({"stage": stage, "reason": reason,
                "occurred_at": row.get("decision_ts") or row.get("emitted_at"),
                "stock_code": str(code or row.get("stock_code") or "")[:6],
                "route": str(route or row.get("market_data_route") or "")[:48],
                "effective_venue": str(row.get("effective_venue") or "")[:32],
                "session_bucket": str(row.get("session_bucket") or "")[:48],
                "evaluation_attempt_id": str(attempt or row.get("evaluation_attempt_id") or "")[:96]})

    def scope_for(stage, row, route=None):
        if stage == "machine_probe":
            return f'route:{route or "UNKNOWN"}'
        return (f'{str(row.get("effective_venue") or "UNKNOWN").upper()}|'
                f'{str(row.get("session_bucket") or "UNKNOWN").upper()}|'
                f'route:{str(route or row.get("market_data_route") or "UNKNOWN")[:48]}')

    def healthy(stage, row, route=None):
        healthy_scopes[f"{scope_for(stage, row, route)}|{stage}"] += 1

    probe_rows, sources["probe"] = _recent_source_rows(
        paths["probe"][0], now, time_field=paths["probe"][1], tail_bytes=tail_bytes)
    for row in probe_rows:
        if row.get("pipeline") != "ENTRY_PIPELINE" or row.get("stage") != "zero_base_probe_result":
            continue
        fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
        result = str(fields.get("zero_base_probe_result") or "")
        reason = str(fields.get("zero_base_probe_reason") or "")
        route = fields.get("zero_base_route")
        observed["probe_results"] += 1
        if result in {"assessed", "required_feature_insufficient", "source_unavailable"} or (
                result == "policy_unavailable" and reason != "zero_base_runtime_disabled"):
            probe_by_route[str(route or "UNKNOWN")] += 1
        if result == "assessed":
            observed["probe_assessed"] += 1
            assessed_by_route[str(route or "UNKNOWN")] += 1
            captured = fields.get("machine_capture_status") == "captured"
            observation_hash = str(fields.get("machine_observation_sha256") or "")
            if (not captured or len(observation_hash) != 64
                    or any(char not in "0123456789abcdef" for char in observation_hash)):
                record("machine_probe", "capture_receipt_missing_or_invalid", row,
                       code=row.get("stock_code"), route=route)
            else:
                healthy("machine_probe", row, route)
        elif result == "required_feature_insufficient":
            kind = str(fields.get("zero_base_machine_source_gap_kind") or "").strip("- ")
            kind = kind or (reason if reason in {
                "tick_or_candle_missing", "candle_source_missing", "candle_context_missing",
                "ws_tick_source_changed_before_machine",
            } else "required_feature_insufficient_unclassified")
            record("machine_probe", kind, row,
                   diagnostic=kind not in {"source_route_conflict", "feature_tick_selection_gap"},
                   code=row.get("stock_code"), route=route)
        elif result == "source_unavailable" and reason in {
            "route_snapshot_missing", "0B_missing", "0B_age_exceeded", "0D_missing",
            "0D_age_exceeded", "rest_route_or_receive_clock_invalid",
            "exact_route_subscription_conflict", "ws_registration_receipt_missing",
        }:
            record("machine_probe", reason, row,
                   diagnostic=reason in {"route_snapshot_missing", "0B_missing", "0B_age_exceeded",
                                         "0D_missing", "0D_age_exceeded"},
                   code=row.get("stock_code"), route=route)
        elif result == "policy_unavailable" and (
                reason == "assessment_contract_invalid" or reason.startswith("machine_exception:")
                or fields.get("zero_base_machine_contract_error") not in (None, "", "-")):
            kind = str(fields.get("zero_base_machine_source_gap_kind") or "").strip("- ")
            contract_error = str(fields.get("zero_base_machine_contract_error") or "").strip("- ")
            kind = kind or (
                "machine_source_nonfinite"
                if contract_error.startswith("Out of range float values are not JSON compliant:")
                else contract_error
            ) or (
                "contract_error_receipt_missing" if reason == "assessment_contract_invalid" else reason)
            record("machine_probe", kind, row,
                   diagnostic=kind == "trusted_tape_source_insufficient",
                   code=row.get("stock_code"), route=route)
    for route, count in probe_by_route.items():
        if sources["probe"]["status"] != "complete" or count < 10:
            continue
        if assessed_by_route[route] * 5 < count:
            # This is degraded admission coverage, not proof of a Kiwoom fault.
            issues[f"machine_probe:coverage_degraded:{route}"] += 1
            issue_scopes[f"route:{route}|machine_probe:coverage_degraded"] += 1
        else:
            healthy_scopes[f"route:{route}|machine_probe:coverage_degraded"] += 1

    trace_rows, sources["trace"] = _recent_source_rows(
        paths["trace"][0], now, time_field=paths["trace"][1], tail_bytes=tail_bytes)
    # Only the adjacent partition required by the same bounded observation
    # window is read. Physical append dates never replace occurrence clocks.
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if (now-midnight).total_seconds() < SOURCE_WINDOW_SEC:
        previous = (now-timedelta(days=1)).date().isoformat()
        for kind, rows in (('probe', probe_rows), ('trace', trace_rows)):
            prior_path = paths[kind][0].with_name(paths[kind][0].name.replace(day, previous))
            prior_rows, receipt = _recent_source_rows(prior_path, now,
                time_field=paths[kind][1], tail_bytes=tail_bytes, allow_adjacent_date=True)
            rows.extend(prior_rows)
            sources[kind]['adjacent_partition'] = receipt
            if receipt['status'] != 'complete':
                sources[kind]['status'] = 'partial'
    pass_projection = []
    unmapped_pass_count = 0
    for row in trace_rows:
        if (row.get('decision_stage') == 'entry_screen'
                and row.get('decision_evaluation_status') == 'evaluated'
                and row.get('entry_mechanistic_action') == 'ENTER_NOW'
                and row.get('entry_ai_screen_status') == 'pass'
                and row.get('entry_ai_risk_verdict') == 'PASS'
                and row.get('provider_called') is True):
            if (not all(str(row.get(key) or '').strip().lower() not in
                    {'', '-', 'none', 'null', 'unknown', '0'} for key in (
                        'async_request_id', 'decision_trace_id', 'evaluation_attempt_id',
                        'async_producer_pid', 'async_producer_start_ticks'))
                    or not str(row.get('stock_code') or '').isdigit()
                    or len(str(row.get('stock_code'))) != 6):
                unmapped_pass_count += 1
                continue
            fields = {k: row.get(k) for k in ('async_request_id', 'async_producer_pid',
                'async_producer_start_ticks', 'async_origin_deadline_epoch', 'scanner_generation_id',
                'evaluation_attempt_id', 'effective_venue', 'async_order_venue', 'entry_machine_bundle_sha256',
                'entry_auxiliary_policy_sha256', 'watch_origin', 'watch_admission_id', 'watch_generation_id',
                'scanner_promotion_id')}
            fields.update(ai_decision_trace_id=row['decision_trace_id'],
                async_disposition='validated_pass_trace',
                async_disposition_event_id='pass-trace:' + row['decision_trace_id'],
                async_machine_action='ENTER_NOW', async_auxiliary_status='pass',
                async_auxiliary_verdict='PASS', async_provider_called=True)
            pass_projection.append(dict(emitted_at=row['decision_ts'], stock_code=row['stock_code'], fields=fields))
    for row in trace_rows:
        if row.get("decision_stage") != "entry_screen":
            continue
        observed["entry_traces"] += 1
        status = str(row.get("machine_evaluation_status") or "")
        if status == "assessed":
            observed["machine_assessed"] += 1
            capture_status = row.get("machine_capture_status")
            observation_hash = str(row.get("machine_observation_sha256") or "")
            capture_valid = (capture_status == "captured" and len(observation_hash) == 64
                             and all(char in "0123456789abcdef" for char in observation_hash))
            if not capture_valid:
                record("machine_trace", "capture_receipt_missing_or_invalid", row)
            if row.get("entry_mechanistic_action") == "SOURCE_INVALID":
                record("machine_trace", str(row.get("entry_source_invalid_primary_blocker")
                                            or "source_invalid_unclassified"), row, diagnostic=True)
            elif capture_valid and not row.get("machine_contract_error"):
                healthy("machine_trace", row)
        elif status in {"required_feature_blocked_before_assessment", "source_quality_blocked_before_assessment"}:
            kind = str(row.get("machine_source_gap_kind") or status)
            record("machine_trace", kind, row,
                   diagnostic=kind not in {"source_route_conflict", "feature_tick_selection_gap"})
        elif status == "assessment_contract_invalid":
            kind = str(row.get("machine_source_gap_kind") or row.get("machine_contract_error")
                       or "contract_error_receipt_missing")
            lifecycle = _reversal_lifecycle_diagnostic(row)
            if lifecycle:
                kind = lifecycle
            if kind.startswith("Out of range float values are not JSON compliant:"):
                kind = "machine_source_nonfinite"
            record("machine_trace", kind, row,
                   diagnostic=bool(lifecycle) or kind == "trusted_tape_source_insufficient")
        elif row.get("machine_contract_error"):
            kind = str(row.get("machine_source_gap_kind") or row["machine_contract_error"])
            record("machine_trace", kind, row,
                   diagnostic=kind not in {"source_route_conflict", "feature_tick_selection_gap"})
        if (row.get("entry_mechanistic_action") != "ENTER_NOW"
                or row.get("entry_ai_screen_required") is not True):
            continue
        observed["auxiliary_required"] += 1
        if row.get("provider_called") is not True:
            continue  # An uncalled auxiliary has no provider-cost receipt obligation.
        observed["auxiliary_called"] += 1
        reference = row.get("reference_price")
        route_valid = (type(reference) in (int, float) and math.isfinite(reference) and reference > 0
                       and row.get("effective_venue") and row.get("session_bucket")
                       and row.get("market_data_route"))
        if not route_valid:
            record("auxiliary_call", "route_or_reference_missing", row)
        if row.get("entry_ai_screen_status") == "not_evaluated_transport":
            observed["auxiliary_transport_unavailable"] += 1
        if row.get("entry_cost_source_status") == "source_gap":
            record("auxiliary_call", "cost_source_gap", row)
        elif row.get("entry_cost_source_status") != "exact_pre_provider_replay":
            record("auxiliary_call", "cost_receipt_missing", row)
        elif not _auxiliary_cost_receipt_valid(row):
            record("auxiliary_call", "cost_receipt_invalid", row)
        elif route_valid:
            observed["auxiliary_cost_bound"] += 1
            healthy("auxiliary_call", row)

    pending_rows, sources["pending"] = _recent_source_rows(
        paths["pending"][0], now, time_field=paths["pending"][1], tail_bytes=tail_bytes)
    pending_by_trace = {}
    for row in pending_rows:
        if (row.get("decision_stage") != "entry_screen"
                or row.get("entry_mechanistic_action") != "ENTER_NOW"
                or row.get("entry_ai_screen_required") is not True
                or row.get("entry_ai_screen_status") not in {
                    "pass", "veto", "caution", "insufficient", "response_invalid",
                    "not_evaluated_transport"}):
            continue
        observed["auxiliary_pending"] += 1
        if row.get("decision_trace_id"):
            prior = pending_by_trace.setdefault(row["decision_trace_id"], row)
            if prior is not row:
                record("auxiliary_pending", "duplicate_trace_identity", row)
        if not row.get("decision_trace_id") or not row.get("evaluation_attempt_id"):
            record("auxiliary_pending", "identity_missing", row)
        reference = row.get("reference_price")
        pending_route_valid = (row.get("market_data_route") and row.get("effective_venue")
                               and row.get("session_bucket") and type(reference) in (int, float)
                               and math.isfinite(reference) and reference > 0)
        if not pending_route_valid:
            record("auxiliary_pending", "route_or_reference_missing", row)
        if row.get("entry_ai_screen_status") != "insufficient":
            if row.get("entry_cost_source_status") != "exact_pre_provider_replay":
                record("auxiliary_pending", "cost_receipt_missing", row)
            elif not _auxiliary_cost_receipt_valid(row):
                record("auxiliary_pending", "cost_receipt_invalid", row)
            elif pending_route_valid and row.get("decision_trace_id") and row.get("evaluation_attempt_id"):
                observed["auxiliary_pending_bound"] += 1
                healthy("auxiliary_pending", row)
    trace_by_id = {row["decision_trace_id"]: row for row in trace_rows
                   if row.get("decision_stage") == "entry_screen" and row.get("decision_trace_id")}
    binding_fields = ("evaluation_attempt_id", "stock_code", "effective_venue", "session_bucket",
                      "market_data_route", "reference_price", "entry_cost_source_status",
                      "entry_conservative_execution_cost_pct", "entry_cost_scope", "entry_cost_basis",
                      "entry_cost_contract_sha256", "entry_cost_replay_context_sha256",
                      "entry_cost_evaluation_attempt_id")
    for trace_id, pending in pending_by_trace.items():
        trace = trace_by_id.get(trace_id)
        if trace is not None and any(pending.get(field) != trace.get(field) for field in binding_fields):
            record("auxiliary_pending", "trace_binding_mismatch", pending)
    if sources["pending"]["status"] == "complete":
        for row in trace_rows:
            if (row.get("decision_stage") == "entry_screen"
                    and row.get("entry_mechanistic_action") == "ENTER_NOW"
                    and row.get("entry_ai_screen_required") is True
                    and row.get("outcome_label_eligible") is True
                    and row.get("decision_trace_id")
                    and (now - stamp(row.get("decision_ts"))).total_seconds() >= 60):
                pending = pending_by_trace.get(row["decision_trace_id"])
                if pending is None:
                    record("auxiliary_pending", "label_receipt_missing", row)
                elif any(pending.get(field) != row.get(field) for field in binding_fields):
                    record("auxiliary_pending", "trace_binding_mismatch", pending)
    elif sources["pending"].get("reason") in {"FileNotFoundError", "empty_source"}:
        for row in trace_rows:
            at = stamp(row.get("decision_ts"))
            if (row.get("decision_stage") == "entry_screen"
                    and row.get("entry_mechanistic_action") == "ENTER_NOW"
                    and row.get("entry_ai_screen_required") is True
                    and row.get("outcome_label_eligible") is True
                    and row.get("decision_trace_id") and at
                    and (now - at).total_seconds() >= 60):
                record("auxiliary_pending", "source_file_missing", row)
    remediation = []
    for issue in sorted(issues):
        stage = issue.split(":", 1)[0]
        owner, action = {
            "machine_probe": ("zero_base_probe|scalping_feature_packet",
                              "compare exact REG/0B/0D route and epoch; use existing queue rotation"),
            "machine_trace": ("entry_setup_live_policy|ai_decision_trace",
                              "inspect exact feature and decision-source receipt"),
            "auxiliary_call": ("ai_engine_openai|ai_decision_trace",
                               "repair exact pre-provider cost or route receipt from verified source"),
            "auxiliary_pending": ("ai_decision_trace|ai_decision_quality",
                                  "join exact attempt pending label and completed-bar source"),
        }[stage]
        remediation.append({"issue": issue, "owner": owner, "source_only_action": action,
                            "automatic_repair_attempted": False, "order_authority": False})
    status = ("gap_observed" if issues or diagnostics else
              "observed_no_gap" if all(s["status"] == "complete" for s in sources.values()) and any(observed.values()) else
              "unobservable")
    return {"schema": "machine_auxiliary_intraday_source_semantics_v1", "as_of": now.isoformat(),
        "status": status, "metric_role": "source_quality_gate", "decision_authority": "report_only",
        "window_policy": "current_10m_bounded_jsonl_tail", "sample_floor": "one_exact_stage_receipt",
        "primary_decision_metric": "source_gap_events_by_stage_and_reason",
        "source_quality_gate": "exact_current_date_complete_window_per_source",
        "forbidden_uses": ["order_authority", "threshold_or_provider_change", "missing_as_zero_ev",
                           "actual_trade_failure_claim", "historical_source_repair_claim"],
        "sources": sources, "observed": dict(observed), "issues": dict(sorted(issues.items())),
        "async_pass_projection": pass_projection[-128:],
        "async_pass_unmapped_count": unmapped_pass_count,
        "async_transition_projection": [dict(emitted_at=row.get('emitted_at'),
            stock_code=row.get('stock_code'), fields=row.get('fields') or {})
            for row in probe_rows if row.get('stage') == 'entry_async_disposition'][-1024:],
        "async_transition_projection_coverage": ('complete' if sources['probe']['status'] == 'complete'
            and sum(row.get('stage') == 'entry_async_disposition' for row in probe_rows) <= 1024 else 'partial'),
        "async_pass_projection_coverage": ('complete' if len(pass_projection) <= 128
            and not unmapped_pass_count and sources['trace']['status'] == 'complete' else 'partial'),
        "diagnostics": dict(sorted(diagnostics.items())),
        "issues_by_scope": dict(sorted(issue_scopes.items())),
        "diagnostics_by_scope": dict(sorted(diagnostic_scopes.items())),
        "healthy_by_scope": dict(sorted(healthy_scopes.items())),
        "probe_route_counts": dict(sorted(probe_by_route.items())),
        "probe_route_assessed_counts": dict(sorted(assessed_by_route.items())),
        "coverage_alert_floor": "10_same_route_source_eligible_probes_below_20pct_assessed",
        "remediation": remediation,
        "examples": issue_examples + diagnostic_examples, "runtime_effect": False,
        "next_action": ("inspect_exact_attempt_source_then_use_existing_bounded_source_only_repair" if issues
                        else "retain_sparse_or_source_quality_diagnostic_and_existing_queue_rotation" if diagnostics
                        else None)}


def attach_source_gap_semantics(result, semantics):
    """Persist fresh source incidents; lack of a complete window cannot resolve one."""
    result["source_gap_semantics"] = semantics
    from types import SimpleNamespace
    current = result.get('async_disposition_coverage') or {}
    retained = [SimpleNamespace(stage='entry_async_disposition', **row)
                for row in (current.get('attempt_projection') or [])
                    + (semantics.get('async_transition_projection') or [])]
    result['async_disposition_coverage'] = async_disposition_coverage(retained, result['as_of'],
        pass_projections=semantics.get('async_pass_projection') or [],
        source_coverage=semantics.get('async_pass_projection_coverage'))
    key = "machine_auxiliary_intraday_source_gap"
    old = result["incidents"].get(key, {})
    issues = semantics.get("issues") or {}
    now = stamp(result["as_of"])
    if issues:
        recurring = bool(set(semantics.get("issues_by_scope") or {})
                         & set(old.get("issues_by_scope") or {}))
        first = (old.get("first_seen", result["as_of"])
                 if old.get("status") in {"pending", "active"} and recurring
                 else result["as_of"])
        only_coverage = all(issue.startswith("machine_probe:coverage_degraded:") for issue in issues)
        item = {"scope": "machine|auxiliary|exact_current_day", "rule": key,
            "category": "review_required" if only_coverage else "structural_evidence",
            "first_seen": first, "last_seen": result["as_of"],
            "status": "active" if (now - stamp(first)).total_seconds() >= 240 else "pending",
            "count": sum(issues.values()), "issues": issues, "examples": semantics.get("examples", [])[:3],
            "issues_by_scope": semantics.get("issues_by_scope", {}),
            "source_status": {name: source.get("status") for name, source in semantics.get("sources", {}).items()},
            "owner": "zero_base_probe|ai_decision_trace|ai_decision_outcomes",
            "closure_test": "new exact-route machine and auxiliary receipts with complete recent windows",
            "notified_status": (old.get("notified_status")
                                if recurring and old.get("status") in {"pending", "active"} else None)}
        if old.get("history"):
            item["history"] = old["history"]
        if old.get("status") in {"recovered", "historical_unresolved"}:
            item["history"] = (list(old.get("history", [])) +
                               [{k: v for k, v in old.items() if k != "history"}])[-8:]
        result["incidents"][key] = item
    elif old.get("status") in {"pending", "active", "historical_unresolved"}:
        stage_source = {"machine_probe": "probe", "machine_trace": "trace",
                        "auxiliary_call": "trace", "auxiliary_pending": "pending"}
        stages = {issue.split(":", 1)[0] for issue in old.get("issues", {})}
        prior_scopes = old.get("issues_by_scope") or {}
        healthy_scopes = semantics.get("healthy_by_scope") or {}
        def recovery_key(issue_scope):
            scope, stage_reason = issue_scope.rsplit("|", 1)
            if stage_reason.startswith("machine_probe:coverage_degraded"):
                return issue_scope
            return f'{scope}|{stage_reason.split(":", 1)[0]}'

        if stages and stages <= set(stage_source) and all(
                (semantics.get("sources", {}).get(stage_source[stage]) or {}).get("status") == "complete"
                for stage in stages) and prior_scopes and all(
                healthy_scopes.get(recovery_key(scope))
                for scope in prior_scopes):
            result["incidents"][key] = {**old, "status": "recovered", "last_seen": result["as_of"],
                "historical_source_repaired": False}
        elif old.get("status") == "active":
            result["incidents"][key] = {**old, "status": "historical_unresolved"}
    item = result["incidents"].get(key, {})
    if item.get("status") in {"active", "recovered"} and item.get("notified_status") != item["status"]:
        result["notification_pending"].append(key)


def pre_submit_delay_source_semantics(data_root, now, prior_cursor=None):
    """Incremental raw/compact/summary and intent receipts; no order authority."""
    from src.engine.scalping.pre_submit_delay_tuning import expected_route_for_session
    from src.engine.pipeline_event_summary import (
        IDENTITY_MODULUS, PRODUCER_SUMMARY_STAGES, execution_projection_identity,
        load_summary_rows, summary_event_from_payload,
    )

    now = stamp(now)
    day = now.date().isoformat()
    data_root = Path(data_root)
    raw_path = data_root / "pipeline_events" / f"pipeline_events_{day}.jsonl"
    prior_today = isinstance(prior_cursor, dict) and prior_cursor.get("date") == day
    previous = prior_cursor if prior_today else {}
    if previous and (type(previous.get("offset")) is not int
                     or not isinstance(previous.get("minutes"), dict)
                     or not isinstance(previous.get("delay_events"), list)
                     or stamp(previous.get("coverage_started_at")) is None):
        previous = {}
    cursor = {"date": day, "offset": 0, "device": None, "inode": None,
              "coverage_started_at": None, "minutes": {}, "delay_events": []}
    issues, diagnostics, healthy, examples = Counter(), Counter(), Counter(), []
    issue_scopes, healthy_scopes = Counter(), Counter()
    raw_status = "unobservable"
    try:
        stat_before = raw_path.stat()
        same_file = (previous.get("device"), previous.get("inode")) == (stat_before.st_dev, stat_before.st_ino)
        if same_file and 0 <= previous.get("offset", -1) <= stat_before.st_size:
            cursor.update({key: previous.get(key) for key in
                           ("offset", "coverage_started_at", "minutes", "delay_events")})
        else:
            reset_generation = prior_today
            cursor["coverage_started_at"] = (
                f"{day}T00:00:00+09:00" if not reset_generation and stat_before.st_size <= DELAY_RAW_BUDGET
                else now.isoformat())
            cursor["offset"] = 0 if stat_before.st_size <= DELAY_RAW_BUDGET else stat_before.st_size - DELAY_RAW_BUDGET
        cursor.update(device=stat_before.st_dev, inode=stat_before.st_ino)
        start = cursor["offset"]
        end = min(stat_before.st_size, start + DELAY_RAW_BUDGET)
        with raw_path.open("rb") as handle:
            handle.seek(start)
            payload = handle.read(end - start)
        stat_after = raw_path.stat()
        if (stat_before.st_dev, stat_before.st_ino) != (stat_after.st_dev, stat_after.st_ino) or stat_after.st_size < end:
            raise ValueError("raw_generation_changed")
        if start and not same_file:
            if b"\n" not in payload:
                raise ValueError("raw_tail_boundary_missing")
            payload = payload.partition(b"\n")[2]
            start = end - len(payload)
        complete_bytes = payload.rfind(b"\n") + 1
        malformed = 0
        for line in payload[:complete_bytes].splitlines():
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError("raw_event_not_object")
                at = stamp(row.get("emitted_at"))
                if at is None:
                    raise ValueError("raw_event_time_invalid")
                if at.date() != now.date() or at > now:
                    continue
                event = summary_event_from_payload(row, summary_stages=PRODUCER_SUMMARY_STAGES)
                if event is None:
                    continue
                minute = event.emitted_at.replace(second=0, microsecond=0).isoformat()
                key = f"{minute}|{event.stage}"
                item = cursor["minutes"].setdefault(key, {"count": 0, "identity_sum": "0" * 64})
                item["count"] += 1
                item["identity_sum"] = f"{(int(item['identity_sum'], 16) + event.evidence_hash) % IDENTITY_MODULUS:064x}"
                if event.stage in DELAY_STAGES:
                    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
                    cursor["delay_events"].append({"stage": event.stage, "at": at.isoformat(),
                        "event_id": execution_projection_identity(row),
                        "stock_code": str(row.get("stock_code") or ""),
                        "record_id": str(row.get("record_id") or ""),
                        "delay_intent_id": str(fields.get("delay_intent_id") or ""),
                        "target_delay_sec": fields.get("target_delay_sec"),
                        "selected_delay_sec": fields.get("selected_delay_sec"),
                        "route": str(fields.get("route") or ""),
                        "session_bucket": str(fields.get("market_session_bucket") or ""),
                        "quote_route": str(fields.get("quote_route") or ""),
                        "quote_valid": fields.get("quote_valid"),
                        "quote_source_reason": fields.get("quote_source_reason"),
                        "decision_committed_at_epoch": fields.get("decision_committed_at_epoch"),
                        "terminal_finished_at_epoch": fields.get("terminal_finished_at_epoch")})
            except (ValueError, TypeError, UnicodeDecodeError, KeyError):
                malformed += 1
        cursor["offset"] = start + complete_bytes
        cutoff = now - timedelta(seconds=DELAY_WINDOW_SEC + DELAY_SUMMARY_GRACE_SEC + 60)
        cursor["minutes"] = {key: value for key, value in cursor["minutes"].items()
                             if (stamp(key.split("|", 1)[0]) or now) >= cutoff}
        cursor["delay_events"] = [row for row in cursor["delay_events"]
                                  if stamp(row["at"]) >= cutoff]
        raw_status = ("complete" if cursor["offset"] == stat_before.st_size and not malformed
                      and stamp(cursor["coverage_started_at"]) <= now - timedelta(seconds=DELAY_WINDOW_SEC)
                      else "partial")
        if raw_status == "complete":
            healthy["raw_cursor_backlog"] += 1
            healthy["raw_source_unobservable_with_summary"] += 1
            healthy_scopes["raw_cursor_backlog|raw"] += 1
            healthy_scopes["raw_source_unobservable_with_summary|raw"] += 1
        if malformed:
            issues["raw_malformed_event"] += malformed
        if stat_before.st_size - cursor["offset"] > 1024 * 1024 and end - start >= DELAY_RAW_BUDGET:
            issues["raw_cursor_backlog"] += 1
            issue_scopes["raw_cursor_backlog|raw"] += 1
    except (OSError, ValueError, TypeError) as exc:
        raw_status = "unobservable"
        diagnostics[f"raw_unobservable:{type(exc).__name__}"] += 1
        if str(exc) == "raw_tail_boundary_missing":
            issues["raw_cursor_backlog"] += 1
            issue_scopes["raw_cursor_backlog|raw"] += 1

    summary_status = "unobservable"
    summary_minutes = {}
    manifest = {}
    summary_grace_sec = DELAY_SUMMARY_GRACE_SEC
    summary_dir = data_root / "pipeline_event_summaries"
    summary_path = summary_dir / f"pipeline_event_producer_summary_{day}.jsonl"
    manifest_path = summary_dir / f"pipeline_event_producer_summary_manifest_{day}.json"
    try:
        manifest_before = manifest_path.stat()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        before = summary_path.stat()
        if before.st_size > 64 * 1024 * 1024 or manifest.get("summary_storage_size_bytes") != before.st_size:
            raise ValueError("summary_generation_uncommitted")
        rows = load_summary_rows(summary_path, include_samples=False, strict=True)
        after = summary_path.stat()
        manifest_after = manifest_path.stat()
        generation = lambda stat: (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
        if (manifest.get("mode") != "shadow" or manifest.get("summary_path") != str(summary_path)
                or generation(after) != generation(before)
                or generation(manifest_after) != generation(manifest_before)
                or manifest.get("summary_event_count") != sum(row["event_count"] for row in rows)):
            raise ValueError("summary_generation_changed")
        flush_interval = manifest.get("flush_interval_sec")
        if type(flush_interval) is int and flush_interval > 0:
            summary_grace_sec = max(DELAY_SUMMARY_GRACE_SEC, 2 * flush_interval + 30)
            if flush_interval > 120:
                issues["producer_summary_flush_interval_too_long"] += 1
                issue_scopes["producer_summary_flush_interval_too_long|producer"] += 1
            else:
                healthy["producer_summary_flush_interval_too_long"] += 1
                healthy_scopes["producer_summary_flush_interval_too_long|producer"] += 1
        for row in rows:
            if row.get("target_date") != day:
                raise ValueError("summary_target_date_invalid")
            key = f"{row['bucket_start']}|{row['stage']}"
            item = summary_minutes.setdefault(key, {"count": 0, "identity_sum": "0" * 64})
            item["count"] += row["event_count"]
            item["identity_sum"] = f"{(int(item['identity_sum'], 16) + int(row['evidence_hash_sum'], 16)) % IDENTITY_MODULUS:064x}"
        summary_status = "complete"
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        diagnostics[f"summary_unobservable:{type(exc).__name__}"] += 1

    compact_status = "complete"
    compact_ids = set()
    compact_recent_ids = set()
    compact_duplicates = 0
    compact_dir = data_root / "threshold_cycle" / f"date={day}" / "family=pre_submit_delay"
    try:
        total_bytes = 0
        for path in sorted(compact_dir.glob("part-execution-*.jsonl")):
            before = path.stat()
            total_bytes += before.st_size
            if path.is_symlink() or total_bytes > 8 * 1024 * 1024:
                raise ValueError("compact_source_unbounded")
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    if not line.endswith("\n"):
                        raise ValueError("compact_partial_line")
                    row = json.loads(line)
                    if row.get("emitted_date") != day or row.get("family") != "pre_submit_delay":
                        raise ValueError("compact_identity_invalid")
                    if row.get("stage") in DELAY_STAGES:
                        identity = str(row.get("execution_source_event_sha256") or "")
                        if identity != execution_projection_identity(row):
                            raise ValueError("compact_projection_identity_invalid")
                        if identity in compact_ids:
                            compact_duplicates += 1
                        compact_ids.add(identity)
                        emitted = stamp(row.get("emitted_at"))
                        if emitted and now - timedelta(seconds=DELAY_WINDOW_SEC) <= emitted <= now - timedelta(seconds=20):
                            compact_recent_ids.add(identity)
            after = path.stat()
            if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
                raise ValueError("compact_generation_changed")
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        compact_status = "unobservable"
        diagnostics[f"compact_unobservable:{type(exc).__name__}"] += 1

    if raw_status == "complete":
        grace = now - timedelta(seconds=summary_grace_sec)
        window = now - timedelta(seconds=DELAY_WINDOW_SEC)
        for key in set(cursor["minutes"]) | (set(summary_minutes) if summary_status == "complete" else set()):
            minute = stamp(key.split("|", 1)[0])
            if minute is None or minute < window or minute > grace:
                continue
            raw_item = cursor["minutes"].get(key, {"count": 0, "identity_sum": "0" * 64})
            summarized = summary_minutes.get(key, {"count": 0, "identity_sum": "0" * 64})
            stage = key.split("|", 1)[1]
            if summary_status != "complete":
                if raw_item["count"]:
                    issues["producer_summary_unobservable_with_raw"] += 1
                    issue_scopes[f"producer_summary_unobservable_with_raw|{stage}"] += 1
                continue
            if raw_item != summarized:
                issues["producer_raw_summary_window_mismatch"] += 1
                issue_scopes[f"producer_raw_summary_window_mismatch|{stage}"] += 1
                if len(examples) < 3:
                    examples.append({"reason": "producer_raw_summary_window_mismatch", "window_stage": key,
                                     "raw_count": raw_item["count"], "summary_count": summarized["count"]})
            elif raw_item["count"]:
                healthy["producer_raw_summary_window_mismatch"] += 1
                healthy_scopes[f"producer_raw_summary_window_mismatch|{stage}"] += 1
                healthy["producer_summary_unobservable_with_raw"] += 1
                healthy_scopes[f"producer_summary_unobservable_with_raw|{stage}"] += 1
        raw_recent_ids = set()
        raw_recent_identity_counts = Counter()
        commit_by_intent = {
            (row.get("stock_code", ""), row.get("record_id", ""), row["delay_intent_id"]): row
            for row in cursor["delay_events"]
            if row["stage"] == "pre_submit_delay_committed" and row["delay_intent_id"]
        }
        for row in cursor["delay_events"]:
            at = stamp(row["at"])
            if at < window or at > now - timedelta(seconds=20):
                continue
            raw_recent_ids.add(row["event_id"])
            raw_recent_identity_counts[row["event_id"]] += 1
            if compact_status == "complete" and row["event_id"] not in compact_ids:
                issues["raw_compact_event_missing"] += 1
                issue_scopes[f"raw_compact_event_missing|{row['stage']}"] += 1
                if len(examples) < 3:
                    examples.append({"reason": "raw_compact_event_missing", "stage": row["stage"],
                                     "delay_intent_id": row["delay_intent_id"]})
            elif compact_status == "complete":
                healthy["raw_compact_event_missing"] += 1
                healthy_scopes[f"raw_compact_event_missing|{row['stage']}"] += 1
                healthy["compact_source_unobservable_with_raw"] += 1
                healthy_scopes[f"compact_source_unobservable_with_raw|{row['stage']}"] += 1
            else:
                issues["compact_source_unobservable_with_raw"] += 1
                issue_scopes[f"compact_source_unobservable_with_raw|{row['stage']}"] += 1
            if row["stage"] == "pre_submit_delay_committed":
                expected_route = expected_route_for_session(row["session_bucket"])
                if not expected_route:
                    issues["committed_session_missing"] += 1
                    issue_scopes["committed_session_missing|UNKNOWN"] += 1
                elif row["route"] and row["route"].upper() != expected_route:
                    issues["committed_route_session_mismatch"] += 1
                    issue_scopes[f"committed_route_session_mismatch|{row['session_bucket']}"] += 1
                else:
                    if not row["route"]:
                        diagnostics["committed_route_derived_from_session"] += 1
                    healthy["committed_session_missing"] += 1
                    healthy["committed_route_session_mismatch"] += 1
                    healthy_scopes["committed_session_missing|UNKNOWN"] += 1
                    healthy_scopes[f"committed_route_session_mismatch|{row['session_bucket']}"] += 1
            if row["stage"] == "pre_submit_delay_quote_observed":
                commit = commit_by_intent.get(
                    (row.get("stock_code", ""), row.get("record_id", ""), row["delay_intent_id"]), {})
                quote_scope = (expected_route_for_session(commit.get("session_bucket"))
                               or commit.get("route") or row["quote_route"] or row["route"] or "UNKNOWN")
                if str(row["quote_valid"]).lower() != "true":
                    issues["quote_source_invalid"] += 1
                    issue_scopes[f"quote_source_invalid|{quote_scope}"] += 1
                    if len(examples) < 3:
                        examples.append({"reason": row["quote_source_reason"] or "quote_source_invalid",
                                         "stage": row["stage"], "delay_intent_id": row["delay_intent_id"]})
                else:
                    if not row["quote_route"]:
                        diagnostics["quote_route_derived_from_session"] += 1
                    healthy["quote_source_invalid"] += 1
                    healthy_scopes[f"quote_source_invalid|{quote_scope}"] += 1
        if any(count > 1 for count in raw_recent_identity_counts.values()):
            issues["raw_family_duplicate_identity"] += sum(
                count - 1 for count in raw_recent_identity_counts.values() if count > 1)
        if compact_status == "complete":
            if compact_duplicates:
                issues["compact_family_duplicate_identity"] += compact_duplicates
            healthy["compact_raw_event_missing"] += len(compact_recent_ids & raw_recent_ids)
            healthy_scopes["compact_raw_event_missing|pre_submit_delay"] += len(
                compact_recent_ids & raw_recent_ids)
            for identity in compact_recent_ids - raw_recent_ids:
                # A settled compact receipt without its raw parent is also a gap.
                issues["compact_raw_event_missing"] += 1
                issue_scopes["compact_raw_event_missing|pre_submit_delay"] += 1
                if len(examples) < 3:
                    examples.append({"reason": "compact_raw_event_missing", "event_id": identity})
        by_intent = {}
        for row in cursor["delay_events"]:
            if not row["delay_intent_id"]:
                continue
            identity = (row.get("stock_code", ""), row.get("record_id", ""), row["delay_intent_id"])
            group = by_intent.setdefault(identity, {"commit": None, "quotes": set(),
                                                    "quote_rows": [], "terminal": None})
            if row["stage"] == "pre_submit_delay_committed":
                group["commit"] = row
            elif row["stage"] == "pre_submit_delay_quote_observed":
                try:
                    horizon = float(row["target_delay_sec"])
                    if not math.isfinite(horizon) or horizon not in (0, 30, 60, 120, 180):
                        raise ValueError("quote_horizon_invalid")
                    group["quotes"].add(horizon)
                except (ValueError, TypeError):
                    issues["quote_horizon_invalid"] += 1
                group["quote_rows"].append(row)
            elif row["stage"] == "pre_submit_delay_intent_terminal":
                group["terminal"] = row
        for identity, group in by_intent.items():
            commit = group["commit"]
            if not commit:
                continue
            committed_route = commit["route"] or expected_route_for_session(commit["session_bucket"]) or ""
            for quote in group["quote_rows"]:
                if ((quote["route"] and quote["route"].upper() != committed_route.upper())
                        or (quote["quote_route"] and quote["quote_route"].upper() != committed_route.upper())):
                    issues["quote_commit_route_mismatch"] += 1
                    issue_scopes[f"quote_commit_route_mismatch|{committed_route or 'UNKNOWN'}"] += 1
                else:
                    healthy["quote_commit_route_mismatch"] += 1
                    healthy_scopes[f"quote_commit_route_mismatch|{committed_route or 'UNKNOWN'}"] += 1
            age = (now - stamp(commit["at"])).total_seconds()
            if age >= 30 and 0 not in group["quotes"] and 0.0 not in group["quotes"]:
                issues["zero_second_quote_missing"] += 1
                issue_scopes[f"zero_second_quote_missing|{committed_route or 'UNKNOWN'}"] += 1
                if len(examples) < 3:
                    examples.append({"reason": "zero_second_quote_missing", "delay_intent_id": identity[2],
                                     "stock_code": identity[0], "record_id": identity[1]})
            elif 0 in group["quotes"] or 0.0 in group["quotes"]:
                healthy["zero_second_quote_missing"] += 1
                healthy_scopes[f"zero_second_quote_missing|{committed_route or 'UNKNOWN'}"] += 1
            if age >= 300 and group["terminal"] is None:
                issues["intent_terminal_missing"] += 1
                issue_scopes[f"intent_terminal_missing|{committed_route or 'UNKNOWN'}"] += 1
            elif group["terminal"] is not None:
                healthy["intent_terminal_missing"] += 1
                healthy_scopes[f"intent_terminal_missing|{committed_route or 'UNKNOWN'}"] += 1
            for horizon in (30, 60, 120, 180):
                if age >= horizon + 30 and horizon not in group["quotes"]:
                    diagnostics[f"due_horizon_unobserved:{horizon}"] += 1
    elif summary_status == "complete" and any(
            stamp(key.split("|", 1)[0]) >= now - timedelta(seconds=DELAY_WINDOW_SEC)
            for key in summary_minutes):
        issues["raw_source_unobservable_with_summary"] += 1
        issue_scopes["raw_source_unobservable_with_summary|raw"] += 1
    status = ("gap_observed" if issues else "observed_no_gap"
              if raw_status == summary_status == compact_status == "complete" else "unobservable")
    return {"schema": "pre_submit_delay_intraday_source_semantics_v1", "as_of": now.isoformat(),
            "status": status, "metric_role": "source_quality_gate", "decision_authority": "report_only",
            "window_policy": "current_10m_incremental_raw_closed_minute_configured_flush_grace",
            "summary_grace_sec": summary_grace_sec,
            "sample_floor": "one_exact_stage_receipt", "primary_decision_metric": "source_gap_events_by_stage_and_reason",
            "source_quality_gate": "complete_raw_cursor_and_exact_current_day_source_generation",
            "forbidden_uses": ["order_authority", "threshold_change", "missing_as_zero_ev",
                               "historical_source_repair_claim"],
            "sources": {"raw": raw_status, "summary": summary_status, "compact": compact_status},
            "issues": dict(sorted(issues.items())), "diagnostics": dict(sorted(diagnostics.items())),
            "healthy": dict(sorted(healthy.items())),
            "issues_by_scope": dict(sorted(issue_scopes.items())),
            "healthy_by_scope": dict(sorted(healthy_scopes.items())),
            "examples": examples, "summary_last_writer_pid": manifest.get("last_writer_pid"),
            "summary_updated_at": manifest.get("updated_at"),
            "summary_flush_error_count": manifest.get("flush_error_count"),
            "cursor": cursor, "runtime_effect": False}


def attach_pre_submit_delay_source_semantics(result, semantics):
    result["pre_submit_delay_source_semantics"] = {k: v for k, v in semantics.items() if k != "cursor"}
    result["pre_submit_delay_source_cursor"] = semantics["cursor"]
    result["status"] = semantics["status"]
    result["blocker"] = next(iter(semantics["issues"]), None)
    key = "pre_submit_delay_intraday_source_gap"
    old = result["incidents"].get(key, {})
    if semantics["issues"]:
        result["incidents"][key] = {"scope": "pre_submit_delay|exact_current_day", "rule": key,
            "category": "structural_evidence", "status": "active",
            "first_seen": old.get("first_seen", result["as_of"]), "last_seen": result["as_of"],
            "count": sum(semantics["issues"].values()), "issues": semantics["issues"],
            "issues_by_scope": semantics["issues_by_scope"],
            "examples": semantics["examples"], "owner": "pipeline_event_logger|pre_submit_delay_tuning",
            "closure_test": "new exact raw_compact_summary and route_bound quote receipts",
            "notified_status": (old.get("notified_status") if set(semantics["issues"]) <= set(old.get("issues") or {})
                                else None)}
    elif (old.get("status") in {"active", "historical_unresolved"} and semantics["status"] == "observed_no_gap"
          and all(semantics["healthy_by_scope"].get(scope, 0)
                  for scope in old.get("issues_by_scope", {}))
          and old.get("issues_by_scope")
          and semantics["sources"]["raw"] == "complete"
          and semantics["sources"]["summary"] == "complete"
          and semantics["sources"]["compact"] == "complete"):
        result["incidents"][key] = {**old, "status": "recovered", "last_seen": result["as_of"],
                                    "historical_source_repaired": False}
    elif old.get("status") == "active" and semantics["status"] == "observed_no_gap":
        result["incidents"][key] = {**old, "status": "historical_unresolved", "last_seen": result["as_of"]}
    item = result["incidents"].get(key, {})
    if item.get("status") in {"active", "recovered"} and item.get("notified_status") != item["status"]:
        result["notification_pending"].append(key)


ECONOMIC_STAGES = frozenset({"entry_ai_economic_plan_observed", "entry_ai_economic_source_gap"})


def economic_evidence(fields, stock_code=None):
    """Project frozen producer proof, without replay, account reads or inferred values."""
    from src.engine.scalping.strategy_owner_replay import _entry_seed_valid, entry_conditional_capital_envelope
    from src.engine.scalping.strategy_owner_components import digest

    status = fields.get("entry_economic_source_status")
    blocker = str(fields.get("entry_economic_source_blocker") or "")
    result = {"status": status, "blocker": blocker or None,
        "capacity_blocker": fields.get("entry_economic_capacity_blocker") or None,
        "owner": fields.get("entry_economic_source_owner") or "main_entry_execution_owners",
        "closure_test": fields.get("entry_economic_source_closure_test") or "exact frozen plan/cost/capital source reaches evaluator",
        "plan_sha256": fields.get("entry_economic_plan_sha256"), "valid_economics": False}
    guard = fields.get("entry_economic_guard_receipt")
    if isinstance(guard, str):
        try:
            guard = json.loads(guard)
        except (ValueError, TypeError):
            guard = None
    if isinstance(guard, dict):
        result["observation_guard"] = guard
    if status != "recorded_source_only":
        if blocker.startswith("common_guard_block:") or blocker == "owner_sizing_zero_or_invalid":
            result["status"] = "guard_excluded"
        elif status == "unsupported_scope":
            result["status"] = "unsupported_scope"
        else:
            result["status"] = "source_gap"
            result["blocker"] = blocker or "economic_producer_status_missing"
        return result
    try:
        seed = fields.get("entry_opportunity_replay_seed")
        seed = json.loads(seed) if isinstance(seed, str) else seed
        if isinstance(seed, dict) and seed.get('schema') == 'entry_probe_conditional_plan_v1':
            from src.engine.scalping.entry_probe_conditional_replay import valid_seed, operating_source_gaps
            if (not valid_seed(seed)
                or seed['plan_sha256'] != fields.get('entry_execution_sizing_plan_sha256')
                or seed['plan_sha256'] != fields.get('entry_economic_plan_sha256')
                or seed['plan_sha256'] != fields.get('entry_economic_writer_plan_sha256')
                or seed['evaluation_attempt_id'] != fields.get('evaluation_attempt_id')
                or seed['scanner_promotion_id'] != fields.get('scanner_promotion_id')
                or (stock_code and stock_code != seed['stock_code'])
                or seed['effective_venue'] != fields.get('effective_venue')
                or seed['session_bucket'] != (fields.get('session_bucket') or fields.get('market_session_bucket'))):
                raise ValueError('economic_conditional_seed_binding_invalid')
            result.update(status='recorded_conditional_source_only',
                blocker='conditional_execution_outcome_not_observed', seed_sha256=seed['seed_sha256'],
                evaluation_role='frozen_conditional_plan_not_paired_economics')
            result['operating_source_gaps'] = operating_source_gaps(seed)
            return result
        if not _entry_seed_valid(seed) or seed.get("plan_sha256") != fields.get("entry_execution_sizing_plan_sha256"):
            raise ValueError("economic_seed_or_plan_binding_invalid")
        for key, field in (("scanner_promotion_id", "scanner_promotion_id"),
                           ("evaluation_attempt_id", "evaluation_attempt_id")):
            if seed.get(key) != fields.get(field):
                raise ValueError("economic_attempt_binding_invalid:" + key)
        if stock_code and seed.get("stock_code") != stock_code:
            raise ValueError("economic_symbol_binding_invalid")
        if fields.get("entry_economic_plan_sha256") != seed.get("plan_sha256"):
            raise ValueError("economic_published_plan_hash_mismatch")
        context = seed.get("operating_contract") or {}
        if not context or context.get("sha256") != digest({k:v for k,v in context.items() if k != "sha256"}):
            raise ValueError("economic_operating_contract_missing_or_hash_invalid")
        for name in ("cost_provenance", "cost_policy_version", "exit_policy_version", "initial_fill_exit_state", "order_leg_ttl_sec"):
            if not context.get(name):
                raise ValueError("economic_operating_field_missing:" + name)
        if any(type(context.get(k)) not in (int, float) or not math.isfinite(context[k])
               for k in ("budget_krw", "cost_rate")) or not 0 <= context["cost_rate"] < 1:
            raise ValueError("economic_budget_or_cost_invalid")
        if not 0 < sum(x["qty"] * x["price"] for x in seed["legs"]) <= context["budget_krw"]:
            raise ValueError("economic_frozen_reserve_budget_invalid")
        capital = context.get("capital_source") or {}
        if capital.get("status") != "recorded_source_only":
            raise ValueError("economic_capital_source:" + str(capital.get("blocker") or "missing"))
        if capital.get("sha256") != digest({k:v for k,v in capital.items() if k != "sha256"}):
            raise ValueError("economic_capital_source_hash_invalid")
        entry_conditional_capital_envelope([seed])
        result.update(status="recorded_source_only", blocker=None, seed_sha256=seed["seed_sha256"],
                      capital_source_sha256=capital["sha256"], evaluation_role="source_contract_only_not_model_validation")
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        result.update(status="source_gap", blocker=str(exc))
    return result


def async_disposition_coverage(events, as_of, *, pass_projections=(), source_coverage=None):
    """Count exact retained PASS attempts per PID/start; never infer missing finals."""
    now = stamp(as_of)
    attempts = {}
    retained = []
    retained_fingerprints = set()
    identity_fields = ('evaluation_attempt_id', 'ai_decision_trace_id', 'scanner_generation_id',
        'native_event_id', 'native_signal_id', 'effective_venue', 'async_order_venue', 'async_origin_snapshot_id',
        'entry_machine_bundle_sha256', 'entry_auxiliary_policy_sha256',
        'watch_origin', 'watch_admission_id', 'watch_generation_id', 'scanner_promotion_id',
        'async_origin_deadline_epoch')
    missing = {'', '-', 'none', 'null', 'unknown'}
    from types import SimpleNamespace
    sources = list(events) + [SimpleNamespace(stage='entry_async_disposition',
        emitted_at=p.get('emitted_at'), stock_code=p.get('stock_code'), fields=p.get('fields') or {})
        for p in pass_projections]
    for event in sources:
        emitted = stamp(event.emitted_at)
        if event.stage != 'entry_async_disposition' or now is None or emitted is None or emitted > now:
            continue
        f = event.fields
        occurred = f.get('async_disposition_epoch')
        try:
            at = datetime.fromtimestamp(float(occurred), tz=now.tzinfo) if occurred not in (None, '') else emitted
        except (ValueError, TypeError, OverflowError, OSError):
            continue
        if at > now or (now-at).total_seconds() > SOURCE_WINDOW_SEC:
            continue
        identity = tuple(str(f.get(k) or '') for k in
                         ('async_producer_pid', 'async_producer_start_ticks', 'async_request_id'))
        if any(v.lower().strip() in {'', '-', 'none', 'null', 'unknown', '0'} for v in identity):
            continue
        row = attempts.setdefault(identity, {'events': {}, 'conflict': False, 'binding': {},
                                              'post_entry': {}})
        for key in (*identity_fields, 'stock_code'):
            value = event.stock_code if key == 'stock_code' else f.get(key)
            if str(value or '').strip().lower() in missing:
                continue  # Early unavailable IDs never borrow current stock IDs.
            if key == 'async_origin_deadline_epoch':
                try:
                    value = float(value)
                    if not math.isfinite(value):
                        raise ValueError()
                except (ValueError, TypeError):
                    row['conflict'] = True
                    continue
            value = str(value)
            if key in row['binding'] and row['binding'][key] != value:
                row['conflict'] = True
            row['binding'][key] = value
        eid = f.get('async_disposition_event_id')
        content = (f.get('async_disposition'), f.get('async_disposition_reason'),
                   f.get('async_machine_action'), f.get('async_auxiliary_status'),
                   f.get('async_auxiliary_verdict'), f.get('async_provider_called'),
                   f.get('async_origin_deadline_epoch'), f.get('ai_decision_trace_id'),
                   f.get('evaluation_attempt_id'), f.get('scanner_generation_id'),
                   f.get('async_disposition_epoch'), f.get('async_entry_submit_attempt_id'),
                   f.get('async_entry_broker_attempts'), f.get('async_entry_broker_accepted'),
                   f.get('async_entry_submit_outcome'))
        if not eid or eid in row['events'] and row['events'][eid] != content:
            row['conflict'] = True
        row['events'][eid] = content
        row['pass'] = row.get('pass', False) or (
            str(f.get('async_machine_action')).upper() == 'ENTER_NOW'
            and str(f.get('async_auxiliary_status')).lower() == 'pass'
            and str(f.get('async_auxiliary_verdict')).upper() == 'PASS'
            and str(f.get('async_provider_called')).lower() == 'true')
        row['deadline'] = row['binding'].get('async_origin_deadline_epoch')
        if f.get('async_disposition') == 'entry_path_returned':
            post_entry = {k: f.get(k) for k in (
                'async_disposition_reason', 'async_entry_submit_attempt_id',
                'async_entry_broker_attempts', 'async_entry_broker_accepted', 'async_entry_submit_outcome')}
            if row['post_entry'] and row['post_entry'] != post_entry:
                row['conflict'] = True
            row['post_entry'] = post_entry
        projection = dict(emitted_at=event.emitted_at, stock_code=event.stock_code,
            fields={k: f.get(k) for k in (*identity_fields,
                'async_producer_pid', 'async_producer_start_ticks', 'async_request_id',
                'async_disposition_event_id', 'async_disposition', 'async_disposition_reason',
                'async_disposition_epoch', 'async_machine_action', 'async_auxiliary_status',
                'async_auxiliary_verdict', 'async_provider_called',
                'async_entry_submit_attempt_id', 'async_entry_broker_attempts',
                'async_entry_broker_accepted', 'async_entry_submit_outcome')})
        fingerprint = json.dumps(projection, sort_keys=True, default=str)
        if fingerprint not in retained_fingerprints:
            retained_fingerprints.add(fingerprint)
            retained.append(projection)
    by_producer = {}
    for identity, row in attempts.items():
        if not row.get('pass'):
            continue
        counts = by_producer.setdefault(':'.join(identity[:2]),
            dict(pass_count=0, accepted=0, rejected=0, pending=0, unobservable=0,
                 accepted_submit_observed=0, accepted_direct_guard=0, accepted_post_entry_unobservable=0))
        states = {entry[0] for entry in row['events'].values()}
        finals = states & {'accepted_to_entry_path', 'rejected', 'terminal_nonexecution'}
        if row['conflict'] or len(finals) > 1:
            status = 'unobservable'
        elif finals:
            status = 'accepted' if 'accepted_to_entry_path' in finals else 'rejected'
        else:
            try:
                deadline = float(row['deadline'])
                status = 'pending' if math.isfinite(deadline) and now.timestamp() < deadline else 'unobservable'
            except (TypeError, ValueError):
                status = 'unobservable'
        counts['pass_count'] += 1
        counts[status] += 1
        if status == 'accepted':
            post = row['post_entry']
            if str(post.get('async_entry_broker_attempts') or '0').isdigit() and int(post.get('async_entry_broker_attempts') or 0) > 0:
                counts['accepted_submit_observed'] += 1
            elif post.get('async_disposition_reason') not in (None, '',
                    'entry_path_returned_without_terminal_evidence', 'entry_execution_exception_or_uncertain'):
                counts['accepted_direct_guard'] += 1
            else:
                counts['accepted_post_entry_unobservable'] += 1
    return dict(schema='main_async_disposition_coverage_v1', by_producer=by_producer,
        metric_role='source_quality_gate', decision_authority='report_only',
        primary_decision_metric='pass_to_main_disposition_coverage',
        window_policy='current_pid_exact_attempt_with_carry_in_out', sample_floor='none',
        source_quality_gate='exact_pid_start_request_and_validated_pass',
        coverage=('bounded_trace_projection_complete' if source_coverage == 'complete'
                  and len(retained) <= 1024 else 'loaded_evidence_only_full_denominator_unobservable'),
        denominator_partial=source_coverage != 'complete' or len(retained) > 1024,
        attempt_projection=retained[-1024:],
        forbidden_uses=['order_authority', 'policy_promotion', 'economics'])


def snapshot(events, as_of):
    """Reuse already loaded events and the existing identity/terminal owner."""
    from src.engine.buy_funnel_sentinel import (
        _machine_primary_entry_funnel, _is_machine_primary_event, _machine_primary_evaluation_key,
        _machine_primary_identity_components, _machine_primary_fixed_watch_identity_components,
        _machine_primary_fixed_watch_identity_valid,
    )

    now = stamp(as_of)
    recent = [e for e in events if 0 <= (now - stamp(e.emitted_at)).total_seconds() <= 2700]
    funnel = _machine_primary_entry_funnel(recent)
    missing_rows = []
    historical_samples = []
    identified_clocks = []
    fixed_watch_clocks = []
    fixed_watch_evidence = []
    def identity_evidence_id(event):
        return hashlib.sha256(repr((event.emitted_at, event.stage, event.stock_code,
            event.record_id, sorted(event.fields.items()))).encode()).hexdigest()
    # Reuse already loaded cache rows for legacy incident metadata only; no
    # second raw scan or historical funnel/recovery calculation. Bound output.
    for e in events:
        at = stamp(e.emitted_at)
        if at.date() != now.date() or at > now:
            continue
        if e.pipeline != "ENTRY_PIPELINE" or not _is_machine_primary_event(e):
            continue
        fixed_watch = str(e.fields.get("watch_origin") or "").strip() == "MAIN_FIXED_WATCH"
        if fixed_watch and _machine_primary_fixed_watch_identity_valid(e):
            fixed_watch_evidence.append((at, identity_evidence_id(e)))
            if (now - at).total_seconds() <= 2700:
                fixed_watch_clocks.append(at)
            continue
        if not fixed_watch and _machine_primary_evaluation_key(e):
            if (now - at).total_seconds() <= 2700:
                identified_clocks.append(at)
            continue
        detail = dict(
            evidence_id=identity_evidence_id(e),
            occurred_at=at.isoformat(), stock_code=e.stock_code, stage=e.stage,
            record_id=e.record_id,
            missing_fields=[k for k, v in (
                _machine_primary_fixed_watch_identity_components(e) if fixed_watch
                else _machine_primary_identity_components(e)).items()
                if not v or v.lower() in {"none", "null", "unknown", "-", "0"}],
            conflicting_fields=["scanner_promotion_id"] if fixed_watch and
                str(e.fields.get("scanner_promotion_id") or "").strip().lower()
                not in {"", "none", "null", "unknown", "-", "0"} else [],
            identity_contract_issues=["fixed_watch_admission_generation_invalid"]
                if fixed_watch and not _machine_primary_fixed_watch_identity_valid(e)
                and all(value and value.lower() not in {"none", "null", "unknown", "-", "0"}
                    for value in _machine_primary_fixed_watch_identity_components(e).values())
                else [])
        if (now - at).total_seconds() <= 2700:
            missing_rows.append(detail)
        else:
            historical_samples.append(detail)
            # Keep the most recent old receipts even when input is unsorted.
            if len(historical_samples) > 128:
                historical_samples.sort(key=lambda r: (r['occurred_at'], r['evidence_id']))
                historical_samples.pop(0)
    missing_rows.sort(key=lambda row: (row["occurred_at"], row["evidence_id"]))
    retained_missing = [r for r in missing_rows
        if (now - stamp(r["occurred_at"])).total_seconds() <= WINDOW_SEC]
    current_missing = [r for r in missing_rows
        if (now - stamp(r["occurred_at"])).total_seconds() < GRACE_SEC]
    current_identified = [at for at in identified_clocks if (now - at).total_seconds() < GRACE_SEC]
    identity_observation = dict(schema="machine_identity_recency_v1", window_sec=GRACE_SEC,
        status="current_gap" if current_missing else "no_recurrence_observed" if current_identified else "unobservable",
        missing_event_count=len(current_missing), identified_event_count=len(current_identified),
        current_missing_first_at=current_missing[0]["occurred_at"] if current_missing else None,
        current_missing_last_at=current_missing[-1]["occurred_at"] if current_missing else None,
        latest_identified_at=max(current_identified).isoformat() if current_identified else None,
        missing_first_at=missing_rows[0]["occurred_at"] if missing_rows else None,
        missing_last_at=missing_rows[-1]["occurred_at"] if missing_rows else None,
        examples=current_missing[:3])
    economic = {}
    economic_by_revision = {}
    chain_status = {r["evaluation_key"]: r["revision_chain_status"] for r in funnel["evaluation_ledger"]}
    economic_history = defaultdict(list)
    confirmations = {}
    for e in sorted(recent, key=lambda event: stamp(event.emitted_at)):
        if e.fields.get('entry_machine_confirmation_sha256'):
            confirmation_key = (_machine_primary_evaluation_key(e), e.fields.get('machine_observation_sha256'))
            if all(confirmation_key):
                confirmations[confirmation_key] = {key: e.fields.get(key) for key in (
                    'entry_machine_confirmation_sha256', 'entry_machine_confirmation_recipe_id',
                    'entry_machine_confirmation_source_sha256', 'entry_machine_confirmation_policy_sha256')}
        if e.stage not in ECONOMIC_STAGES:
            continue
        if str(e.fields.get("watch_origin") or "").strip() == "MAIN_FIXED_WATCH":
            continue
        key = _machine_primary_evaluation_key(e)
        if key:
            value = e.fields.get("economic_source_monitor_projection")
            value = json.loads(value) if isinstance(value, str) else value
            value = value if isinstance(value, dict) else economic_evidence(e.fields, e.stock_code)
            # Older slim-cache projections omitted this diagnostic, but the
            # original field was retained. No raw rescan or proof regeneration.
            value = {**value, "capacity_blocker": e.fields.get("entry_economic_capacity_blocker")
                     or value.get("capacity_blocker")}
            observation = {"observed_at": stamp(e.emitted_at).isoformat(), "stage": e.stage,
                "mechanistic_action": e.fields.get("entry_mechanistic_action"),
                "machine_observation_sha256": e.fields.get("machine_observation_sha256"),
                "evidence": dict(value)}
            if observation not in economic_history[key]:
                economic_history[key].append(observation)
            revision_key = (key, e.fields.get("machine_observation_sha256")) if chain_status.get(key) == "valid" else (key, None)
            old = economic_by_revision.get(revision_key, {})
            if (old.get("blocker") == "economic_observation_conflicting_proofs"
                or old.get("status") == value.get("status") == "recorded_source_only"
                and old.get("seed_sha256") != value.get("seed_sha256")):
                value = {**old, "status": "source_gap", "blocker": "economic_observation_conflicting_proofs"}
            economic_by_revision[revision_key] = value
            economic[key] = value
    for row in funnel["evaluation_ledger"]:
        confirmation_hash = ((row.get('decision_history') or [{}])[-1].get('machine_observation_sha256')
                             if row['revision_chain_status'] in {'valid', 'single_revision'} else None)
        row['recipe_confirmation_evidence'] = confirmations.get(
            (row['evaluation_key'], confirmation_hash))
        row["economic_history"] = economic_history.get(row["evaluation_key"], [])
        feature_guard = (row["mechanistic_action"] == "RECHECK"
                         and row["ai_screen_status"] == "not_requested_required_feature_insufficient"
                         and not row["conflict_reasons"])
        row["economic_source"] = economic.get(row["evaluation_key"], {
            "status": ("guard_excluded" if feature_guard else
                       "not_applicable_machine_source_invalid" if row["mechanistic_action"] not in {"ENTER_NOW", "BLOCK", "RECHECK"}
                       else "source_gap" if stamp(row["first_evaluated_at"]).date().isoformat() >= "2026-09-21" else "historical_not_required"),
            "blocker": ("required_feature_input_insufficient" if feature_guard else
                        "economic_observation_event_missing"
                        if row["mechanistic_action"] in {"ENTER_NOW", "BLOCK", "RECHECK"}
                        else None),
            "owner": "main_entry_execution_owners->pipeline_event_logger->sentinel_cache",
            "closure_test": "same exact attempt publishes its pre-AI economic observation"})
        if row["revision_chain_status"] == "valid":
            missing = {"status": "source_gap", "blocker": "economic_observation_event_missing",
                "owner": "main_entry_execution_owners->pipeline_event_logger->sentinel_cache",
                "closure_test": "same exact revision publishes its pre-AI economic observation"}
            final_hash = row["decision_history"][-1]["machine_observation_sha256"]
            row["economic_source"] = economic_by_revision.get((row["evaluation_key"], final_hash), missing)
            # A later revision's success cannot retrospectively repair an
            # earlier ENTER_NOW's missing proof. Guard exclusions are separate.
            for observed in row["decision_history"]:
                proof = economic_by_revision.get((row["evaluation_key"], observed["machine_observation_sha256"]), missing)
                if observed["action"] == "ENTER_NOW" and proof.get("status") == "source_gap":
                    row["economic_source"] = {**proof, "machine_observation_sha256": observed["machine_observation_sha256"]}
                    break
    return {
        "schema": SCHEMA, "as_of": now.isoformat(),
        "async_disposition_coverage": async_disposition_coverage(events, as_of),
        "latest_event_at": max((stamp(e.emitted_at) for e in recent), default=now - timedelta(days=1)).isoformat(),
        "auxiliary_ai_semantic_status_counts": funnel.get("auxiliary_ai_semantic_status_counts", {}),
        "auxiliary_ai_semantic_issue_counts": funnel.get("auxiliary_ai_semantic_issue_counts", {}),
        "identity_missing_events": funnel["evaluation_identity_missing_event_count"],
        "fixed_watch_identified_evidence": [evidence for _, evidence in
            sorted(fixed_watch_evidence, reverse=True)[:256]],
        "fixed_watch_identity_observation": {
            "schema": "fixed_watch_source_identity_v1",
            "metric_role": "source_quality_gate", "decision_authority": "report_only",
            "window_policy": "current_45_minutes", "sample_floor": "none_for_source_identity",
            "primary_decision_metric": "identified_event_count",
            "source_quality_gate": "exact_watch_admission_generation_attempt_scope_bundle",
            "forbidden_uses": ["scanner_promotion_denominator", "submission_state",
                "order_authority", "economic_acceptance"],
            "identified_event_count": len(fixed_watch_clocks),
            "identity_missing_event_count": funnel["fixed_watch_identity_missing_event_count"],
            "latest_identified_at": max(fixed_watch_clocks).isoformat() if fixed_watch_clocks else None,
        },
        "rows": [{k: r[k] for k in (
            "evaluation_key", "scanner_promotion_id", "stock_code", "effective_venue",
            "session_bucket", "policy_bundle_hash", "first_evaluated_at", "last_event_at",
            "mechanistic_action", "ai_screen_status", "auxiliary_ai_semantics", "broker_acceptance_observed",
            "final_guard_blocked", "final_guard_evidence", "final_state", "conflict_reasons", "source_invalid_decomposition", "economic_source",
            "decision_history", "initial_observed_action", "latest_observed_action",
            "enter_now_observed", "economic_history", "revision_chain_status",
            "recipe_confirmation_evidence",
        )} for r in funnel["evaluation_ledger"]],
        "missing_identity_evidence": sorted({r["evidence_id"] for r in retained_missing}),
        "missing_identity_examples": retained_missing[:3],
        "missing_identity_first_at": retained_missing[0]['occurred_at'] if retained_missing else None,
        "missing_identity_last_at": retained_missing[-1]['occurred_at'] if retained_missing else None,
        "historical_identity_samples": historical_samples,
        "identity_observation": identity_observation,
    }


def _nonentry_capacity_observation_gap(row):
    """Only explicit no-fetch non-entry misses are coverage, not submit faults."""
    economic = row.get("economic_source") or {}
    return (row.get("mechanistic_action") in {"BLOCK", "RECHECK"}
            and row.get("ai_screen_status") == "not_requested_machine_nonentry"
            and not row.get("conflict_reasons")
            and _latest_nonentry_economics(row)
            and not row.get("broker_acceptance_observed")
            and row.get("final_state") in {"machine_block_point_drop", "machine_recheck_observation"}
            and economic.get("status") == "source_gap"
            and economic.get("blocker") == "exact_broker_capacity_missing"
            and economic.get("capacity_blocker") == "capacity_observation_cache_miss_nonentry")


def _nonentry_downstream_gap(row):
    """An uncalled execution replay is not a machine admission contract."""
    return (row.get("mechanistic_action") in {"BLOCK", "RECHECK"}
            and row.get("ai_screen_status") == "not_requested_machine_nonentry"
            and not row.get("conflict_reasons") and _latest_nonentry_economics(row)
            and not row.get("broker_acceptance_observed")
            and row.get("final_state") in {"machine_block_point_drop", "machine_recheck_observation"}
            and (row.get("economic_source") or {}).get("status") == "source_gap")


def _latest_nonentry_economics(row):
    """A valid later machine revision can supersede an earlier ENTER_NOW."""
    if not row.get("enter_now_observed"):
        return True
    decisions = row.get("decision_history") or []
    economics = row.get("economic_history") or []
    if (row.get("revision_chain_status") != "valid"
            or row.get("latest_observed_action") != row.get("mechanistic_action")
            or not decisions or not economics):
        return False
    latest_decision, latest_economic = decisions[-1], economics[-1]
    return bool(
        latest_decision.get("action") == row.get("mechanistic_action")
        and latest_economic.get("mechanistic_action") == row.get("mechanistic_action")
        and latest_decision.get("machine_observation_sha256")
        and latest_decision.get("machine_observation_sha256")
        == latest_economic.get("machine_observation_sha256")
        and latest_economic.get("evidence") == row.get("economic_source")
    )


def _small_json(path):
    if path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("semantic_artifact_size_limit")
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError("semantic_artifact_invalid")
    return value


def _reversal_selection_receipt(bundle, data_root):
    """Read the issued family and its frozen reports, without legacy score gates."""
    from src.engine.scalping.continuous_reversal_policy import validate_sources

    validate_sources(bundle, data_root)
    family = bundle['continuous_reversal']
    if (family.get('effective_date') != bundle.get('target_date')
            or family.get('source_date') != bundle.get('source_date')
            or family.get('publication_date') != bundle.get('publication_date')):
        raise ValueError('reversal_selection_date_binding_invalid')
    selections = {}
    expanded = [(key+'|'+route,value) for key,cell in family['machine_cells'].items() for route,value in cell.get('routes',{}).items()] if family['schema'] in {'continuous_reversal_policy_v3','continuous_reversal_policy_v4','continuous_reversal_policy_v5','continuous_reversal_policy_v6'} else list(family['machine_cells'].items())
    for key, cell in expanded:
        metrics = cell.get('local_metrics')
        selections[key] = dict(
            version=family['selection_metric'], score_contract_valid=True,
            payload=cell['payload'], payload_sha256=cell['payload_sha256'],
            inherited_from=cell.get('inherited_from'), local_metrics=metrics,
            win_rate_pct=(100 * metrics['wins'] / metrics['resolved']) if metrics else None,
            realized_pnl=False, report_is_activation_receipt=False,
        )
    return selections


def _reversal_observation_receipt(bundle, observation, *, verified_components=None):
    """Validate captured reversal identity, rule and verdict against its family."""
    from src.engine.scalping import continuous_reversal as kernel
    from src.engine.scalping.continuous_reversal_policy import validate_family
    from src.engine.scalping.mechanistic_entry_runtime_policy import digest

    family = bundle['continuous_reversal']
    if family.get('schema') in {'continuous_reversal_policy_v5','continuous_reversal_policy_v6'}:
        from src.engine.scalping.reversal_auxiliary_intraday import audit_observation
        return audit_observation(bundle,observation)
    is_v4=family.get('schema')=='continuous_reversal_policy_v4'
    is_v3=family.get('schema') in {'continuous_reversal_policy_v3','continuous_reversal_policy_v4'}
    is_v2=family.get('schema') in {'continuous_reversal_policy_v2','continuous_reversal_policy_v3','continuous_reversal_policy_v4'}
    if verified_components is None:
        validate_family(family)
        verified_components = dict(machine=digest(family['machine_cells']),
                                   auxiliary=digest(family['auxiliary_cells']))
    context, source = observation['label_context'], observation['source']
    assessment, receipt = source['assessment'], observation['runtime_consumption']
    raw = source.get('exact_payload')
    if not isinstance(raw, dict) or not raw:
        raise ValueError('reversal_exact_payload_missing')
    symbol = str(context['stock_code'])
    session = context['session_bucket']
    captured = stamp(observation['captured_at'])
    if (str(raw.get('stock_code')) != symbol
            or kernel.market_bucket(raw.get('session_bucket')) != kernel.market_bucket(session)
            or raw.get('evaluation_attempt_id') != context.get('evaluation_attempt_id')
            or not context.get('evaluation_attempt_id')
            or bundle.get('target_date') != captured.date().isoformat()):
        raise ValueError('reversal_observation_identity_invalid')
    observed_epoch = raw.get('entry_machine_input_as_of')
    if (not isinstance(observed_epoch, (int, float)) or not math.isfinite(observed_epoch)
            or observed_epoch > captured.timestamp()):
        raise ValueError('reversal_observation_source_time_invalid')
    if (receipt.get('bundle_sha256') != bundle['bundle_sha256']
            or any(receipt.get(k) is not None for k in
                   ('policy_sha256', 'selector_leaf', 'effective_thresholds'))):
        raise ValueError('effective_policy_receipt_mismatch')
    if (assessment.get('schema') != 'mechanistic_entry_policy_decision_v1'
            or assessment.get('policy_version') != (family['schema'] if is_v2 else kernel.VERSION)
            or assessment.get('primary_decision_owner') != 'mechanistic_entry_adjudicator'
            or assessment.get('ai_role') != 'auxiliary_risk_screen_pass_veto_no_promotion'):
        raise ValueError('reversal_assessment_contract_invalid')
    component = verified_components['machine']
    native = receipt.get('continuous_reversal')
    if observation.get('capture_contract') == 'continuous_reversal_consumption_v1' and native is None:
        raise ValueError('reversal_native_consumption_receipt_missing')
    if native is not None:
        from src.engine.scalping.ai_decision_trace import _json_bytes
        expected = dict(schema='continuous_reversal_consumption_v1',
            family_sha256=family['family_sha256'], bundle_sha256=bundle['bundle_sha256'],
            source_date=family['source_date'], publication_date=family['publication_date'],
            effective_date=family['effective_date'], machine_component_sha256=component,
            auxiliary_component_sha256=verified_components['auxiliary'],
            event_id=assessment.get('event_id'), cell_key=assessment.get('cell_key'),
            rule=assessment.get('rule'), pid=receipt.get('pid'),
            process_start_ticks=receipt.get('process_start_ticks'), captured_at=observation['captured_at'],
            exact_payload_sha256=hashlib.sha256(_json_bytes(raw)).hexdigest(),
            assessment_sha256=hashlib.sha256(_json_bytes(assessment)).hexdigest())
        if not isinstance(native, dict) or any(native.get(k) != v for k, v in expected.items()):
            raise ValueError('reversal_native_consumption_receipt_mismatch')
        clock = native.get('snapshot_read_at')
        if (not isinstance(clock, (int, float)) or not math.isfinite(clock)
                or not observed_epoch <= clock <= captured.timestamp()):
            raise ValueError('reversal_snapshot_read_clock_invalid')
        key = assessment.get('cell_key')
        if is_v2:
            phase=assessment.get('decision_phase')
            arm=(family['auxiliary_cells'][key]['routes'][assessment['route']]['payload']['branch_policies'][assessment['primary_branch']]['arm'] if is_v3 and key and assessment.get('primary_branch') else family['auxiliary_cells'][key]['payload']['phase_policies'][phase]['arm'] if not is_v3 and key and phase else None)
            for field in ('primary_branch','matched_branches','signal_id','branch_definition_sha256'):
                if native.get(field)!=assessment.get(field):raise ValueError('reversal_branch_receipt_mismatch:'+field)
            if native.get('phase')!=assessment.get('decision_phase','FIRST_UPTICK'):
                raise ValueError('reversal_phase_receipt_mismatch')
        else:arm = family['auxiliary_cells'][key]['payload']['arm'] if key else None
        if native.get('arm') != arm:
            raise ValueError('reversal_auxiliary_arm_receipt_mismatch')
        if assessment.get('action') == 'ENTER_NOW':
            from src.engine.scalping.reversal_auxiliary_contract import production_prompt, response_schema, ARMS
            if any(not isinstance(native.get(k), str) or len(native[k]) != 64
                   for k in ('input_sha256', 'prompt_sha256', 'response_schema_sha256')):
                raise ValueError('reversal_auxiliary_request_hash_missing')
            request = source.get('auxiliary_request')
            if not isinstance(request, dict) or any(
                    digest(request.get(k)) != native.get(v) for k, v in (
                        ('input', 'input_sha256'), ('prompt', 'prompt_sha256'),
                        ('response_schema', 'response_schema_sha256'))):
                raise ValueError('reversal_auxiliary_request_hash_mismatch')
            inp = request['input']
            expected_prompt=production_prompt(arm)
            expected_schema=response_schema(inp,complete_source_only=arm==ARMS[-1])
            if is_v2:
                from src.engine.scalping import reversal_auxiliary_phases as phases
                if is_v4:
                    from src.engine.scalping import reversal_path_auxiliary as phases
                expected_prompt=phases.prompt(phase,arm)
                if is_v4 and phase in phases.PHASES:
                    phases.validate_input_signal(inp,assessment['auxiliary_event'])
                    expected_schema['properties']['risk_codes']['minItems']=1
                    if (inp.get('signal_kind')!=phase or inp.get('mechanistic_entry_assessment',{}).get('machine_signal_confirmed') is not True
                            or 'price_reversal_confirmed' in inp.get('mechanistic_entry_assessment',{})):
                        raise ValueError('path_auxiliary_signal_contract_mismatch')
                if phase=='CONFIRMED_UPTICK':
                    expected_schema['properties']['risk_codes']['minItems']=1
                    e=assessment['event'];timeline=inp.get('observation_phase',{})
                    if (timeline.get('stage')!=phase or timeline.get('rolling_windows_end')!='AT_CONFIRMATION'
                            or timeline.get('original_first_uptick')!=dict(id=e['anchor_event_id'],as_of=e['anchor_epoch'],price=e['anchor_price'])
                            or timeline.get('additional_higher_trade')!=dict(id=e['event_id'],as_of=e['epoch'],price=e['confirmation_price'])):
                        raise ValueError('reversal_confirmation_timeline_mismatch')
            if (request['prompt'] != expected_prompt
                    or request['response_schema'] != expected_schema
                    or inp.get('objective') != dict(net_target_pct=.4, net_soft_stop_pct=-3.,
                                                    horizon_seconds=1800, cost_rate=.0023)):
                raise ValueError('reversal_auxiliary_issued_contract_mismatch')
            facts = inp['entry_setup_evidence_v1']['facts']
            auxiliary_event=(assessment.get('auxiliary_event') or assessment['event']) if is_v2 else assessment['event']
            if any(facts.get(k) != auxiliary_event.get(k) for k in (
                    'confirmation_price', 'entry_ask', 'low_price', 'drop_pct',
                    'drawdown_5m_pct', 'down_steps', 'spread_pct', 'volume_ratio_60s')):
                raise ValueError('reversal_auxiliary_event_input_mismatch')
        elif any(native.get(k) is not None for k in ('input_sha256', 'prompt_sha256', 'response_schema_sha256')):
            raise ValueError('reversal_nonentry_provider_receipt_invalid')
    event = assessment.get('event')
    if event is None:
        if (assessment.get('action') != 'BLOCK'
                or assessment.get('reason') != ('no_current_reversal_signal' if is_v2 else 'no_current_first_uptick')
                or assessment.get('price_reversal_confirmed') is not False
                or any(assessment.get(k) is not None for k in ('cell_key', 'rule', 'event_id'))):
            raise ValueError('reversal_nonturn_receipt_invalid')
        return {}, dict(policy_sha256=component, leaf='NO_CURRENT_FIRST_UPTICK')
    if (not isinstance(event, dict) or event.get('symbol') != symbol
            or event.get('market') != kernel.market_bucket(session)
            or assessment.get('event_id') != event.get('event_id')
            or (assessment.get('machine_signal_confirmed') is not True if is_v4 else assessment.get('price_reversal_confirmed') is not True)):
        raise ValueError('reversal_event_identity_invalid')
    if (not isinstance(event.get('epoch'), (int, float))
            or not math.isfinite(event['epoch']) or event['epoch'] > (
                native['snapshot_read_at'] if native else captured.timestamp())
            or not isinstance(event.get('source_item'), str)
            or event['source_item'].split('_', 1)[0] != symbol):
        raise ValueError('reversal_event_source_invalid')
    key = kernel.cell_key(symbol, session, event['confirmation_price'])
    if is_v3:
        from src.engine.scalping.reversal_registered_catalog import cell_key
        key=cell_key(symbol,session,event['confirmation_price'])
    if is_v2:
        from src.engine.scalping.continuous_reversal_policy_v2 import assess
        if is_v3:
            from src.engine.scalping.continuous_reversal_policy_v3 import assess
        if is_v4:
            from src.engine.scalping.continuous_reversal_policy_v4 import assess
        replay,_,_,_=assess(family,(event,None),symbol=symbol,session=session,build_request=False)
        for field in ('action','reason','cell_key','event_id','signal_id','matched_branches','branch_states',
                      'primary_branch','decision_phase','auxiliary_arm','auxiliary_event','machine_component_sha256','family_sha256','price_reversal_confirmed',
                      *(['machine_signal_confirmed','signal_kind'] if is_v4 else [])):
            if assessment.get(field)!=replay.get(field):raise ValueError('reversal_v2_branch_verdict_mismatch:'+field)
        return (family['machine_cells'][key]['routes'][assessment['route']]['payload'] if is_v3 else family['machine_cells'][key]['payload']),dict(policy_sha256=component,leaf=key)
    rule = family['machine_cells'][key]['payload']['rule']
    if (assessment.get('cell_key') != key or assessment.get('rule') != rule
            or assessment.get('machine_component_sha256') != component):
        raise ValueError('reversal_selected_cell_receipt_mismatch')
    if event['entry_ask'] is None:
        action, reason = 'RECHECK', 'entry_quote_source_missing'
    elif not kernel.conditions(event)[rule]:
        missing = (('VOL' in rule and event['volume_ratio_60s'] is None)
                   or (rule.startswith('DD5') and event['drawdown_5m_pct'] is None))
        action, reason = ('RECHECK', 'required_reversal_feature_missing') if missing else (
            'BLOCK', 'selected_reversal_condition_not_met')
    else:
        action, reason = 'ENTER_NOW', 'continuous_reversal_cell_pass'
    if assessment.get('action') != action or assessment.get('reason') != reason:
        raise ValueError('reversal_rule_verdict_mismatch')
    return {'rule': rule}, dict(policy_sha256=component, leaf=key)


def machine_semantics(data_root, now, *, tail_bytes=8 * 1024 * 1024):
    """Bounded receipt audit, not a replay, policy publisher or outcome estimator."""
    from src.engine.scalping import entry_strategy_policy as strategy
    from src.engine.scalping import mechanistic_entry_runtime_policy as runtime
    from src.engine.scalping.ai_decision_trace import _json_bytes
    from src.engine.buy_funnel_sentinel import _canonical_session

    now = stamp(now)
    day = now.date().isoformat()
    result = dict(status="unobservable", metric_role="source_quality_gate",
        decision_authority="report_only", window_policy="recent_30m_bounded_tail",
        sample_floor="none_for_receipt_checks", primary_decision_metric="receipt_mismatch_count",
        source_quality_gate="exact_observation_hash_scope_and_frozen_policy",
        forbidden_uses=["automatic_policy_change", "realized_pnl", "missing_as_zero_ev"],
        selection={}, scopes={}, issues={}, examples=[], observation_count=0,
        source_invalid_count=0, required_feature_guard_count=0, source_invalid_blockers={}, action_replay_performed=False)
    issues = Counter()
    try:
        current = runtime.load_effective(data_root=data_root, target_date=day)
        if not current:
            raise ValueError("current_policy_missing")
        result["current_bundle_sha256"] = current["bundle_sha256"]
        if current.get("continuous_reversal"):
            result["selection"] = _reversal_selection_receipt(current, data_root)
            result["selection_family"] = "continuous_reversal"
            result["publication"] = dict(
                source_date=current["source_date"], publication_date=current["publication_date"],
                effective_date=current["target_date"], status="native_frozen_family_verified",
                actual_pid_consumption="see_per_scope_live_pid_receipts")
        else:
            report = _small_json(data_root / "report/ai_decision_action_outcome_calibration" / f"machine_policy_{day}.json")
            digest = runtime.digest({k: v for k, v in report.items() if k != "artifact_content_sha256"})
            if digest != report.get("artifact_content_sha256") or report.get("target_date") != day:
                raise ValueError("selection_artifact_invalid")
            for scope, selected in report.get("selections", {}).items():
                economy = ((selected.get("machine_evidence") or {}).get("train") or {}).get("economics") or {}
                score = strategy.machine_support_adjusted_win_rate(economy)
                recorded = economy.get("support_adjusted_win_rate_pct")
                valid = selected.get("selection_basis") == strategy.MACHINE_SELECTION_VERSION
                if selected.get("promotion_pass"):
                    valid = valid and score is not None and isinstance(recorded, (int, float)) and math.isclose(score, recorded, abs_tol=1e-8)
                result["selection"][scope] = dict(version=selected.get("selection_basis"), score_contract_valid=valid,
                    promotion_pass=selected.get("promotion_pass"), reasons=selected.get("promotion_errors"),
                    unique_opportunities=economy.get("selected_opportunity_count"), win_rate_pct=economy.get("win_rate_pct"),
                    support_adjusted_score_pct=recorded, mean_net_path_ev_pct=economy.get("selected_path_ev_pct"),
                    realized_pnl=False, report_is_activation_receipt=False)
                if not valid:
                    issues["selection_score_contract_invalid"] += 1
            terminal = _small_json(data_root / "report/ai_decision_action_outcome_calibration" / f"machine_policy_terminal_{day}.json")
            if (terminal.get("report_sha256") != report["artifact_content_sha256"]
                    or runtime.digest({k:v for k,v in terminal.items() if k != "artifact_content_sha256"}) != terminal.get("artifact_content_sha256")):
                raise ValueError("selection_terminal_binding_invalid")
            result["publication"] = dict(status=terminal.get("status"), activation=terminal.get("activation"),
                actual_pid_consumption="see_per_scope_live_pid_receipts")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result["selection_status"] = "unobservable:" + str(exc)[:160]
    path = data_root / "ai_decision_payloads" / f"ai_decision_payloads_{day}.jsonl"
    generations, seen = {}, set()
    verified_reversal_generations = {}
    reversal_observations = []
    pid_identities = {}
    try:
        with path.open("rb") as stream:
            before = os.fstat(stream.fileno())
            size = before.st_size
            start = max(0, size - tail_bytes)
            stream.seek(start)
            if start:
                stream.readline()
            result.update(tail_truncated=bool(start), source_bytes=size, read_limit_bytes=tail_bytes)
            payload = stream.read(max(0, size - stream.tell()))
            after = path.stat()
            if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino) or after.st_size < size:
                raise OSError('machine_source_generation_changed_during_read')
            result.update(bytes_read=len(payload), read_count=1,
                          window_coverage='bounded_suffix' if start else 'complete_file_prefix')
            for line in payload.splitlines(keepends=True):
                if not line.endswith(b"\n"):
                    break
                try:
                    observation = json.loads(line)
                except (ValueError, UnicodeDecodeError):
                    issues["observation_json_invalid"] += 1
                    continue
                if not isinstance(observation, dict) or observation.get("schema") != "mechanistic_entry_observation_v1":
                    continue
                at = stamp(observation.get("captured_at"))
                if not at or not 0 <= (now - at).total_seconds() <= WINDOW_SEC:
                    continue
                observed_hash = observation.get("machine_observation_sha256")
                if observed_hash in seen:
                    continue
                seen.add(observed_hash)
                result["observation_count"] += 1
                try:
                    if hashlib.sha256(_json_bytes({k:v for k,v in observation.items() if k != "machine_observation_sha256"})).hexdigest() != observed_hash:
                        raise ValueError("machine_observation_hash_invalid")
                    receipt = observation["runtime_consumption"]
                    bundle_hash = observation["bundle_sha256"]
                    if not isinstance(bundle_hash, str) or len(bundle_hash) != 64 or any(c not in "0123456789abcdef" for c in bundle_hash):
                        raise ValueError("bundle_hash_invalid")
                    if bundle_hash not in generations:
                        bundle = _small_json(runtime.root(data_root) / "generations" / f"{bundle_hash}.json")
                        if runtime.digest({k:v for k,v in bundle.items() if k != "bundle_sha256"}) != bundle_hash:
                            raise ValueError("frozen_bundle_hash_invalid")
                        generations[bundle_hash] = bundle
                    context, source = observation["label_context"], observation["source"]
                    assessment = source.get("assessment") or {}
                    invalid = str(assessment.get("action", "")).upper() == "SOURCE_INVALID"
                    feature_guard = (assessment.get("schema") == "mechanistic_entry_required_feature_v1"
                        and assessment.get("action") == "RECHECK" and assessment.get("reason") == "required_feature_input_insufficient"
                        and (source.get("setup_evidence") or {}).get("source_quality_status") == "blocked")
                    if invalid or feature_guard:
                        result["source_invalid_count" if invalid else "required_feature_guard_count"] += 1
                        for blocker in (source.get("setup_evidence") or {}).get("source_quality_blockers", []):
                            result["source_invalid_blockers"][blocker] = result["source_invalid_blockers"].get(blocker, 0) + 1
                        continue
                    scope = (str(context["effective_venue"]).upper(), _canonical_session(context["session_bucket"]))
                    frozen = generations[bundle_hash]
                    if frozen.get("continuous_reversal"):
                        if bundle_hash not in verified_reversal_generations:
                            _reversal_selection_receipt(frozen, data_root)
                            # Keep verification cache outside the signed bundle.
                            verified_reversal_generations[bundle_hash] = dict(
                                machine=runtime.digest(frozen['continuous_reversal']['machine_cells']),
                                auxiliary=runtime.digest(frozen['continuous_reversal']['auxiliary_cells']))
                        profile, selection = _reversal_observation_receipt(frozen, observation,
                            verified_components=verified_reversal_generations[bundle_hash])
                        reversal_observations.append(observation)
                    else:
                        scoped = runtime.for_cohort(generations[bundle_hash], scope)
                        if not scoped:
                            raise ValueError("frozen_policy_scope_missing")
                        setup = source["setup_evidence"]
                        raw = setup.get("strategy_raw_input")
                        if not isinstance(raw, dict):
                            raise ValueError("machine_raw_input_missing")
                        if strategy.digest(raw) != setup.get("strategy_raw_sha256"):
                            raise ValueError("machine_raw_hash_invalid")
                        profile, selection = strategy.select(scoped["machine_policy"], raw, setup)
                        if (receipt.get("bundle_sha256") != bundle_hash
                                or receipt.get("policy_sha256") != selection["policy_sha256"]
                                or receipt.get("selector_leaf") != selection["leaf"]
                                or receipt.get("effective_thresholds") != profile):
                            raise ValueError("effective_policy_receipt_mismatch")
                    key = "|".join((*scope, bundle_hash, selection["policy_sha256"], selection["leaf"]))
                    counts = result["scopes"].setdefault(key, dict(matched_receipts=0, live_pid_receipts=0,
                        effective_thresholds=profile, current_bundle=bundle_hash == result.get("current_bundle_sha256")))
                    counts["matched_receipts"] += 1
                    contract = ('native_reversal_receipt' if receipt.get('continuous_reversal')
                                else 'historical_reversal_capture' if frozen.get('continuous_reversal')
                                else 'legacy_strategy_receipt')
                    counts[contract] = counts.get(contract, 0) + 1
                    identity = (receipt.get('pid'), receipt.get('cwd'), receipt.get('process_start_ticks'))
                    if identity not in pid_identities:
                        try:
                            proc = Path('/proc') / str(int(receipt['pid']))
                            live = (str((proc/'cwd').resolve()) == receipt.get('cwd')
                                and (proc/'stat').read_text().split(') ', 1)[1].split()[19] == receipt.get('process_start_ticks'))
                        except (OSError, ValueError, KeyError, IndexError):
                            live = False
                        pid_identities[identity] = live
                    live = pid_identities[identity]
                    counts["live_pid_receipts"] += int(live)
                except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
                    reason = str(exc)[:160]
                    issues[reason] += 1
                    if len(result["examples"]) < 3:
                        result["examples"].append(dict(observation_sha256=observed_hash, reason=reason))
    except OSError as exc:
        result["source_status"] = 'unobservable:' + (
            'compressed_archive_not_current_bounded_source'
            if path.with_suffix(path.suffix + '.gz').exists() else type(exc).__name__)
    if reversal_observations:
        lineage = _reversal_provider_lineage(data_root, now, reversal_observations, tail_bytes=tail_bytes)
        result['reversal_provider_lineage'] = lineage
        issues.update(lineage['issues'])
    result['pid_identity_read_count'] = len(pid_identities)
    result["issues"] = dict(issues)
    if issues:
        result["status"] = "review_required"
    elif result.get("selection_status") or result.get("source_status"):
        result["status"] = "partial_unobservable"
    elif result["source_invalid_count"] or result["required_feature_guard_count"]:
        result["status"] = "source_invalid_observed"
    elif result["observation_count"]:
        result["status"] = "observed_receipts_match"
    return result


def _latest_dated_json(directory, prefix, through_date):
    """Read one exact-date artifact; never scan event/history payloads here."""
    candidates = []
    for path in directory.glob(f"{prefix}????-??-??.json"):
        day = path.name[len(prefix):-5]
        try:
            if datetime.fromisoformat(day).date().isoformat() == day and day <= through_date:
                candidates.append((day, path))
        except ValueError:
            continue
    if not candidates:
        return None, None
    day, path = max(candidates)
    if path.is_symlink():
        raise ValueError("semantic_artifact_symlink_rejected")
    return day, _small_json(path)


def entry_execution_tuning_semantics(data_root, now):
    """Audit the independent split/delay postclose receipts without replaying data."""
    now = stamp(now)
    day = now.date().isoformat()
    result = {
        "schema": "entry_execution_tuning_semantics_v1",
        "as_of": now.isoformat(),
        "metric_role": "source_quality_gate",
        "decision_authority": "report_only",
        "axes_are_independent": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "forbidden_uses": ["entry_action", "split_or_delay_policy_change", "missing_as_zero_ev"],
        "bootstrap": {"status": "unobservable"},
        "entry_split": {"status": "unobservable", "runtime_consumption": "not_proven"},
        "pre_submit_delay": {"status": "unobservable", "runtime_consumption": "not_proven"},
        "issues": {},
        "examples": [],
    }
    issues = Counter()
    data_root = Path(data_root)

    bootstrap_path = data_root / "runtime/policy_bootstrap" / f"runtime_policy_bootstrap_{day}.json"
    verify_path = data_root / "runtime/policy_bootstrap" / f"runtime_policy_bootstrap_verify_{day}.json"
    bootstrap = {}
    bootstrap_valid = False
    try:
        bootstrap = _small_json(bootstrap_path)
        verify = _small_json(verify_path)
        if bootstrap.get("target_date") != day or verify.get("target_date") != day:
            raise ValueError("bootstrap_target_date_mismatch")
        bootstrap_valid = True
        result["bootstrap"] = {
            "status": "verified" if verify.get("status") == "pass" and verify.get("passed") is True else "verification_not_passed",
            "verify_status": verify.get("status"),
            "pid_passed": verify.get("pid_passed"),
            "policy_pid_consumption_proven": False,
        }
        if result["bootstrap"]["status"] != "verified":
            issues["entry_execution_bootstrap_verification_failed"] += 1
            result["examples"].append({"axis": "bootstrap", "reason": "same_date_verification_not_passed"})
    except (OSError, ValueError, TypeError) as exc:
        result["bootstrap"] = {"status": "unobservable", "reason": str(exc)[:160]}

    # Entry split: exact report-policy generation, source gap, and the dated
    # incumbent named by the bootstrap are distinct facts. No candidate is not
    # a receipt defect and does not create a synthetic zero-EV result.
    split = result["entry_split"]
    try:
        report_date, report = _latest_dated_json(
            data_root / "report/entry_split_order_plan", "entry_split_order_plan_", day
        )
        if report is None:
            split.update(status="not_yet_observed", blocker="entry_split_report_missing")
        else:
            policy_path = data_root / "threshold_cycle/entry_split_order_policy" / f"entry_split_order_policy_{report_date}.json"
            binding_status = "missing"
            policy = None
            if policy_path.is_symlink():
                binding_status = "symlink_rejected"
            elif policy_path.exists():
                policy = _small_json(policy_path)
                from src.engine.scalping.entry_split_order_plan import validate_report_policy_generation
                valid, reason = validate_report_policy_generation(report, policy)
                binding_status = "matched" if valid else reason
            if binding_status != "matched":
                issues["entry_split_report_policy_generation_mismatch"] += 1
                if len(result["examples"]) < 3:
                    result["examples"].append({"axis": "entry_split", "reason": binding_status, "source_date": report_date})
            bootstrap_policy_binding = "unobservable"
            if bootstrap_valid:
                env = bootstrap.get("env_overrides") or {}
                env_file = env.get("KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_POLICY_FILE") if isinstance(env, dict) else None
                env_version = env.get("KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_POLICY_VERSION") if isinstance(env, dict) else None
                configured = None
                if env_file:
                    configured_path = Path(str(env_file))
                    try:
                        configured_path.resolve(strict=True).relative_to(data_root.resolve(strict=True))
                        if configured_path.is_symlink():
                            raise ValueError("bootstrap_policy_symlink_rejected")
                        configured = _small_json(configured_path)
                    except (OSError, ValueError, RuntimeError):
                        configured = None
                        bootstrap_policy_binding = "configured_policy_invalid"
                if configured is not None and configured.get("policy_version") != env_version:
                    bootstrap_policy_binding = "configured_policy_version_mismatch"
                elif configured is not None and policy and policy.get("runtime_apply_allowed") is True:
                    same_file = Path(str(env_file)).resolve() == policy_path.resolve()
                    bootstrap_policy_binding = "candidate_bound" if same_file and env_version == policy.get("policy_version") else "promoted_candidate_not_bound"
                elif policy and policy.get("runtime_apply_allowed") is True:
                    bootstrap_policy_binding = "promoted_candidate_not_bound"
                elif configured is not None:
                    bootstrap_policy_binding = "incumbent_preserved_candidate_not_promoted"
                if bootstrap_policy_binding in {
                    "configured_policy_invalid", "configured_policy_version_mismatch", "promoted_candidate_not_bound"
                }:
                    issue = "entry_split_bootstrap_policy_binding_invalid"
                    issues[issue] += 1
                    if len(result["examples"]) < 3:
                        result["examples"].append({"axis": "entry_split", "reason": bootstrap_policy_binding, "source_date": report_date})
            acceptance = report.get("economic_acceptance") or {}
            candidates = report.get("operating_candidate_grid") or []
            split.update(
                status="source_gap" if acceptance.get("blockers") else "candidate_observed" if candidates else "no_candidate_observed",
                source_date=report_date,
                report_schema=report.get("schema_version"),
                clean_baseline_date=(report.get("cumulative_state") or {}).get("clean_tuning_baseline_date"),
                cumulative_source_date_count=len((report.get("cumulative_state") or {}).get("source_dates") or []),
                economic_status=acceptance.get("status"),
                blockers=list(acceptance.get("blockers") or [])[:12],
                operating_candidate_count=len(candidates),
                primary_operating_ev_pct=acceptance.get("primary_operating_ev_pct"),
                robust_paired_delta_ev_lower_bound_pct=acceptance.get("robust_paired_delta_ev_lower_bound_pct"),
                paired_model_row_count=acceptance.get("model_rows"),
                consumed_holdout_count=acceptance.get("consumed_holdouts"),
                policy_generation_binding=binding_status,
                policy_runtime_apply_allowed=bool(policy and policy.get("runtime_apply_allowed")),
                prepared_effective_date=(policy or {}).get("prepared_effective_date"),
                paired_net_ev_delta_pct=acceptance.get("paired_net_ev_delta_pct"),
                bootstrap_policy_binding=bootstrap_policy_binding,
                runtime_consumption="bootstrap_manifest_bound_not_pid_proven" if bootstrap_policy_binding in {
                    "candidate_bound", "incumbent_preserved_candidate_not_promoted"
                } else "not_proven",
            )
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        split.update(status="unobservable", reason=str(exc)[:160])

    # The bootstrap's own delay selector is the canonical policy validator.
    # Re-run that bounded small-artifact check and compare it with the frozen
    # manifest; do not read raw pipeline/BBO history or regenerate the tuner.
    delay = result["pre_submit_delay"]
    try:
        delay_report_date, delay_report = _latest_dated_json(
            data_root / "report/pre_submit_delay_tuning", "pre_submit_delay_tuning_", day
        )
        if delay_report is not None:
            report_identity_valid = (
                delay_report.get("schema") == "pre_submit_delay_tuning_v1"
                and delay_report.get("source_date") == delay_report_date
                and delay_report.get("analysis_axis") == "pre_submit_delay"
            )
            if not report_identity_valid:
                issues["pre_submit_delay_report_identity_invalid"] += 1
                if len(result["examples"]) < 3:
                    result["examples"].append({"axis": "pre_submit_delay", "reason": "report_identity_invalid", "source_date": delay_report_date})
            delay_grid = delay_report.get("candidate_grid") or []
            from src.engine.scalping.pre_submit_delay_tuning import price_pattern_projection
            price_analysis = price_pattern_projection(delay_report)
            if price_analysis["status"] == "source_invalid":
                issues["pre_submit_delay_price_pattern_invalid"] += 1
            delay.update(
                report_status="observed" if report_identity_valid else "invalid",
                report_date=delay_report_date,
                report_schema=delay_report.get("schema"),
                report_source_date=delay_report.get("source_date"),
                clean_baseline_date=delay_report.get("clean_tuning_baseline_date"),
                source_date_count=(delay_report.get("source") or {}).get("source_date_count"),
                committed_count=delay_report.get("committed_attempt_count"),
                completed_terminal_count=delay_report.get("terminal_observation_count"),
                submit_call_terminal_count=delay_report.get("terminal_observation_count"),
                terminal_count_semantics="submit_call_completion_not_fill_or_exit",
                price_pattern_analysis=price_analysis,
                candidate_count=len(delay_grid),
                candidate_delays_sec=[row.get("delay_sec") for row in delay_grid[:8]],
                report_blockers=[delay_report.get("first_blocker")] if delay_report.get("first_blocker") else [],
                selected_delay_sec=delay_report.get("selected_delay_sec"),
                net_ev_delta_pct=delay_report.get("net_ev_delta_pct"),
            )
        else:
            delay["report_status"] = "not_yet_observed"
        from src.engine.automation import runtime_policy_bootstrap as bootstrap_owner
        expected_env, expected_handoff = bootstrap_owner._pre_submit_delay_handoff(day)
        recorded_handoff = bootstrap.get("pre_submit_delay_handoff")
        env = bootstrap.get("env_overrides") or {}
        if not isinstance(env, dict):
            raise ValueError("bootstrap_env_overrides_invalid")
        # A missing/stale bootstrap is unobservable; do not turn it into a
        # mismatch against today's selector. Only compare same-day receipts.
        handoff_match = recorded_handoff == expected_handoff if bootstrap_valid else None
        env_keys = set(bootstrap_owner.PRE_SUBMIT_DELAY_ENV_KEYS)
        env_match = ({key: env.get(key) for key in env_keys if key in env} == expected_env
                     if bootstrap_valid else None)
        if bootstrap_valid and handoff_match is not True:
            issues["pre_submit_delay_bootstrap_handoff_mismatch"] += 1
            if len(result["examples"]) < 3:
                result["examples"].append({"axis": "pre_submit_delay", "reason": "bootstrap_handoff_mismatch"})
        if bootstrap_valid and env_match is not True:
            issues["pre_submit_delay_bootstrap_env_mismatch"] += 1
            if len(result["examples"]) < 3:
                result["examples"].append({"axis": "pre_submit_delay", "reason": "bootstrap_env_mismatch"})
        status = expected_handoff.get("status")
        delay.update(
            status=("verified_policy_bound" if status in {"verified_candidate", "verified_carried_candidate"} and env_match is True
                    else "source_gap" if status == "no_validated_candidate_source_gap"
                    else "not_evaluated" if status == "no_validated_candidate_not_evaluated"
                    else "unpublished" if status == "not_published"
                    else "contract_mismatch" if status == "binding_invalid" or handoff_match is False
                    else "unobservable"),
            handoff_status=status,
            source_date=expected_handoff.get("source_date"),
            effective_from=expected_handoff.get("effective_from"),
            policy_sha256=expected_handoff.get("policy_sha256"),
            bootstrap_handoff_match=handoff_match,
            bootstrap_env_match=env_match,
            runtime_consumption="bootstrap_manifest_bound_not_pid_proven" if expected_env and env_match is True else "not_proven",
            runtime_effect=False,
        )
        if status == "binding_invalid":
            issues["pre_submit_delay_policy_binding_invalid"] += 1
            if len(result["examples"]) < 3:
                result["examples"].append({"axis": "pre_submit_delay", "reason": "policy_binding_invalid"})
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        delay.update(status="unobservable", reason=str(exc)[:160])

    # Postclose artifact_freshness owns cancel-wait incidents. This projection
    # provides the same diagnostics without creating a duplicate intraday alert.
    from src.engine.error_detectors.artifact_freshness import _entry_cancel_wait_result_semantics, _cancel_wait_monitor_source_date
    result["entry_cancel_wait"] = _entry_cancel_wait_result_semantics(data_root.parent,
        _cancel_wait_monitor_source_date(data_root.parent,day,data_root=data_root), now,
        data_root=data_root)
    result["entry_cancel_wait"]["notification_owner"] = "artifact_freshness"
    result["issues"] = dict(issues)
    if issues:
        result["status"] = "review_required"
    elif result["bootstrap"].get("status") == "verified":
        result["status"] = "observed"
    else:
        result["status"] = "partial_unobservable"
    return result


def attach_entry_execution_tuning_semantics(result, semantics):
    """Persist only contradictory receipt claims; source gaps remain diagnostic."""
    result["entry_execution_tuning_semantics"] = semantics
    key = "entry_execution_tuning_receipt_contract"
    old = result["incidents"].get(key, {})
    if semantics.get("issues"):
        now = stamp(result["as_of"])
        first = old.get("first_seen", result["as_of"]) if old.get("status") in {"pending", "active"} else result["as_of"]
        item = dict(
            scope="entry_split|pre_submit_delay",
            rule=key,
            category="structural_evidence",
            first_seen=first,
            last_seen=result["as_of"],
            status="active" if (now - stamp(first)).total_seconds() >= 240 else "pending",
            count=sum(semantics["issues"].values()),
            issues=semantics["issues"],
            examples=semantics.get("examples", [])[:3],
            owner="entry_split_order_plan->pre_submit_delay_tuning->runtime_policy_bootstrap",
            closure_test="same-date report/policy generation and bootstrap handoff hashes agree",
            notified_status=old.get("notified_status") if old.get("status") in {"pending", "active"} else None,
        )
        if old.get("history"):
            item["history"] = old["history"]
        if old.get("status") == "historical_unresolved":
            item["history"] = (list(old.get("history", [])) + [{k: v for k, v in old.items() if k != "history"}])[-8:]
        result["incidents"][key] = item
    elif old.get("status") == "active":
        result["incidents"][key] = {**old, "status": "historical_unresolved"}
    elif old.get("status") == "pending":
        result["incidents"].pop(key, None)
    item = result["incidents"].get(key, {})
    if item.get("status") == "active" and item.get("notified_status") != item["status"]:
        if key not in result["notification_pending"]:
            result["notification_pending"].append(key)


def attach_machine_semantics(result, semantics):
    """Persistent report-only receipt faults; absence never repairs old evidence."""
    result["machine_semantics"] = semantics
    key = "machine_policy_receipt_contract"
    old = result["incidents"].get(key, {})
    if semantics.get("issues"):
        now = stamp(result["as_of"])
        first = old.get("first_seen", result["as_of"]) if old.get("status") in {"pending", "active"} else result["as_of"]
        item = dict(scope=semantics.get("current_bundle_sha256", "unbound"), rule=key,
            category="structural_evidence", first_seen=first, last_seen=result["as_of"],
            status="active" if (now - stamp(first)).total_seconds() >= 240 else "pending",
            count=sum(semantics["issues"].values()), examples=semantics.get("examples", []),
            issues=semantics["issues"], owner="machine_observation->frozen_policy->runtime_receipt",
            closure_test="repair exact receipt source; absence does not repair historical observations",
            notified_status=old.get("notified_status") if old.get("status") in {"pending", "active"} else None)
        if old.get("history"):
            item["history"] = old["history"]
        if old.get("status") == "historical_unresolved":
            item["history"] = (list(old.get("history", [])) + [{k:v for k,v in old.items() if k != "history"}])[-8:]
        result["incidents"][key] = item
    elif old.get("status") == "active":
        result["incidents"][key] = {**old, "status": "historical_unresolved"}
    elif old.get("status") == "pending":
        result["incidents"].pop(key, None)
    item = result["incidents"].get(key, {})
    if item.get("status") == "active" and item.get("notified_status") != item["status"]:
        if key not in result["notification_pending"]:
            result["notification_pending"].append(key)


def evaluate(report, state, now):
    """Pure state transition. Old/stale evidence never triggers recovery or alerts."""
    now = stamp(now)
    source = report.get("submission_monitor") or {}
    as_of = stamp(source.get("as_of"))
    latest = stamp(source.get("latest_event_at"))
    today = now.date().isoformat()
    prior = state if state.get("date") == today and state.get("schema") == SCHEMA else {}
    incidents = dict(prior.get("incidents") or {})
    result = {"schema": SCHEMA, "date": today, "as_of": now.isoformat(),
              "async_disposition_coverage": source.get('async_disposition_coverage') or {},
              "runtime_effect": False, "status": "unobservable", "blocker": None,
              "notification_status": "idle",
              "incidents": incidents, "notification_pending": [], "scopes": {},
              "source_as_of": prior.get("source_as_of"),
              "identity_observation": {"status": "unobservable", "reason": "source_not_validated"},
              "last_notification_at": prior.get("last_notification_at")}
    result["economic_coverage_contract"] = {
        "metric_role": "funnel_count", "decision_authority": "report_only",
        "window_policy": "exact_attempts_current_30_minutes",
        "sample_floor": "none_for_counts_no_quality_acceptance",
        "primary_decision_metric": "economic_gap_action_counts",
        "source_quality_gate": "same_attempt_explicit_nonentry_cache_miss_only",
        "forbidden_uses": ["order_authority", "missing_as_zero_ev", "tuning_population_acceptance"],
    }
    # A quiet machine window cannot prove normal current behavior. It can
    # still correct an old alert when a fresh source snapshot binds every old
    # evidence hash to a valid fixed-watch admission.
    reclassification_source_current = (
        report.get("target_date") == today and not report.get("dry_run")
        and source.get("schema") == SCHEMA and as_of is not None
        and 0 <= (now - as_of).total_seconds() <= 420
        and (not prior.get("source_as_of") or
            (stamp(prior["source_as_of"]) is not None
             and as_of > stamp(prior["source_as_of"])))
        and (source.get("fixed_watch_identity_observation") or {}).get("schema")
            == "fixed_watch_source_identity_v1"
    )
    old_identity = incidents.get("unbound_machine_identity", {})
    old_evidence = set(old_identity.get("evidence_ids") or [])
    if (reclassification_source_current and old_identity.get("rule") == "source_identity_missing"
        and old_evidence and old_evidence <= set(source.get("fixed_watch_identified_evidence") or [])):
        incidents["unbound_machine_identity_reclassified_fixed_watch"] = {
            **old_identity, "status": "reclassified", "scope": "fixed_watch",
            "classification": "valid_fixed_watch_non_scanner_identity",
            "correction_basis": "all_prior_evidence_ids_match_valid_fixed_watch_source_events",
            "last_seen": now.isoformat(),
        }
        incidents.pop("unbound_machine_identity", None)
        result["fixed_watch_identity_observation"] = source["fixed_watch_identity_observation"]
    if (report.get("target_date") != today or report.get("dry_run")
            or source.get("schema") != SCHEMA or not as_of or not latest
            or not 0 <= (now - as_of).total_seconds() <= 420
            or not 0 <= (now - latest).total_seconds() <= 600):
        result["blocker"] = "missing_stale_or_noncurrent_sentinel_evidence"
        return result
    if prior.get("source_as_of") and as_of <= stamp(prior["source_as_of"]):
        result["blocker"] = "duplicate_or_reversed_source_snapshot"
        return result
    result.update(status="observing", source_as_of=as_of.isoformat())
    result["fixed_watch_identity_observation"] = source.get("fixed_watch_identity_observation") or {}
    # Preserve the original incident as superseded evidence, without reporting
    # alias normalization as recovery or double-counting its exact attempts.
    for old_key, old in list(incidents.items()):
        parts = str(old.get("scope", "")).split("|")
        if len(parts) != 3 or parts[1] != "KRX_LIKE_PREMARKET" or old.get("superseded_by"):
            continue
        parts[1] = "PREMARKET_KRX_LIKE"
        scope = "|".join(parts)
        key = hashlib.sha256(f"{scope}|{old['rule']}".encode()).hexdigest()[:24]
        def normalized_identity(value):
            fields = value.split("|")
            if len(fields) == 6 and fields[4] == "KRX_LIKE_PREMARKET":
                fields[4] = "PREMARKET_KRX_LIKE"
            return "|".join(fields)
        current = incidents.get(key, {})
        ids = sorted(set(current.get("evidence_ids", [])) | {
            normalized_identity(value) for value in old.get("evidence_ids", [])})
        incidents[key] = {**old, **current, "scope": scope,
            "evidence_ids": ids[:128], "count": max(len(ids), old.get("count", 0), current.get("count", 0)),
            "first_seen": min(old["first_seen"], current.get("first_seen", old["first_seen"])),
            "promotion_ids": sorted(set(old.get("promotion_ids", [])) | set(current.get("promotion_ids", []))),
            "examples": current.get("examples") or [{**example,
                "evaluation_key": normalized_identity(example["evaluation_key"])}
                for example in old.get("examples", [])]}
        incidents[old_key] = {**old, "status": "superseded_alias", "superseded_by": key}
    groups = defaultdict(list)
    for row in source.get("rows", []):
        start = stamp(row.get("first_evaluated_at"))
        if start and 0 <= (now - start).total_seconds() <= 2700:
            scope = "|".join(str(row.get(k) or "missing") for k in (
                "effective_venue", "session_bucket", "policy_bundle_hash"))
            groups[scope].append(row)
    if not groups:
        result.update(status="unobservable", blocker="no_identified_machine_evaluation")
    for scope, all_rows in groups.items():
        rows = [r for r in all_rows if (now - stamp(r["first_evaluated_at"])).total_seconds() <= WINDOW_SEC]
        # Count each promotion once for scarcity, but retain exact attempts for gaps.
        parents = {}
        for row in sorted(rows, key=lambda r: r["first_evaluated_at"]):
            parents[(row["scanner_promotion_id"], row["stock_code"])] = row
        valid = [r for r in parents.values() if not r["conflict_reasons"] and r["mechanistic_action"] != "SOURCE_INVALID"]
        entered = [r for r in valid if r["mechanistic_action"] == "ENTER_NOW"]
        veto = [r for r in entered if r["ai_screen_status"] == "veto"]
        accepted = [r for r in rows if r["broker_acceptance_observed"]]
        gaps = [r for r in all_rows if (now - stamp(r["first_evaluated_at"])).total_seconds() >= GRACE_SEC
                and (r["conflict_reasons"] or r["mechanistic_action"] == "SOURCE_INVALID"
                     or r["final_state"].startswith("lineage_gap")
                     or r["final_state"] == "pending_broker_reconciliation"
                     or (r["ai_screen_status"] == "pass" and r["final_state"] == "pending"))]
        economic_gaps = [r for r in all_rows
            if (now - stamp(r["first_evaluated_at"])).total_seconds() >= GRACE_SEC
            and (r.get("economic_source") or {}).get("status") == "source_gap"
            and not _nonentry_downstream_gap(r)]
        observation_gaps = [r for r in rows if _nonentry_capacity_observation_gap(r)]
        tests = {
            "economic_producer_gap": (economic_gaps, "structural_evidence", 240),
            "source_or_submit_lineage_gap": (gaps, "structural_evidence", 240),
            "enter_now_scarcity": (valid if len(valid) >= MIN_PROMOTIONS and not entered
                and not any(r.get("enter_now_observed") for r in rows) else [], "review_required", PERSIST_SEC),
            "ai_veto_concentration": (veto if len(entered) >= MIN_PROMOTIONS and len(veto) / len(entered) >= .9 and not accepted else [], "review_required", PERSIST_SEC),
        }
        result["scopes"][scope] = {"unique_promotions": len(parents), "valid_promotions": len(valid),
            "enter_now_observed_attempts": sum(bool(r.get("enter_now_observed")) for r in rows),
            "enter_now_observed_conflicting_attempts": sum(bool(r.get("enter_now_observed")) and bool(r["conflict_reasons"]) for r in rows),
            "enter_now": len(entered), "veto": len(veto), "accepted_attempts": len(accepted),
            "machine_action_counts": dict(Counter(r["mechanistic_action"] for r in valid)),
            "unresolved_attempts": len(gaps), "economic_producer_gaps": len(economic_gaps),
            "nonentry_capacity_observation_gaps": len(observation_gaps),
            "nonentry_downstream_observation_gaps": sum(_nonentry_downstream_gap(r) for r in rows),
            "economic_producer_gap_owner": "downstream_execution_replay_not_machine_tuning",
            "nonentry_capacity_observation_examples": [{k: r.get(k) for k in
                ("stock_code", "evaluation_key", "first_evaluated_at", "mechanistic_action", "economic_source")}
                for r in observation_gaps[:3]],
            "economic_gap_action_counts": {action: sum(r["mechanistic_action"] == action
                and (r.get("economic_source") or {}).get("status") == "source_gap" for r in rows)
                for action in ("ENTER_NOW", "BLOCK", "RECHECK", "SOURCE_INVALID")},
            "economic_status_counts": {status: sum((r.get("economic_source") or {}).get("status") == status for r in rows)
                for status in ("recorded_source_only", "source_gap", "guard_excluded", "unsupported_scope")}, "guard_blocked": sum(r["final_guard_blocked"] for r in rows)}
        for rule, (bad, category, persistence) in tests.items():
            key = hashlib.sha256(f"{scope}|{rule}".encode()).hexdigest()[:24]
            old = incidents.get(key, {})
            ids = sorted({r["evaluation_key"] for r in bad})
            if bad:
                first = old.get("first_seen", now.isoformat()) if old.get("status") in {"pending", "active"} else now.isoformat()
                # Ratios need new independent promotions, not repeated snapshots.
                identities = sorted({f'{r["scanner_promotion_id"]}|{r["stock_code"]}' for r in bad})
                new_support = bool(set(identities) - set(old.get("promotion_ids", [])))
                confirmed = bool(old) and (now - stamp(first)).total_seconds() >= persistence
                confirmed = confirmed and (category == "structural_evidence" or new_support or old.get("status") == "active")
                item = {"scope": scope, "rule": rule, "category": category, "first_seen": first,
                    "last_seen": now.isoformat(), "status": "active" if confirmed else "pending",
                    "evidence_ids": ids[:128], "promotion_ids": identities[:128],
                    "count": len(ids), "notified_status": old.get("notified_status"),
                    "examples": [{k: r.get(k) for k in ("stock_code", "evaluation_key", "mechanistic_action", "final_state", "conflict_reasons", "auxiliary_ai_semantics", "source_invalid_decomposition", "economic_source", "final_guard_evidence")} for r in bad[:3]],
                    "owner": (bad[0].get("economic_source") or {}).get("owner") if rule == "economic_producer_gap" else "buy_funnel_sentinel.machine_primary_entry_funnel",
                    "closure_test": (
                        "same attempt publishes valid frozen economic proof"
                        if rule == "economic_producer_gap" else
                        "new conflict-free ENTER_NOW promotion in the same scope; order submission is tracked separately"
                        if rule == "enter_now_scarcity" else
                        "same attempt receives a consistent terminal; ratios recover on new valid promotions"
                    )}
                if old.get("history"):
                    item["history"] = old["history"]
                if old.get("status") == "observation_only_unresolved":
                    item["history"] = (list(old.get("history") or []) + [
                        {k: v for k, v in old.items() if k != "history"}])[-8:]
                    item["notified_status"] = None
                incidents[key] = item
            elif (rule == "economic_producer_gap" and old
                  and old.get("status") in {"active", "pending"}
                  and old.get("count") == len(set(old.get("evidence_ids", [])))
                  and old.get("evidence_ids")
                  and set(old["evidence_ids"]) <= {r["evaluation_key"] for r in all_rows
                                                    if _nonentry_downstream_gap(r)}):
                # Reclassification is not source recovery. Preserve old proof
                # IDs/count/examples; unknown/expired/mixed incidents stay open.
                incidents[key] = {**old, "status": "observation_only_unresolved",
                    "classification_reason": "exact_nonentry_downstream_evidence_not_machine_tuning",
                    "classified_at": now.isoformat()}
            elif old and old.get("status") == "active":
                # Window expiration is not recovery. Require explicit closure evidence.
                old_ids = set(old.get("evidence_ids", []))
                resolved = {r["evaluation_key"] for r in all_rows if r["evaluation_key"] in old_ids
                    and ((r.get("economic_source") or {}).get("status") == "recorded_source_only"
                         if rule == "economic_producer_gap" else not r["conflict_reasons"]
                         and r["final_state"] in {"submit_pipeline_reached", "final_guard_blocked", "broker_rejected"})}
                healthy = bool(old_ids and old.get("count") == len(old_ids) and old_ids <= resolved) if category == "structural_evidence" else bool(accepted and any(r["evaluation_key"] not in old_ids for r in accepted))
                if rule == "enter_now_scarcity":
                    healthy = any(
                        r["mechanistic_action"] == "ENTER_NOW"
                        and not r["conflict_reasons"]
                        for r in rows
                    )
                if healthy:
                    incidents[key] = {**old, "status": "recovered", "last_seen": now.isoformat()}
            elif old and old.get("status") == "pending":
                incidents.pop(key, None)
    missing = source.get("missing_identity_evidence") or []
    key = "unbound_machine_identity"
    old = incidents.get(key, {})
    observation = source.get("identity_observation") or {}
    current_status = (observation.get("status") if observation.get("schema") == "machine_identity_recency_v1"
                      else "unobservable")
    if current_status not in {"current_gap", "no_recurrence_observed", "unobservable"}:
        current_status = "unobservable"
    result["identity_observation"] = observation or {"status": "unobservable", "reason": "legacy_source_no_recency"}
    if missing:
        recurrence = (old.get("status") == "historical_unresolved" and current_status == "current_gap"
                      and bool(set(missing) - set(old.get("evidence_ids", []))))
        history = list(old.get("history") or [])
        if recurrence:
            history.append({k: v for k, v in old.items() if k != "history"})
        first = old.get("first_seen", now.isoformat()) if not recurrence else now.isoformat()
        status = "active"  # Exact current identity loss needs no ratio/persistence floor.
        if current_status != "current_gap":
            status = "historical_unresolved"
        # A shrinking window must not erase the already recorded old incident.
        preserve = bool(old) and not recurrence and (status == "historical_unresolved"
                                                    or old.get("status") == "historical_unresolved")
        if preserve:
            status = "historical_unresolved"
        incidents[key] = {**old, "scope": "unbound", "rule": "source_identity_missing",
            "category": "structural_evidence", "first_seen": first, "last_seen": now.isoformat(),
            "status": status, "current_status": current_status, "history": history,
            "count": old.get("count", len(missing)) if preserve else len(missing),
            "evidence_ids": old.get("evidence_ids", missing[:128]) if preserve else missing[:128],
            "examples": (old.get("examples") or []) if preserve else source.get("missing_identity_examples") or [],
            "occurred_first_at": old.get("occurred_first_at") if preserve else source.get("missing_identity_first_at"),
            "occurred_last_at": old.get("occurred_last_at") if preserve else source.get("missing_identity_last_at"),
            "notified_status": None if recurrence else old.get("notified_status"),
            "normal_observation_pending": False if recurrence else old.get("normal_observation_pending", False),
            "normal_observation_notified_at": None if recurrence else old.get("normal_observation_notified_at"),
            "owner": "ENTRY_PIPELINE machine producer identity",
            "closure_test": "new identified machine evaluations with no missing identity; old unbound rows remain unrepairable"}
    elif old:
        incidents[key] = {**old, "status": "historical_unresolved", "current_status": current_status}
    item = incidents.get(key, {})
    if (item.get("status") == "historical_unresolved"
            and old.get("status") == "active" and old.get("notified_status") == "active"):
        item["normal_observation_pending"] = True
    if item and not item.get('examples'):
        matched = {r['evidence_id']: r for r in (source.get('historical_identity_samples', [])
                    + source.get('missing_identity_examples', []))
                   if r.get('evidence_id') in set(item.get('evidence_ids', []))}
        if matched:
            details = sorted(matched.values(), key=lambda r: r['occurred_at'])
            item['examples'] = details[:3]
            item['detail_basis'] = 'existing_cache_exact_evidence_hash_match'
            if len(matched) == len(set(item.get('evidence_ids', []))) == item.get('count'):
                item['occurred_first_at'] = details[0]['occurred_at']
                item['occurred_last_at'] = details[-1]['occurred_at']
    if missing or old:
        result["scopes"]["unbound"] = {"missing_identity_events": len(missing),
            "current_missing_events": observation.get("missing_event_count"), "current_status": current_status}
    if observation.get("missing_event_count"):
        result["blocker"] = "machine_identity_missing_events"
        result["identity_missing_events"] = observation["missing_event_count"]
    # Absent scopes/stale sources retain incidents without asserting they resolved.
    result["notification_pending"] = [k for k, v in incidents.items()
        if _notification_kind(v, result) and v["scope"] in result["scopes"]]
    return result


def _notification_kind(item, result):
    status = item.get("status")
    if status in {"active", "recovered"} and item.get("notified_status") != status:
        return status
    observation = result.get("identity_observation") or {}
    if (status == "historical_unresolved" and item.get("rule") == "source_identity_missing"
            and item.get("normal_observation_pending")
            and observation.get("status") == "no_recurrence_observed"
            and observation.get("missing_event_count") == 0
            and observation.get("identified_event_count", 0) > 0):
        return "normal_observation"
    return None


def notify(result, path, send=None):
    keys = [key for key in result["notification_pending"]
            if _notification_kind(result["incidents"][key], result)]
    keys.sort(key=lambda key: (
        _notification_kind(result["incidents"][key], result) != "active",
        key != "machine_auxiliary_intraday_source_gap"))
    last = stamp(result.get("last_notification_at"))
    if last and (stamp(result["as_of"]) - last).total_seconds() < 300:
        result["notification_status"] = "cooldown"
        return
    if not keys:
        return
    messages = []
    for key in keys[:4]:
        item = result["incidents"][key]
        if _notification_kind(item, result) == "normal_observation":
            obs = result["identity_observation"]
            messages.append(
                "현재 정상 관측: 식별자 결손 최근10분 0건 / "
                f'정상 식별 {obs["identified_event_count"]} 이벤트\n'
                "추가 점검 요청 없음. 과거 결손은 보고서에 보존하며 원천 복구를 뜻하지 않습니다.")
            continue
        if item["rule"] == "source_identity_missing":
            obs = result.get("identity_observation") or {}
            examples = obs.get("examples") or item.get("examples") or []
            sample = examples[0] if examples else {}
            identity_details = []
            if sample.get("missing_fields"):
                identity_details.append("누락 필드: " + ", ".join(sample["missing_fields"]))
            if sample.get("conflicting_fields"):
                identity_details.append("충돌 필드: " + ", ".join(sample["conflicting_fields"]))
            if sample.get("identity_contract_issues"):
                identity_details.append("식별 계약: " + ", ".join(sample["identity_contract_issues"]))
            if not identity_details:
                identity_details.append("식별 결손 세부정보: 미확인(구형 이력)")
            messages.append(
                f'{item["status"]}: source_identity_missing\n'
                f'현재 최근10분: {item.get("current_status", "unobservable")} '
                f'/ 결손 {obs.get("missing_event_count", "미확인")}건\n'
                f'과거 원천 복구 주장 없음 / 보존 근거 {item["count"]} 이벤트 (주문 수 아님)\n'
                f'현재 결손 발생: {obs.get("current_missing_first_at") or item.get("occurred_first_at") or "미확인(구형 이력)"} ~ '
                f'{obs.get("current_missing_last_at") or item.get("occurred_last_at") or "미확인(구형 이력)"}\n'
                f'종목: {sample.get("stock_code") or "미확인(구형 이력)"} / '
                f'{" / ".join(identity_details)}\n'
                f'대표 발생시각: {sample.get("occurred_at") or "미확인(구형 이력)"}')
            continue
        if item["rule"] == "enter_now_scarcity":
            stats = result.get("scopes", {}).get(item["scope"], {})
            actions = stats.get("machine_action_counts", {})
            messages.append(
                f'{item["status"]}: 기계판정 ENTER_NOW 희소 / {item["scope"]}\n'
                f'유효 승격 {stats.get("valid_promotions", "미확인")}건 / '
                f'BLOCK {actions.get("BLOCK", 0)} / RECHECK {actions.get("RECHECK", 0)} / '
                f'ENTER_NOW {actions.get("ENTER_NOW", 0)}\n'
                "판정 경로 검토 신호이며 주문 제출 실패·미체결 증거가 아닙니다."
            )
            continue
        if item["rule"] == "machine_auxiliary_intraday_source_gap":
            if item["status"] == "recovered":
                messages.append(
                    "현재 정상 관측: 해당 결손 단계에 새 정상 영수증이 들어왔습니다. "
                    "과거 결손 원천이 복구됐다는 뜻은 아닙니다.")
                continue
            sample = (item.get("examples") or [{}])[0]
            messages.append(
                f'{item["status"]}: 기계·보조 AI 장중 원천결손 / '
                f'{item["count"]}건 (주문 수 아님)\n'
                f'원인: {json.dumps(item.get("issues", {}), ensure_ascii=False)[:500]}\n'
                f'대표: {sample.get("stock_code") or "미확인"} '
                f'{sample.get("route") or "경로 미확인"} '
                f'{sample.get("reason") or "원인 미확인"}\n'
                '정확한 판정 ID의 원천을 확인하고 기존 제한된 원천 보강 경로로 처리하세요.')
            continue
        if item["rule"] == "pre_submit_delay_intraday_source_gap":
            if item["status"] == "recovered":
                messages.append("pre_submit_delay의 새 원천 구간이 정상입니다. 과거 결손은 복원되지 않았습니다.")
            else:
                semantics = result.get("pre_submit_delay_source_semantics") or {}
                messages.append(
                    f'{item["status"]}: pre_submit_delay 장중 원천결손 / {item["count"]}건\n'
                    f'원인: {json.dumps(item.get("issues", {}), ensure_ascii=False)[:450]}\n'
                    f'대표: {json.dumps((item.get("examples") or [{}])[0], ensure_ascii=False)[:350]}\n'
                    f'원천 상태: {semantics.get("sources")} / 요약 PID: {semantics.get("summary_last_writer_pid")}\n'
                    '정확한 원천 ID와 호가 경로를 대조하세요. 자동 매매 변경은 없습니다.')
            continue
        example = (item.get("examples") or [{}])[0]
        cause = ((example.get("economic_source") or {}).get("blocker")
                 if item["rule"] == "economic_producer_gap" else
                 (example.get("source_invalid_decomposition") or {}).get("primary_blocker")
                 or next(iter(example.get("conflict_reasons") or []), None)
                 or example.get("final_state") or example.get("reason")
                 or next(iter(item.get("issues") or {}), None))
        cause_text = f"첫 결손: {str(cause)[:180]}\n" if cause else ""
        if item["rule"] == "economic_producer_gap":
            detail = (example.get("economic_source") or {}).get("capacity_blocker")
            cause_text += (f"판정: {example.get('mechanistic_action') or '미확인'} / "
                           f"조회 원인: {detail or '자금 조회 외 계약 결손 또는 구형 근거'}\n"
                           "후단 실행 재생 증거 결손입니다. 기계 튜닝 실패나 실제 주문 실패 건수가 아닙니다.\n")
        elif item["rule"] == "entry_execution_tuning_receipt_contract":
            axis = ", ".join(sorted({str(row.get("axis")) for row in item.get("examples", []) if row.get("axis")}))
            cause_text += f"대상 축: {axis or 'entry_split / pre_submit_delay'}\n"
            cause_text += "보고서의 후보 부족·source gap 자체는 오류나 EV 0으로 판정하지 않습니다.\n"
        messages.append(cause_text + f'{item["status"]}: {item["rule"]}\n{item["scope"]}\n근거 {item["count"]}건 / {item["category"]}\n' +
                        json.dumps(item.get("examples", [])[:1], ensure_ascii=False)[:350])
    active_keys = [key for key in keys[:4]
                   if _notification_kind(result["incidents"][key], result) == "active"]
    actionable = bool(active_keys)
    has_structural = any(result["incidents"][key].get("category") == "structural_evidence"
                         for key in active_keys)
    active_rules = {result["incidents"][key].get("rule") for key in active_keys}
    if not actionable and {result["incidents"][key].get("rule") for key in keys[:4]} == {
            "pre_submit_delay_intraday_source_gap"}:
        title = "매수 지연 원천 정상 관측"
    elif not actionable:
        title = "제출병목 정상 확인"
    elif not has_structural and active_rules == {"enter_now_scarcity"}:
        title = "기계판정 검토"
    elif not has_structural and active_rules <= {"enter_now_scarcity", "ai_veto_concentration"}:
        title = "진입판정 검토"
    elif active_rules == {"machine_auxiliary_intraday_source_gap"}:
        title = "판정 원천결손 점검"
    elif active_rules == {"pre_submit_delay_intraday_source_gap"}:
        title = "매수 지연 원천결손 점검"
    else:
        title = "제출병목 점검"
    message = f"[{title}] 자동 매매 변경 없음\n" + "\n".join(messages) + f"\n근거: {path}"
    if actionable:
        message += ("\n정확 경로의 수신·판정 원천을 대조하세요. 체결 희소를 API 결함으로 단정하지 않습니다."
                    if active_rules == {"machine_auxiliary_intraday_source_gap"}
                    else "\nCodex에서 원천과 제출 경로를 점검하세요."
                    if has_structural else "\n판정·기회비용 검토 신호이며 자동 매매 변경은 없습니다.")
    if send is None:
        try:
            token, admin = _load_telegram_config()
        except (OSError, ValueError):
            result["notification_status"] = "configuration_invalid"
            return
        if not token or not admin:
            result["notification_status"] = "configuration_missing"
            return
        send = lambda text: _send_telegram(token, admin, text)
    try:
        send(message[:4000])
    except Exception as exc:
        # Never leak a token-bearing HTTP exception into logs.
        result["notification_status"] = f"retry_required:{type(exc).__name__}"
        return
    for key in keys[:4]:
        if _notification_kind(result["incidents"][key], result) == "normal_observation":
            result["incidents"][key]["normal_observation_pending"] = False
            result["incidents"][key]["normal_observation_notified_at"] = result["as_of"]
        result["incidents"][key]["notified_status"] = result["incidents"][key]["status"]
    result["notification_status"] = "sent"
    result["last_notification_at"] = result["as_of"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--notify", action="store_true")
    parser.add_argument("--source-only", action="store_true",
                        help="Use current-day bounded probe/trace/pending receipts when Sentinel fails.")
    parser.add_argument("--delay-source-only", action="store_true",
                        help="Independently inspect current-day pre-submit source and producer summary.")
    parser.add_argument("--date", help="Exact KST date for independent source monitoring.")
    args = parser.parse_args()
    current = datetime.now(KST)
    if args.date and args.date != current.date().isoformat():
        parser.error("source_monitor_requires_current_kst_date")
    state_path = PROJECT_ROOT / "tmp" / ("pre_submit_delay_source_monitor_state.json" if args.delay_source_only
                                         else "submission_bottleneck_monitor_state.json")
    output = PROJECT_ROOT / "data/report/buy_funnel_sentinel" / (
        "pre_submit_delay_source_monitor_latest.json" if args.delay_source_only
        else "submission_bottleneck_monitor_latest.json")
    try:
        if args.report.stat().st_size > 8 * 1024 * 1024:
            raise ValueError("report_size_limit")
        report = json.loads(args.report.read_text())
        if not isinstance(report, dict):
            report = {}
    except (OSError, ValueError):
        report = {}
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        prior = _load_state(state_path)
        result = evaluate({} if args.source_only or args.delay_source_only else report,
                          prior, current)
        if args.delay_source_only:
            attach_pre_submit_delay_source_semantics(result, pre_submit_delay_source_semantics(
                PROJECT_ROOT / "data", result["as_of"], prior.get("pre_submit_delay_source_cursor")))
        elif not args.source_only:
            attach_machine_semantics(result, machine_semantics(PROJECT_ROOT / "data", result["as_of"]))
            attach_entry_execution_tuning_semantics(
                result, entry_execution_tuning_semantics(PROJECT_ROOT / "data", result["as_of"])
            )
        if not args.delay_source_only:
            attach_source_gap_semantics(result, source_gap_semantics(PROJECT_ROOT / "data", result["as_of"]))
        if args.notify:
            notify(result, output)
        _write_state(state_path, result)
        _write_state(output, result)
        name = ("pre_submit_delay_source_monitor" if args.delay_source_only else "submission_bottleneck_monitor")
        _write_state(output.with_name(f"{name}_{result['date']}.json"), result)
    print(json.dumps({**{k: result.get(k) for k in ("status", "blocker", "notification_status")},
                      "source_gap_status": (result.get("source_gap_semantics") or {}).get("status"),
                      "pre_submit_delay_source_status": (
                          result.get("pre_submit_delay_source_semantics") or {}).get("status")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
