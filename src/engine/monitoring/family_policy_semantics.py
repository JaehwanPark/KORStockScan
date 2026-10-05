"""Small sealed Widget/Episode projections, owned by their report producers.

This is monitoring evidence, not selection or trading authority. Full reports
are summarized once by the producer; periodic monitoring never runs a grid.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from src.utils.jsonl_io import write_json_object_generation_safe

SCHEMA = 'family_policy_semantic_projection_v1'
CONTRACT = dict(metric_role='source_quality_gate', decision_authority='report_only',
    window_policy='exact_source_date_and_published_family_generation',
    sample_floor='native_family_selection_floor_not_a_monitoring_floor',
    primary_decision_metric='native_family_paired_ev_with_diagnostic_win_rate',
    source_quality_gate='sealed_report_policy_and_producer_generation',
    forbidden_uses=['orders', 'threshold_changes', 'custody_changes', 'quarantine_release', 'profit_imputation'])


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=True, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def seal(value):
    body = {k: v for k, v in value.items() if k != 'receipt_sha256'}
    return dict(body, receipt_sha256=digest(body))


def file_sha(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 128 * 1024 * 1024:
        raise ValueError('family_semantic_source_untrusted_or_oversized')
    before = path.stat()
    sha = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(128 * 1024), b''):
            sha.update(chunk)
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
        after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError('semantic_generation_changed_during_read')
    return sha.hexdigest()


def projection_path(report_path, family, day):
    return Path(report_path).parent / f'{family}_policy_semantics_{day}.json'


def widget_summary(report):
    rows = []
    for symbol, source in sorted((report.get('symbols') or {}).items()):
        for session, value in sorted((source.get('sessions') or {}).items()):
            paired = value.get('paired_economics') or {}
            study, selection = paired.get('study') or {}, paired.get('selection') or {}
            execution = (source.get('execution_quality_by_session') or {}).get(session) or {}
            events = execution.get('event_counts') or {}
            rows.append(dict(symbol=symbol, session=session,
                cohort='samsung' if symbol == '005930' else 'non_samsung',
                disposition=value.get('decision'), evidence_state=selection.get('evidence_state'),
                source_rows=source.get('source_row_count'), replay_source={k: (study.get('source_audit') or {}).get(k)
                    for k in ('exact_input_count', 'raw_record_count', 'replay_input_occurrences',
                        'duplicate_input_occurrences', 'invalid_source_rows', 'conflicting_observations',
                        'target_date', 'target_date_sessions', 'raw_state_counts', 'quote_valid_count')},
                study_status=study.get('status'), pair_count=study.get('paired_opportunity_count'),
                candidates=len(study.get('candidates') or []),
                candidate_ready=selection.get('candidate_ready') is True,
                gate_reasons=selection.get('path_exclusion_reasons') or [],
                comparable_windows=selection.get('diagnostics') or [],
                scale_in_source_census=study.get('scale_in_source_census'),
                # Counts remain in the native symbol/session window, never Main
                # counts or a unique-order count masquerading as fill quantity.
                execution=dict(scope=execution.get('execution_event_scope'), events=events,
                    submit_failed=execution.get('order_submit_failed_count'),
                    ambiguous=execution.get('order_submit_ambiguous_count'),
                    terminal_failed=execution.get('terminal_execution_failure_count'))))
    return dict(ready_sessions=report.get('ready_session_policy_count'),
        carried_sessions=report.get('carried_forward_session_policy_count'),
        selected_sessions=report.get('statistically_ready_session_policy_count'),
        source_census_reconciliation=report.get('source_census_reconciliation'),
        rows=rows, actual_pid_consumed=False, realized_profit=None)


def episode_summary(report):
    search = report.get('paired_economic_search') or {}
    daily = (report.get('daily') or {}).get('profiles') or {}
    profiles = search.get('profiles') or {}
    if isinstance(profiles, list):
        profiles = {p['profile_id']: p for p in profiles}
    rows = []
    for pid, value in sorted(profiles.items()):
        source = daily.get(pid) or {}
        capture = (source.get('durable_observation_capture') or {}).get('profile') or {}
        rows.append(dict(profile_id=pid, symbol=source.get('symbol'), session=source.get('session'),
            cohort='samsung' if source.get('symbol') == '005930' else 'non_samsung',
            disposition=value.get('disposition'),
            research_disposition=value.get('research_disposition'),
            promotion_disposition=value.get('promotion_disposition'),
            gate_reasons=value.get('promotion_blocking_reasons') or [],
            completed_legs=value.get('completed_actual_legs'), held_legs=value.get('actual_held_legs'),
            source_valid_days=value.get('actual_source_valid_days'), source_quality=source.get('source_quality'),
            source_reason=source.get('source_quality_reasons') or source.get('reason'),
            capture=capture, policy_hash=source.get('policy_hash'),
            # Native leg rows preserve partial/carry/manual/cost attribution.
            legs=source.get('legs') or [], actual_economics=source.get('broker_realized_economics')))
    manifest = report.get('durable_observation_manifest') or {}
    return dict(stage_counts=search.get('stage_counts'),
        dispositions=dict(Counter(r['disposition'] for r in rows)), rows=rows,
        capture_manifest={k: manifest.get(k) for k in ('status', 'event_count', 'expected_event_count',
            'valid_event_count', 'invalid_event_count', 'invalid_reasons', 'source_sha256', 'source_generation')},
        actual_pid_consumed=False, realized_profit=None)


def publish(report, policy, *, report_path, policy_path, family, producer_path):
    if family not in {'widget', 'episode'}:
        raise ValueError('family_semantic_owner_invalid')
    day = report['target_date']
    # Summarize exactly the generation on disk. A competing publisher cannot
    # attach this in-memory summary to different report/policy bytes.
    report_sha, policy_sha = file_sha(report_path), file_sha(policy_path)
    if json.loads(Path(report_path).read_text()) != report or json.loads(Path(policy_path).read_text()) != policy:
        raise ValueError('semantic_generation_changed_during_read')
    summary = widget_summary(report) if family == 'widget' else episode_summary(report)
    value = seal(dict(schema=SCHEMA, family=family, source_date=day,
        target_date=policy.get('effective_date') or policy.get('target_date'),
        metric_contract=CONTRACT, runtime_effect=False, actual_order_submitted=False,
        report=dict(path=str(Path(report_path).resolve()), sha256=report_sha),
        policy=dict(path=str(Path(policy_path).resolve()), sha256=policy_sha),
        producer_kernels={str(Path(p).resolve()): file_sha(p) for p in (producer_path, __file__)},
        summary=summary))
    if file_sha(report_path) != report_sha or file_sha(policy_path) != policy_sha:
        raise ValueError('semantic_generation_changed_during_read')
    path = projection_path(report_path, family, day)
    write_json_object_generation_safe(path, value)
    return path
