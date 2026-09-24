from __future__ import annotations


import csv
import gzip
import glob
import hashlib
import json
import os
import time
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.utils.constants import PROJECT_ROOT
from src.utils.jsonl_io import existing_or_gzip_path
from src.utils.market_day import is_krx_trading_day

from src.engine.error_detectors.base import (
    BaseDetector,
    DetectionResult,
    register_detector,
)
from src.engine.error_detectors.schedule_contract import (
    evaluate_schedule_contract,
    load_installed_crontab,
)
from src.engine.error_detectors.cron_completion import CronCompletionDetector


def _today_kst_str(now_kst: datetime | None = None) -> str:
    return (now_kst or datetime.now()).strftime("%Y-%m-%d")


def _machine_result_semantics(root: Path, source_date: str) -> dict[str, Any]:
    """Check exact-date machine economics separately from stage completion."""
    report_path = (root / "data/report/ai_decision_action_outcome_calibration"
                   / f"ai_decision_action_outcome_calibration_{source_date}.json")
    if not (report_path.exists() or report_path.is_symlink()):
        # The scheduled artifact/cron owners detect absence. This semantic
        # check runs only after a report exists, including historical review.
        return {"status": "not_assessed", "findings": []}
    try:
        if report_path.is_symlink() or report_path.stat().st_size > 64 * 1024 * 1024:
            return {"status": "source_invalid", "findings": ["machine_report_untrusted_path_or_size"]}
        report = json.loads(report_path.read_text(encoding="utf-8"))
        declared = report.get("artifact_content_sha256")
        body = {key: value for key, value in report.items() if key != "artifact_content_sha256"}
        actual = hashlib.sha256(json.dumps(body, ensure_ascii=True, sort_keys=True,
            separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
        if report.get("target_date") != source_date or declared != actual:
            raise ValueError("machine_report_date_or_hash_invalid")
        scopes = (report.get("machine_full_evaluation") or {}).get("scope_evaluations")
        if not isinstance(scopes, dict):
            raise ValueError("machine_scope_evaluations_missing")
    except (OSError, UnicodeError, ValueError, TypeError, AttributeError) as exc:
        return {"status": "source_invalid", "findings": [str(exc)]}
    findings: list[str] = []
    scope_details: dict[str, dict[str, Any]] = {}
    for scope, row in scopes.items():
        if not isinstance(row, dict):
            findings.append("machine_scope_row_invalid")
            continue
        full = row.get("full_population_count")
        eligible = row.get("current_structure_eligible_count")
        paired = row.get("paired_comparable_count")
        exclusions = row.get("row_exclusion_reason_counts") or {}
        if not isinstance(exclusions, dict):
            findings.append("machine_exclusion_counts_invalid")
            continue
        invalid = exclusions.get("source_contract_invalid", 0)
        if (any(type(value) is not int or value < 0 for value in (full, eligible, invalid))
            or eligible > full or (paired is not None and (type(paired) is not int or paired < 0))):
            findings.append("machine_population_count_invalid")
            continue
        if not full and not invalid:
            continue
        scope_details[scope] = {"full": full, "eligible": eligible,
            "operating_paired": paired, "source_contract_invalid": invalid}
        if invalid:
            findings.append("machine_source_contract_exclusions")
        if full and not eligible:
            findings.append("machine_current_structure_empty")
        if eligible and not paired:
            findings.append("machine_operating_paired_unbound")
        if eligible and row.get("downstream_operating_evidence_complete") is not True:
            findings.append("machine_operating_economics_incomplete")
    compact_path = (root / "data/report/ai_entry_setup_paired_replay_batch"
                    / f"compact_auxiliary_paired_economic_{source_date}.source.json")
    compact_exclusions: dict[str, int] = {}
    compact_path = existing_or_gzip_path(compact_path)
    if compact_path.exists() or compact_path.is_symlink():
        try:
            if compact_path.is_symlink() or compact_path.stat().st_size > 64 * 1024 * 1024:
                findings.append("compact_projection_untrusted_path_or_size")
            else:
                opener = gzip.open if compact_path.suffix == ".gz" else open
                with opener(compact_path, "rt", encoding="utf-8") as handle:
                    compact_text = handle.read(64 * 1024 * 1024 + 1)
                if len(compact_text) > 64 * 1024 * 1024:
                    raise ValueError("compact_projection_uncompressed_size_exceeded")
                compact = json.loads(compact_text)
                if compact.get("target_date") != source_date or not isinstance(compact.get("rows"), list):
                    raise ValueError("compact_projection_date_or_rows_invalid")
                compact_hash = compact.get("artifact_content_sha256")
                compact_body = {k: v for k, v in compact.items() if k != "artifact_content_sha256"}
                actual_hash = hashlib.sha256(json.dumps(compact_body, ensure_ascii=False,
                    sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
                if compact_hash != actual_hash:
                    raise ValueError("compact_projection_hash_invalid")
                if any(not isinstance(row, dict) for row in compact["rows"]):
                    raise ValueError("compact_projection_rows_invalid")
                compact_exclusions = dict(Counter(str(row.get("exclusion_reason"))
                    for row in compact["rows"] if row.get("exclusion_reason")))
                if compact["rows"] and sum(compact_exclusions.values()) == len(compact["rows"]):
                    findings.append("compact_operating_rows_all_excluded")
        except (OSError, EOFError, UnicodeError, ValueError, TypeError, AttributeError):
            findings.append("compact_projection_invalid")
    winrate_path = (root / 'data/report/ai_decision_action_outcome_calibration'
                    / f'winrate_policy_{source_date}.json')
    if winrate_path.exists() or winrate_path.is_symlink():
        try:
            if winrate_path.is_symlink() or winrate_path.stat().st_size > 64 * 1024 * 1024:
                raise ValueError('winrate_report_untrusted_path_or_size')
            from src.engine.scalping import ai_action_outcome_calibration as calibration
            from src.engine.scalping import mechanistic_entry_runtime_policy as runtime_policy
            winrate = json.loads(winrate_path.read_text(encoding='utf-8'))
            if winrate.get('schema') == 'main_entry_winrate_policy_report_v1':
                if (not calibration._artifact_content_sha256_valid(winrate)
                    or winrate.get('target_date') != source_date
                    or winrate.get('selection_basis') != 'win_rate_only'):
                    findings.append('winrate_report_hash_or_scope_invalid')
                accepted = winrate.get('accepted_attempt_count')
                input_count = winrate.get('input_attempt_count')
                source_excluded = winrate.get('source_contract_excluded_count')
                excluded = winrate.get('excluded_attempt_counts') or {}
                if (type(input_count) is not int or input_count < 0
                    or type(accepted) is not int or accepted < 0
                    or type(source_excluded) is not int or source_excluded < 0
                    or any(type(v) is not int or v < 0 for v in excluded.values())
                    or accepted + source_excluded + sum(excluded.values()) != input_count
                    or sum((winrate.get('situation_attempt_counts') or {}).values()) != accepted):
                    findings.append('winrate_population_denominator_invalid')
                if not runtime_policy.winrate_market_census_valid(winrate):
                    findings.append('winrate_market_denominator_invalid')
                elif any(item['input_attempt_count'] == 0
                    for item in winrate['market_census'].values()):
                    findings.append('winrate_market_source_empty')
                disposition = winrate.get('disposition')
                if (disposition == 'successor_selected'
                    and not runtime_policy._winrate_successor_hurdles_valid(winrate)):
                    findings.append('winrate_successor_hurdle_invalid')
                if disposition in {'initial_adopted', 'successor_selected'}:
                    for part in ('train', 'holdout'):
                        metrics = (winrate.get('candidate') or {}).get(part) or {}
                        if (not metrics.get('selected_opportunity_count')
                            or metrics.get('win_rate_pct') is None
                            or metrics.get('support_adjusted_win_rate_pct') is None):
                            findings.append('winrate_selected_zero_or_undefined')
                terminal_path = winrate_path.with_name(f'winrate_policy_terminal_{source_date}.json')
                terminal = json.loads(terminal_path.read_text(encoding='utf-8'))
                target = (terminal.get('staged') or {}).get('target_date')
                if (not calibration._artifact_content_sha256_valid(terminal)
                    or terminal.get('report_sha256') != winrate.get('artifact_content_sha256')
                    or not isinstance(target, str)):
                    raise ValueError('winrate_terminal_binding_invalid')
                bundle = runtime_policy.load(data_root=root / 'data', target_date=target)
                selection = (bundle or {}).get('winrate_selection') or {}
                if (selection.get('report_sha256') != winrate.get('artifact_content_sha256')
                    or selection.get('disposition') != disposition
                    or selection.get('machine_policy_sha256') != runtime_policy.digest(bundle['machine_policy'])
                    or (bundle.get('scope_policies') or {}).get('KRX|KRX_REGULAR', {}).get('machine_disposition') != disposition):
                    findings.append('winrate_candidate_bundle_or_scope_mismatch')
            else:
                findings.append('winrate_report_schema_invalid')
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            findings.append('winrate_semantic_validation_failed')
    return {"status": "warning" if findings else "pass", "findings": sorted(set(findings)),
        "scopes": scope_details, "compact_exclusions": compact_exclusions}


def _reconcile_update_kospi_master_difference(
    payload: dict[str, Any],
    details: dict[str, Any],
) -> bool:
    """Accept only a fully verified, non-active eligibility difference.

    ``update_kospi`` deliberately preserves FDR rows even when the official
    ka10099 listing response does not return them.  That is a useful warning
    until the same-date canonical common-stock master proves every omitted
    code is outside the active trading universe.  Keep the reconciliation in
    the detector so the producer's raw warning and missing-code evidence stay
    intact.
    """

    if payload.get("status") != "completed_with_warnings":
        return False
    if payload.get("failed_steps") != []:
        return False
    if payload.get("warning_steps") != ["update_kospi_data"]:
        return False

    target_date_text = str(payload.get("target_date") or "").strip()
    try:
        target_date = date.fromisoformat(target_date_text)
    except ValueError:
        return False

    steps = payload.get("steps")
    if not isinstance(steps, list):
        return False
    update_steps = [
        step
        for step in steps
        if isinstance(step, dict) and step.get("name") == "update_kospi_data"
    ]
    if len(update_steps) != 1:
        return False
    update_step = update_steps[0]
    step_details = update_step.get("details")
    if not isinstance(step_details, dict):
        return False
    eligibility = step_details.get("eligibility")
    if (
        update_step.get("status") != "completed_with_warnings"
        or step_details.get("reason") != "market_eligibility_partial"
        or not isinstance(eligibility, dict)
        or eligibility.get("complete") is not True
        or eligibility.get("status") != "partial"
    ):
        return False

    market_meta = eligibility.get("market_source_meta")
    missing_codes = eligibility.get("missing_codes")
    requested_count = eligibility.get("requested_code_count")
    received_count = eligibility.get("received_code_count")
    if (
        not isinstance(market_meta, list)
        or {str(row.get("market")) for row in market_meta if isinstance(row, dict)}
        != {"0", "10"}
        or any(
            not isinstance(row, dict)
            or row.get("complete") is not True
            or row.get("continuous_next_key_missing") is True
            or row.get("continuous_page_limit_reached") is True
            for row in market_meta
        )
        or not isinstance(missing_codes, list)
        or not missing_codes
        or len({str(code) for code in missing_codes}) != len(missing_codes)
        or any(len(str(code)) != 6 or not str(code).isdigit() for code in missing_codes)
        or not isinstance(requested_count, int)
        or isinstance(requested_count, bool)
        or not isinstance(received_count, int)
        or isinstance(received_count, bool)
        or received_count + len(missing_codes) != requested_count
    ):
        return False

    master_path = existing_or_gzip_path(
        PROJECT_ROOT
        / "data/report/micro_reversion_economic_reference"
        / f"micro_reversion_symbol_master_{target_date_text}.json"
    )
    if not master_path.exists():
        return False

    try:
        from src.engine.scalping.micro_reversion.symbol_master import (
            SymbolLookupStatus,
            VerifiedSymbolMaster,
        )

        master = VerifiedSymbolMaster.from_json_path(
            master_path,
            require_canonical_owner=True,
        )
        allowed_statuses = {
            SymbolLookupStatus.MISSING,
            SymbolLookupStatus.OUTSIDE_EFFECTIVE_WINDOW,
        }
        lookup_statuses = {
            str(code): master.lookup(code, as_of=target_date).status
            for code in missing_codes
        }
    except (OSError, TypeError, ValueError):
        return False

    unresolved = {
        code: status.value
        for code, status in lookup_statuses.items()
        if status not in allowed_statuses
    }
    details["update_kospi_status_master_path"] = str(master_path)
    details["update_kospi_status_master_difference_count"] = len(missing_codes)
    details["update_kospi_status_master_difference_unresolved"] = unresolved
    if unresolved:
        return False
    details["update_kospi_status_warning_reconciliation"] = "benign_master_difference"
    return True


ARTIFACT_SCHEDULE_CONTRACTS: dict[str, dict[str, Any]] = {
    "pattern_lab_currentness_audit_report": {"markers": ["THRESHOLD_CYCLE_POSTCLOSE"], "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE", "parent_default_enabled": False},
    "pattern_lab_propagation_audit_report": {"markers": ["THRESHOLD_CYCLE_POSTCLOSE"], "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE", "parent_default_enabled": False},
    "codebase_performance_workorder_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT",
        "parent_default_enabled": False,
    },
    "codex_workorder_runner_report": {
        "markers": ["POSTCLOSE_DONE_CONTROLLER"],
        "parent_env_key": "POSTCLOSE_DONE_CONTROLLER_RUN_CODEX",
        "parent_default_enabled": False,
    },
    "swing_live_dry_run_status": {"markers": ["SWING_LIVE_DRY_RUN"]},
    "swing_selection_funnel_report": {"markers": ["SWING_LIVE_DRY_RUN"]},
    "swing_lifecycle_audit_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
    "swing_threshold_ai_review_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
    "swing_improvement_automation_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
    "swing_runtime_approval_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
    "swing_pattern_lab_automation_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
    "swing_model_retrain_diagnosis": {"markers": ["SWING_MODEL_RETRAIN_POSTCLOSE"]},
    "swing_bull_period_ai_review": {"markers": ["SWING_MODEL_RETRAIN_POSTCLOSE"]},
    "swing_model_retrain_report": {"markers": ["SWING_MODEL_RETRAIN_POSTCLOSE"]},
    "swing_model_retrain_status": {"markers": ["SWING_MODEL_RETRAIN_POSTCLOSE"]},
    "swing_model_registry_current": {"markers": ["SWING_MODEL_RETRAIN_POSTCLOSE"]},
    "swing_daily_simulation_status": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
    "swing_daily_simulation_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
}

ARTIFACT_TERMINAL_SKIP_CONTRACTS: dict[str, dict[str, str]] = {
    "codebase_performance_workorder_report": {
        "log": "logs/threshold_cycle_postclose_cron.log",
        "step": "codebase_performance_workorder",
    }
}


ARTIFACT_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "pipeline_events",
        "path_template": "data/pipeline_events/pipeline_events_{date}.jsonl",
        "max_staleness_sec": 600,
        "critical": True,
        "trading_day_only": True,
        "window_start": (9, 0),
        "window_end": (15, 30),
        "window_grace_sec": 300,
    },
    {
        "id": "threshold_events",
        "path_template": "data/threshold_cycle/threshold_events_{date}.jsonl",
        "partitioned_compact": {
            "checkpoint_template": "data/threshold_cycle/checkpoints/{date}.json",
            "partition_glob_template": "data/threshold_cycle/date={date}/family=*/part-*.jsonl*",
        },
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 0),
        "window_end": (15, 30),
        "window_grace_sec": 300,
    },
    {
        "id": "daily_recommendations_csv",
        "path_template": "data/daily_recommendations_v2.csv",
        "max_staleness_sec": 3600,
        "critical": False,
        "window_start": (7, 20),
        "window_end": (8, 0),
        "trading_day_only": True,
        "content_freshness": {
            "format": "csv",
            "date_field": "date",
            "max_age_days": 7,
            "min_rows": 1,
        },
    },
    {
        "id": "daily_recommendations_diag",
        "path_template": "data/daily_recommendations_v2_diagnostics.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "window_start": (7, 20),
        "window_end": (8, 0),
        "trading_day_only": True,
        "content_freshness": {
            "format": "json",
            "date_field": "latest_date",
            "max_age_days": 7,
            "min_count_field": "selected_count",
            "min_count": 1,
        },
    },
    {
        "id": "runtime_policy_bootstrap",
        "path_template": "data/runtime/policy_bootstrap/runtime_policy_bootstrap_{date}.json",
        "max_staleness_sec": 900,
        "critical": True,
        "window_start": (7, 35),
        "window_end": (7, 50),
        # The producer and the full detector are both installed at 07:35.
        # Allow one detector interval for the producer to replace the previous
        # evening's target-date handoff before treating it as stale.
        "window_grace_sec": 300,
        "trading_day_only": True,
    },
    {
        "id": "threshold_preopen_status",
        "path_template": "data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_{date}.status.json",
        "max_staleness_sec": 1800,
        "critical": True,
        "trading_day_only": True,
        "window_start": (7, 50),
        "window_end": (8, 5),
        "json_status_field": "status",
        "json_ok_values": ["succeeded"],
    },
    {
        "id": "submission_bottleneck_monitor",
        "first_required_date": "2026-09-21",
        "path_template": "data/report/buy_funnel_sentinel/submission_bottleneck_monitor_{date}.json",
        "max_staleness_sec": 600,
        "critical": True,
        "trading_day_only": True,
        "window_start": (8, 10),
        "window_end": (20, 0),
        "json_status_field": "notification_status",
        "json_ok_values": ["idle", "sent", "cooldown"],
    },
    {
        "id": "buy_funnel_sentinel_report",
        "path_template": "data/report/buy_funnel_sentinel/buy_funnel_sentinel_{date}.md",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 5),
        "window_end": (15, 30),
    },
    {
        "id": "bd_fbuy_accum_pre_artifact",
        "path_template": "data/runtime/bd_fbuy_accum_pre/BD_FBUY_ACCUM_PRE_V1_{date}.json",
        "max_staleness_sec": 900,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 5),
        "window_end": (15, 20),
        "json_status_field": "schema_version",
        "json_ok_values": ["BD_FBUY_ACCUM_PRE_V1"],
    },
    {
        "id": "holding_exit_sentinel_report",
        "path_template": "data/report/holding_exit_sentinel/holding_exit_sentinel_{date}.md",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 5),
        "window_end": (15, 30),
    },
    {
        "id": "panic_sell_defense_report",
        "path_template": "data/report/panic_sell_defense/panic_sell_defense_{date}.md",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 5),
        "window_end": (15, 30),
    },
    {
        "id": "market_panic_breadth_report",
        "path_template": "data/report/market_panic_breadth/market_panic_breadth_{date}.json",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 5),
        "window_end": (15, 30),
    },
    {
        "id": "runtime_approval_summary_report",
        "path_template": "data/report/runtime_approval_summary/runtime_approval_summary_{date}.json",
        "max_staleness_sec": 1800,
        "critical": True,
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
        "window_grace_sec": 1200,
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
            "process_patterns": [
                "deploy/run_threshold_cycle_postclose.sh",
                "run_threshold_cycle_postclose.sh",
            ],
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "threshold_postclose_status",
        "path_template": "data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_{date}.status.json",
        "max_staleness_sec": 3600,
        "critical": True,
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (21, 40),
        "window_end": (22, 10),
        "json_status_field": "status",
        "json_ok_values": ["succeeded"],
        "running_status_deadline": (23, 20),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
            "process_patterns": [
                "deploy/run_threshold_cycle_postclose.sh",
                "run_threshold_cycle_postclose.sh",
            ],
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "postclose_done_controller_report",
        "path_template": "data/report/postclose_done_controller/postclose_done_controller_{date}.json",
        "max_staleness_sec": 3600,
        "critical": True,
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 55),
        "window_grace_sec": 300,
        "json_status_field": "status",
        "json_ok_values": ["done", "dry_run_planned"],
        "suppress_missing_while_cron_in_progress": {
            "id": "postclose_done_controller",
            "log": "logs/postclose_done_controller_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "codex_workorder_runner_report",
        "path_template": "data/report/codex_workorder_runner/codex_workorder_runner_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 55),
        "json_status_field": "status",
        "json_ok_values": ["completed", "dry_run_planned"],
        "suppress_missing_while_cron_in_progress": {
            "id": "postclose_done_controller",
            "log": "logs/postclose_done_controller_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "code_improvement_workorder",
        "path_template": "docs/code-improvement-workorders/code_improvement_workorder_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
    },
    {
        "id": "pipeline_event_verbosity_report",
        "path_template": "data/report/pipeline_event_verbosity/pipeline_event_verbosity_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "observation_source_quality_audit_report",
        "path_template": "data/report/observation_source_quality_audit/observation_source_quality_audit_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "codebase_performance_workorder_report",
        "path_template": "data/report/codebase_performance_workorder/codebase_performance_workorder_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "system_metric_samples",
        "path_template": "logs/system_metric_samples.jsonl",
        "max_staleness_sec": 180,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 0),
        "window_end": (15, 30),
    },
    {
        "id": "swing_live_dry_run_status",
        "path_template": "data/report/swing_selection_funnel/status/swing_live_dry_run_{date}.status.json",
        "max_staleness_sec": 1800,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 15),
        "window_end": (20, 35),
        "json_status_field": "status",
        "json_ok_values": ["succeeded", "skipped"],
    },
    {
        "id": "swing_selection_funnel_report",
        "path_template": "data/report/swing_selection_funnel/swing_selection_funnel_{date}.md",
        "max_staleness_sec": 1800,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 15),
        "window_end": (20, 35),
    },
    {
        "id": "swing_lifecycle_audit_report",
        "path_template": "data/report/swing_lifecycle_audit/swing_lifecycle_audit_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
    },
    {
        "id": "swing_threshold_ai_review_report",
        "path_template": "data/report/swing_threshold_ai_review/swing_threshold_ai_review_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
    },
    {
        "id": "swing_improvement_automation_report",
        "path_template": "data/report/swing_improvement_automation/swing_improvement_automation_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
    },
    {
        "id": "swing_runtime_approval_report",
        "path_template": "data/report/swing_runtime_approval/swing_runtime_approval_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
    },
    {
        "id": "swing_pattern_lab_automation_report",
        "path_template": "data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
    },
    {
        "id": "pattern_lab_currentness_audit_report",
        "path_template": "data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "pattern_lab_propagation_audit_report",
        "path_template": "data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "swing_model_retrain_diagnosis",
        "path_template": "data/report/swing_model_retrain/diagnosis_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
    },
    {
        "id": "swing_bull_period_ai_review",
        "path_template": "data/report/swing_model_retrain/bull_period_ai_review_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
    },
    {
        "id": "swing_model_retrain_report",
        "path_template": "data/report/swing_model_retrain/swing_model_retrain_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
    },
    {
        "id": "swing_model_retrain_status",
        "path_template": "data/report/swing_model_retrain/status/swing_model_retrain_{date}.status.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
        "json_status_field": "status",
        "json_ok_values": ["succeeded", "skipped"],
    },
    {
        "id": "swing_model_registry_current",
        "path_template": "data/model_registry/swing_v2/current.json",
        "max_staleness_sec": 7776000,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
    },
    {
        "id": "swing_daily_simulation_status",
        "path_template": "data/report/swing_daily_simulation/status/swing_daily_simulation_{date}.status.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (21, 0),
        "window_end": (21, 50),
        "json_status_field": "status",
        "json_ok_values": ["succeeded", "skipped"],
    },
    {
        "id": "swing_daily_simulation_report",
        "path_template": "data/report/swing_daily_simulation/swing_daily_simulation_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (21, 0),
        "window_end": (21, 50),
    },
    {
        "id": "update_kospi_status",
        "path_template": "data/runtime/update_kospi_status/update_kospi_{date}.json",
        "max_staleness_sec": 1800,
        "critical": False,
        "trading_day_only": False,
        "window_start": (20, 5),
        "window_end": (21, 5),
        "json_status_field": "status",
        "json_ok_values": ["completed", "skipped_non_trading_day"],
    },
]


@register_detector
class ArtifactFreshnessDetector(BaseDetector):
    id = "artifact_freshness"
    name = "Artifact Freshness Detector"
    category = "artifact"

    def check(self) -> DetectionResult:
        now_dt = datetime.now()
        now_ts = time.time()
        now_h, now_m = _kst_time_tuple(now_dt)
        now_total = now_h * 60 + now_m
        source_day = getattr(self, "postclose_source_date", None)
        today = source_day or _today_kst_str(now_dt)
        past_source_day = bool(source_day and source_day < _today_kst_str(now_dt))
        if past_source_day:
            now_total = 24 * 60
        trading_day = is_krx_trading_day(datetime.strptime(today, "%Y-%m-%d").date())
        details: dict = {}
        issues: list[str] = []
        warnings: list[str] = []
        installed_crontab = load_installed_crontab()

        for artifact in ARTIFACT_REGISTRY:
            aid = artifact["id"]
            if today < artifact.get("first_required_date", "0001-01-01"):
                details[f"{aid}_status"] = "not_required_before_introduction"
                continue
            artifact_day = today
            artifact_now_total = now_total
            artifact_past_source_day = past_source_day
            if aid == "runtime_policy_bootstrap" and past_source_day:
                prepared = os.environ.get("POSTCLOSE_PREPARED_EFFECTIVE_DATE", "")
                try:
                    prepared_day = date.fromisoformat(prepared)
                    if prepared <= today or not is_krx_trading_day(prepared_day):
                        raise ValueError("invalid prepared date")
                except ValueError:
                    details[f"{aid}_status"] = "fail"
                    issues.append(f"{aid}: explicit prepared effective date missing or invalid")
                    continue
                details[f"{aid}_historical_source_date"] = today
                details[f"{aid}_prepared_effective_date"] = prepared
                if prepared > _today_kst_str(now_dt):
                    details[f"{aid}_status"] = "future_due"
                    continue
                artifact_day = prepared
                artifact_past_source_day = prepared < _today_kst_str(now_dt)
                artifact_now_total = 24 * 60 if artifact_past_source_day else now_h * 60 + now_m
            path_str = artifact["path_template"].replace("{date}", artifact_day)
            artifact_path = PROJECT_ROOT / path_str
            artifact_path = existing_or_gzip_path(artifact_path)
            critical = artifact.get("critical", False)
            max_stale = artifact.get("max_staleness_sec", 600)
            trading_day_only = artifact.get("trading_day_only", False)
            ws = artifact.get("window_start")
            we = artifact.get("window_end")

            if trading_day_only and not trading_day:
                details[f"{aid}_status"] = "skip_non_trading_day"
                continue

            schedule_contract = ARTIFACT_SCHEDULE_CONTRACTS.get(aid)
            if schedule_contract:
                schedule_status, schedule_details = evaluate_schedule_contract(
                    installed_crontab,
                    **schedule_contract,
                )
                details[f"{aid}_schedule_contract"] = schedule_details
                if schedule_status.startswith("disabled_"):
                    details[f"{aid}_status"] = schedule_status
                    continue

            ws_total = ws[0] * 60 + ws[1] if ws else None

            if ws_total is not None and artifact_now_total < ws_total:
                details[f"{aid}_status"] = "not_yet_due"
                details[f"{aid}_window"] = f"{ws[0]:02d}:{ws[1]:02d}"
                continue

            past_window_end = False
            if we is not None:
                window_end = now_dt.replace(
                    hour=we[0], minute=we[1], second=0, microsecond=0
                )
                past_window_end = artifact_past_source_day or now_dt >= window_end
            exists = artifact_path.exists()
            grace_sec = int(artifact.get("window_grace_sec") or 0)
            in_startup_grace = False
            if grace_sec > 0 and ws and not past_window_end:
                window_start = now_dt.replace(
                    hour=ws[0], minute=ws[1], second=0, microsecond=0
                )
                elapsed_from_start = (now_dt - window_start).total_seconds()
                in_startup_grace = 0 <= elapsed_from_start <= grace_sec
            if not exists and in_startup_grace:
                details[f"{aid}_status"] = "startup_grace"
                details[f"{aid}_window"] = f"{ws[0]:02d}:{ws[1]:02d}"
                details[f"{aid}_grace_sec"] = grace_sec
                continue

            if not exists:
                terminal_skip = self._terminal_skip_status(aid, artifact_day)
                if terminal_skip:
                    details[f"{aid}_status"] = "pass_terminal_skip"
                    details[f"{aid}_terminal_skip"] = terminal_skip
                    continue
                alternate_status = self._validate_partitioned_compact(
                    artifact,
                    artifact_day,
                    details,
                )
                if alternate_status:
                    status, warning = alternate_status
                    details[f"{aid}_status"] = status
                    if warning:
                        warnings.append(warning)
                    continue

                in_progress_cron = self._is_upstream_cron_in_progress(
                    artifact.get("suppress_missing_while_cron_in_progress"),
                    artifact_day,
                )
                if in_progress_cron and not past_window_end:
                    warnings.append(
                        f"{aid}: upstream cron in progress; artifact not generated yet"
                    )
                    details[f"{aid}_status"] = "warning"
                    details[f"{aid}_upstream_status"] = "in_progress"
                    continue
                if (
                    in_progress_cron
                    and past_window_end
                    and bool(
                        artifact.get(
                            "allow_missing_after_window_while_cron_in_progress"
                        )
                    )
                ):
                    warnings.append(
                        f"{aid}: upstream cron still in progress after window end"
                    )
                    details[f"{aid}_status"] = "warning"
                    details[f"{aid}_upstream_status"] = "in_progress_after_window"
                    continue
                if past_window_end:
                    if critical:
                        issues.append(f"{aid}: missing after window end")
                        details[f"{aid}_status"] = "fail"
                    else:
                        warnings.append(f"{aid}: not generated within window")
                        details[f"{aid}_status"] = "warning"
                else:
                    if critical:
                        issues.append(f"{aid}: {path_str} missing")
                        details[f"{aid}_status"] = "fail"
                    else:
                        warnings.append(f"{aid}: {path_str} not found")
                        details[f"{aid}_status"] = "warning"
                continue

            mtime = artifact_path.stat().st_mtime
            age_sec = now_ts - mtime
            details[f"{aid}_age_sec"] = round(age_sec, 1)
            json_error = self._validate_json_artifact(artifact_path)
            if json_error:
                details[f"{aid}_content_status"] = "invalid_json"
                message = f"{aid}: invalid JSON ({json_error})"
                if critical:
                    issues.append(message)
                    details[f"{aid}_status"] = "fail"
                else:
                    warnings.append(message)
                    details[f"{aid}_status"] = "warning"
                continue
            status_warning = self._validate_json_status(
                artifact, artifact_path, details
            )
            if status_warning:
                if self._is_bounded_postclose_running(
                    artifact, artifact_path, artifact_day, now_dt
                ):
                    warnings.append(
                        f"{aid}: exact-date postclose still running before deadline"
                    )
                    details[f"{aid}_status"] = "warning"
                    details[f"{aid}_upstream_status"] = "running_before_deadline"
                    details[f"{aid}_running_deadline"] = "23:20"
                    continue
                if critical:
                    issues.append(status_warning)
                    details[f"{aid}_status"] = "fail"
                else:
                    warnings.append(status_warning)
                    details[f"{aid}_status"] = "warning"
                continue
            content_warning, content_passed = self._validate_content_freshness(
                artifact,
                artifact_path,
                details,
                now_dt,
            )
            if content_warning:
                warnings.append(content_warning)
                details[f"{aid}_status"] = "warning"
                continue
            if content_passed:
                details[f"{aid}_status"] = "pass_content_date"
                continue

            if artifact.get("one_shot"):
                details[f"{aid}_status"] = "pass_one_shot"
                continue

            if past_window_end:
                details[f"{aid}_status"] = "pass_after_window"
                continue

            if age_sec > max_stale:
                if in_startup_grace:
                    details[f"{aid}_status"] = "startup_grace"
                    details[f"{aid}_window"] = f"{ws[0]:02d}:{ws[1]:02d}" if ws else ""
                    details[f"{aid}_grace_sec"] = grace_sec
                    details[f"{aid}_startup_stale_suppressed"] = True
                    continue
                if critical:
                    issues.append(f"{aid}: stale ({age_sec:.0f}s > {max_stale}s)")
                    details[f"{aid}_status"] = "fail"
                else:
                    warnings.append(f"{aid}: stale ({age_sec:.0f}s > {max_stale}s)")
                    details[f"{aid}_status"] = "warning"
            else:
                details[f"{aid}_status"] = "pass"

        if trading_day:
            machine_semantics = _machine_result_semantics(PROJECT_ROOT, today)
            details["machine_result_semantics"] = machine_semantics
            if machine_semantics["findings"]:
                warnings.append("machine_result_semantics: " + ", ".join(machine_semantics["findings"]))

        severity, summary = self._classify(issues, warnings)
        return DetectionResult(
            detector_id=self.id,
            category=self.category,
            severity=severity,
            summary=summary,
            details=details,
            recommended_action=self._recommend_action(severity, issues),
        )

    @staticmethod
    def _terminal_skip_status(aid: str, today: str) -> dict[str, str] | None:
        contract = ARTIFACT_TERMINAL_SKIP_CONTRACTS.get(aid)
        if not contract:
            return None
        log_path = PROJECT_ROOT / contract["log"]
        if not log_path.exists():
            return None
        try:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[
                -5000:
            ]
        except OSError:
            return None
        step_token = f"step={contract['step']}"
        for line in reversed(lines):
            if (
                "[SKIP]" in line
                and f"target_date={today}" in line
                and step_token in line
            ):
                return {
                    "log": contract["log"],
                    "step": contract["step"],
                    "marker": line.strip(),
                }
        return None

    @staticmethod
    def _classify(issues: list[str], warnings: list[str]) -> tuple[str, str]:
        if issues:
            return "fail", f"Artifact failures: {'; '.join(issues[:5])}"
        if warnings:
            return "warning", f"Artifact warnings: {'; '.join(warnings[:5])}"
        return "pass", "All critical artifacts fresh."

    @staticmethod
    def _recommend_action(severity: str, issues: list[str]) -> str:
        if severity == "fail":
            return f"Check missing/stale artifacts: {'; '.join(issues[:3])}"
        if severity == "warning":
            return "Non-critical artifacts missing/stale. Monitor next cycle."
        return ""

    @staticmethod
    def _is_bounded_postclose_running(
        artifact: dict[str, Any], artifact_path: Path, today: str, now: datetime
    ) -> bool:
        # Only the postclose owner can be pending here, never a failed status,
        # a prior-day recovery, a generic live process, or an unbounded wait.
        if (
            artifact.get("id") != "threshold_postclose_status"
            or artifact.get("running_status_deadline") != (23, 20)
            or today != now.date().isoformat()
            or (now.hour, now.minute) >= (23, 20)
        ):
            return False
        try:
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            if (
                not isinstance(payload, dict)
                or type(payload.get("schema_version")) is not int
                or payload.get("schema_version") != 1
                or payload.get("report_type") != "threshold_cycle_postclose_status"
                or payload.get("runtime_effect") is not False
                or payload.get("status") != "running"
                or payload.get("target_date") != today
                or payload.get("reason") != "started"
                or type(payload.get("exit_code")) is not int
                or payload["exit_code"] != 0
            ):
                return False
            started = datetime.fromisoformat(payload["started_at"])
            if (
                started.date().isoformat() != today
                or started.timestamp() > now.timestamp()
            ):
                return False
        except (OSError, ValueError, TypeError, KeyError):
            return False
        config = artifact.get("suppress_missing_while_cron_in_progress")
        if not isinstance(config, dict) or not config.get("log"):
            return False
        # A live PID alone must not hide a newer FAIL/DONE or another date.
        markers = CronCompletionDetector._read_once_markers(
            PROJECT_ROOT / config["log"], today
        )
        if not (
            ("[START]" in markers.upper() or "[BEGIN]" in markers.upper())
            and CronCompletionDetector._last_terminal_marker(markers) == "none"
        ):
            return False
        return ArtifactFreshnessDetector._has_matching_live_process(
            config, target_date=today
        )

    @staticmethod
    def _is_upstream_cron_in_progress(config: Any, today: str) -> bool:
        if not isinstance(config, dict):
            return False
        if ArtifactFreshnessDetector._has_matching_live_process(config):
            return True
        log_value = str(config.get("log") or "").strip()
        if not log_value:
            return False
        log_path = PROJECT_ROOT / log_value
        if not log_path.exists():
            return False
        # Reuse the cron owner's exact-date, latest-run and rotated-log
        # contract. Verbose JSON must not evict START; prior-day recovery DONE
        # or an older failed attempt must not terminate the current run.
        markers = CronCompletionDetector._read_once_markers(log_path, today)
        has_start = "[START]" in markers.upper() or "[BEGIN]" in markers.upper()
        return (
            has_start
            and CronCompletionDetector._last_terminal_marker(markers) == "none"
        )

    @staticmethod
    def _has_matching_live_process(
        config: dict[str, Any], *, target_date: str | None = None
    ) -> bool:
        patterns_raw = config.get("process_patterns")
        if not isinstance(patterns_raw, list):
            return False
        patterns = [
            str(pattern).strip() for pattern in patterns_raw if str(pattern).strip()
        ]
        if not patterns:
            return False
        proc_root = Path("/proc")
        try:
            proc_entries = list(proc_root.iterdir())
        except OSError:
            return False
        current_pid = os.getpid()
        for entry in proc_entries:
            if not entry.name.isdigit():
                continue
            try:
                pid = int(entry.name)
            except ValueError:
                continue
            if pid == current_pid:
                continue
            try:
                raw_cmdline = (entry / "cmdline").read_bytes()
            except OSError:
                continue
            if target_date is not None:
                argv = raw_cmdline.decode("utf-8", errors="replace").split("\x00")
                for index, arg in enumerate(argv[:-1]):
                    name = Path(arg).name
                    is_wrapper = name == "run_threshold_cycle_postclose.sh" or (
                        name.startswith(".run_threshold_cycle_postclose.snapshot.")
                        and name.endswith(".sh")
                    )
                    if is_wrapper and argv[index + 1] == target_date:
                        return True
                continue
            cmdline = raw_cmdline.replace(b"\x00", b" ").decode(
                "utf-8", errors="replace"
            )
            if cmdline and any(pattern in cmdline for pattern in patterns):
                return True
        return False

    @staticmethod
    def _validate_partitioned_compact(
        artifact: dict[str, Any],
        today: str,
        details: dict[str, Any],
    ) -> tuple[str, str] | None:
        config = artifact.get("partitioned_compact")
        if not isinstance(config, dict):
            return None

        aid = str(artifact["id"])
        checkpoint_template = str(config.get("checkpoint_template") or "").strip()
        partition_glob_template = str(
            config.get("partition_glob_template") or ""
        ).strip()
        if not checkpoint_template or not partition_glob_template:
            return "warning", f"{aid}: partitioned compact detector config incomplete"

        checkpoint_path = PROJECT_ROOT / checkpoint_template.replace("{date}", today)
        partition_glob = partition_glob_template.replace("{date}", today)
        if Path(partition_glob).is_absolute():
            partition_paths = sorted(Path(path) for path in glob.glob(partition_glob))
        else:
            partition_paths = sorted(PROJECT_ROOT.glob(partition_glob))
        partition_paths = [
            path
            for path in partition_paths
            if path.name.endswith((".jsonl", ".jsonl.gz"))
        ]

        details[f"{aid}_legacy_path_missing"] = True
        details[f"{aid}_partitioned_checkpoint_path"] = str(checkpoint_path)
        details[f"{aid}_partitioned_part_count"] = len(partition_paths)

        if not checkpoint_path.exists():
            return "warning", f"{aid}: partitioned checkpoint missing"
        if not partition_paths:
            return "warning", f"{aid}: partitioned compact parts missing"

        try:
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        except Exception as exc:
            details[f"{aid}_partitioned_checkpoint_status"] = "invalid_json"
            return "warning", f"{aid}: invalid partitioned checkpoint ({exc})"

        completed = bool(checkpoint.get("completed"))
        status = str(checkpoint.get("status") or checkpoint.get("state") or "").strip()
        paused_reason = checkpoint.get("paused_reason")
        written_count = checkpoint.get("written_count", checkpoint.get("written_total"))

        details[f"{aid}_partitioned_checkpoint_status"] = status or "unknown"
        details[f"{aid}_partitioned_completed"] = completed
        details[f"{aid}_partitioned_written_count"] = written_count
        if paused_reason:
            details[f"{aid}_partitioned_paused_reason"] = paused_reason

        if not completed:
            reason = f" paused_reason={paused_reason}" if paused_reason else ""
            return (
                "warning",
                f"{aid}: partitioned compact checkpoint incomplete{reason}",
            )

        latest_mtime = max(path.stat().st_mtime for path in partition_paths)
        details[f"{aid}_age_sec"] = round(time.time() - latest_mtime, 1)
        return "pass_partitioned_checkpoint", ""

    @staticmethod
    def _validate_json_status(
        artifact: dict[str, Any],
        artifact_path: Path,
        details: dict[str, Any],
    ) -> str:
        status_field = artifact.get("json_status_field")
        if not status_field:
            return ""

        aid = artifact["id"]
        ok_values = {str(v) for v in artifact.get("json_ok_values", [])}
        try:
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        except Exception as exc:
            details[f"{aid}_content_status"] = "invalid_json"
            return f"{aid}: invalid status JSON ({exc})"

        current: Any = payload
        for part in str(status_field).split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                details[f"{aid}_content_status"] = "missing_status_field"
                return f"{aid}: missing JSON status field {status_field}"

        status_value = str(current)
        details[f"{aid}_content_status"] = status_value
        if (
            aid == "update_kospi_status"
            and status_value == "completed_with_warnings"
            and _reconcile_update_kospi_master_difference(payload, details)
        ):
            return ""
        if ok_values and status_value not in ok_values:
            return f"{aid}: JSON status is {status_value}"
        return ""

    @staticmethod
    def _validate_json_artifact(artifact_path: Path) -> str:
        if artifact_path.suffix != ".json":
            return ""
        try:
            json.loads(artifact_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return str(exc)
        return ""

    @staticmethod
    def _validate_content_freshness(
        artifact: dict[str, Any],
        artifact_path: Path,
        details: dict[str, Any],
        now_dt: datetime,
    ) -> tuple[str, bool]:
        config = artifact.get("content_freshness")
        if not isinstance(config, dict):
            return "", False

        aid = artifact["id"]
        data_format = str(config.get("format") or "").strip().lower()
        try:
            payload = ArtifactFreshnessDetector._load_content_payload(
                data_format, artifact_path
            )
        except Exception as exc:
            details[f"{aid}_content_status"] = "invalid_content"
            return f"{aid}: invalid content freshness payload ({exc})", False

        min_rows = config.get("min_rows")
        if (
            min_rows is not None
            and isinstance(payload, list)
            and len(payload) < int(min_rows)
        ):
            details[f"{aid}_content_status"] = "insufficient_rows"
            details[f"{aid}_content_rows"] = len(payload)
            return f"{aid}: insufficient rows ({len(payload)} < {int(min_rows)})", False
        if isinstance(payload, list):
            details[f"{aid}_content_rows"] = len(payload)

        min_count_field = str(config.get("min_count_field") or "").strip()
        if min_count_field:
            count_value = ArtifactFreshnessDetector._resolve_field(
                payload, min_count_field
            )
            try:
                count_int = int(count_value)
            except (TypeError, ValueError):
                details[f"{aid}_content_status"] = "invalid_count"
                return f"{aid}: invalid count field {min_count_field}", False
            details[f"{aid}_{min_count_field}"] = count_int
            min_count = int(config.get("min_count") or 0)
            if count_int < min_count:
                details[f"{aid}_content_status"] = "insufficient_count"
                return (
                    f"{aid}: insufficient {min_count_field} ({count_int} < {min_count})",
                    False,
                )

        date_field = str(config.get("date_field") or "").strip()
        if not date_field:
            details[f"{aid}_content_status"] = "pass"
            return "", True
        raw_date = ArtifactFreshnessDetector._resolve_field(payload, date_field)
        content_date = ArtifactFreshnessDetector._parse_date_value(raw_date)
        if content_date is None:
            details[f"{aid}_content_status"] = "invalid_date"
            return f"{aid}: invalid content date field {date_field}", False

        age_days = (now_dt.date() - content_date.date()).days
        max_age_days = int(config.get("max_age_days") or 0)
        details[f"{aid}_content_date"] = content_date.date().isoformat()
        details[f"{aid}_content_age_days"] = age_days
        if age_days < 0:
            details[f"{aid}_content_status"] = "future_date"
            return (
                f"{aid}: content date is in the future ({content_date.date().isoformat()})",
                False,
            )
        if max_age_days >= 0 and age_days > max_age_days:
            details[f"{aid}_content_status"] = "stale_date"
            return f"{aid}: content date stale ({age_days}d > {max_age_days}d)", False

        details[f"{aid}_content_status"] = "pass"
        return "", True

    @staticmethod
    def _load_content_payload(data_format: str, artifact_path: Path) -> Any:
        if data_format == "json":
            return json.loads(artifact_path.read_text(encoding="utf-8"))
        if data_format == "csv":
            with artifact_path.open("r", encoding="utf-8-sig", newline="") as handle:
                return list(csv.DictReader(handle))
        raise ValueError(f"unsupported content freshness format: {data_format}")

    @staticmethod
    def _resolve_field(payload: Any, field_path: str) -> Any:
        current = payload[0] if isinstance(payload, list) and payload else payload
        for part in field_path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    @staticmethod
    def _parse_date_value(value: Any) -> datetime | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        if " " in text and "T" not in text:
            text = text.split(" ", 1)[0]
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            pass
        for fmt in ("%Y%m%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None


def _kst_time_tuple(now_kst: datetime | None = None) -> tuple[int, int]:
    now_kst = now_kst or datetime.now()
    return now_kst.hour, now_kst.minute
