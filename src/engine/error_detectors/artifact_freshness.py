from __future__ import annotations

import csv
import glob
import json
import os
import time
from datetime import datetime
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


def _today_kst_str(now_kst: datetime | None = None) -> str:
    return (now_kst or datetime.now()).strftime("%Y-%m-%d")


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
            "partition_glob_template": "data/threshold_cycle/date={date}/family=*/part-*.jsonl",
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
        "id": "threshold_runtime_env",
        "path_template": "data/threshold_cycle/runtime_env/threshold_runtime_env_{date}.json",
        "max_staleness_sec": 900,
        "critical": True,
        "window_start": (7, 35),
        "window_end": (7, 50),
        "trading_day_only": True,
    },
    {
        "id": "threshold_apply_plan",
        "path_template": "data/threshold_cycle/apply_plans/threshold_apply_{date}.json",
        "max_staleness_sec": 900,
        "critical": True,
        "window_start": (7, 35),
        "window_end": (7, 50),
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
        "id": "panic_buying_report",
        "path_template": "data/report/panic_buying/panic_buying_{date}.md",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 5),
        "window_end": (15, 30),
    },
    {
        "id": "openai_ws_stability_report",
        "path_template": "data/report/openai_ws/openai_ws_stability_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (16, 10),
        "window_end": (17, 10),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "threshold_postclose_report",
        "path_template": "data/report/threshold_cycle_ev/threshold_cycle_ev_{date}.json",
        "max_staleness_sec": 1800,
        "critical": True,
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (16, 10),
        "window_end": (17, 0),
        "window_grace_sec": 1200,
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "threshold_postclose_status",
        "path_template": "data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_{date}.status.json",
        "max_staleness_sec": 3600,
        "critical": True,
        "trading_day_only": True,
        "window_start": (17, 0),
        "window_end": (17, 30),
        "json_status_field": "status",
        "json_ok_values": ["succeeded"],
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
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
        "window_start": (16, 5),
        "window_end": (20, 5),
        "json_status_field": "status",
        "json_ok_values": ["done", "dry_run_planned"],
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
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
        "window_start": (16, 5),
        "window_end": (20, 5),
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
        "window_start": (16, 10),
        "window_end": (17, 0),
    },
    {
        "id": "pipeline_event_verbosity_report",
        "path_template": "data/report/pipeline_event_verbosity/pipeline_event_verbosity_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (16, 10),
        "window_end": (17, 0),
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
        "window_start": (16, 10),
        "window_end": (17, 0),
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
        "window_start": (16, 10),
        "window_end": (17, 0),
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
        "window_start": (15, 45),
        "window_end": (16, 5),
        "json_status_field": "status",
        "json_ok_values": ["succeeded", "skipped"],
    },
    {
        "id": "swing_selection_funnel_report",
        "path_template": "data/report/swing_selection_funnel/swing_selection_funnel_{date}.md",
        "max_staleness_sec": 1800,
        "critical": False,
        "trading_day_only": True,
        "window_start": (15, 45),
        "window_end": (16, 5),
    },
    {
        "id": "swing_lifecycle_audit_report",
        "path_template": "data/report/swing_lifecycle_audit/swing_lifecycle_audit_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (16, 10),
        "window_end": (17, 10),
    },
    {
        "id": "swing_threshold_ai_review_report",
        "path_template": "data/report/swing_threshold_ai_review/swing_threshold_ai_review_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (16, 10),
        "window_end": (17, 10),
    },
    {
        "id": "swing_improvement_automation_report",
        "path_template": "data/report/swing_improvement_automation/swing_improvement_automation_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (16, 10),
        "window_end": (17, 10),
    },
    {
        "id": "swing_runtime_approval_report",
        "path_template": "data/report/swing_runtime_approval/swing_runtime_approval_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (16, 10),
        "window_end": (17, 10),
    },
    {
        "id": "scalping_pattern_lab_automation_report",
        "path_template": "data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (16, 10),
        "window_end": (17, 10),
    },
    {
        "id": "scalp_entry_action_decision_matrix_report",
        "path_template": "data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (16, 10),
        "window_end": (17, 10),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "lifecycle_decision_matrix_report",
        "path_template": "data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (16, 10),
        "window_end": (17, 10),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "swing_pattern_lab_automation_report",
        "path_template": "data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (16, 10),
        "window_end": (17, 10),
    },
    {
        "id": "pattern_lab_currentness_audit_report",
        "path_template": "data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (16, 10),
        "window_end": (17, 10),
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
        "window_start": (16, 10),
        "window_end": (17, 10),
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
        "window_start": (21, 0),
        "window_end": (21, 50),
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
        today = _today_kst_str(now_dt)
        trading_day = is_krx_trading_day(now_dt.date())
        details: dict = {}
        issues: list[str] = []
        warnings: list[str] = []

        for artifact in ARTIFACT_REGISTRY:
            aid = artifact["id"]
            path_str = artifact["path_template"].replace("{date}", today)
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

            ws_total = ws[0] * 60 + ws[1] if ws else None
            we_total = we[0] * 60 + we[1] if we else None

            if ws_total is not None and now_total < ws_total:
                details[f"{aid}_status"] = "not_yet_due"
                details[f"{aid}_window"] = f"{ws[0]:02d}:{ws[1]:02d}"
                continue

            past_window_end = False
            if we is not None:
                window_end = now_dt.replace(hour=we[0], minute=we[1], second=0, microsecond=0)
                past_window_end = now_dt >= window_end
            exists = artifact_path.exists()
            grace_sec = int(artifact.get("window_grace_sec") or 0)
            in_startup_grace = False
            if grace_sec > 0 and ws and not past_window_end:
                window_start = now_dt.replace(hour=ws[0], minute=ws[1], second=0, microsecond=0)
                elapsed_from_start = (now_dt - window_start).total_seconds()
                in_startup_grace = 0 <= elapsed_from_start <= grace_sec
            if not exists and in_startup_grace:
                details[f"{aid}_status"] = "startup_grace"
                details[f"{aid}_window"] = f"{ws[0]:02d}:{ws[1]:02d}"
                details[f"{aid}_grace_sec"] = grace_sec
                continue

            if not exists:
                alternate_status = self._validate_partitioned_compact(
                    artifact,
                    today,
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
                    today,
                )
                if in_progress_cron and not past_window_end:
                    warnings.append(f"{aid}: upstream cron in progress; artifact not generated yet")
                    details[f"{aid}_status"] = "warning"
                    details[f"{aid}_upstream_status"] = "in_progress"
                    continue
                if (
                    in_progress_cron
                    and past_window_end
                    and bool(artifact.get("allow_missing_after_window_while_cron_in_progress"))
                ):
                    warnings.append(f"{aid}: upstream cron still in progress after window end")
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
            status_warning = self._validate_json_status(artifact, artifact_path, details)
            if status_warning:
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
    def _is_upstream_cron_in_progress(config: Any, today: str) -> bool:
        if not isinstance(config, dict):
            return False
        log_value = str(config.get("log") or "").strip()
        if not log_value:
            return False
        log_path = PROJECT_ROOT / log_value
        if not log_path.exists():
            return False
        try:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-200:]
        except OSError:
            return False
        today_lines = [line for line in lines if today in line or f"target_date={today}" in line]
        if not today_lines:
            return False
        has_start = any("[START]" in line or "[BEGIN]" in line for line in today_lines)
        has_done = any("[DONE]" in line or "[OK]" in line or "[SUCCESS]" in line or "[COMPLETED]" in line for line in today_lines)
        has_fail = any("[FAIL]" in line or "[ERROR]" in line or "[CRITICAL]" in line for line in today_lines)
        if not has_start or has_done:
            return False
        if has_fail:
            return False
        return True

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
        partition_glob_template = str(config.get("partition_glob_template") or "").strip()
        if not checkpoint_template or not partition_glob_template:
            return "warning", f"{aid}: partitioned compact detector config incomplete"

        checkpoint_path = PROJECT_ROOT / checkpoint_template.replace("{date}", today)
        partition_glob = partition_glob_template.replace("{date}", today)
        if Path(partition_glob).is_absolute():
            partition_paths = sorted(Path(path) for path in glob.glob(partition_glob))
        else:
            partition_paths = sorted(PROJECT_ROOT.glob(partition_glob))

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
            return "warning", f"{aid}: partitioned compact checkpoint incomplete{reason}"

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
            payload = ArtifactFreshnessDetector._load_content_payload(data_format, artifact_path)
        except Exception as exc:
            details[f"{aid}_content_status"] = "invalid_content"
            return f"{aid}: invalid content freshness payload ({exc})", False

        min_rows = config.get("min_rows")
        if min_rows is not None and isinstance(payload, list) and len(payload) < int(min_rows):
            details[f"{aid}_content_status"] = "insufficient_rows"
            details[f"{aid}_content_rows"] = len(payload)
            return f"{aid}: insufficient rows ({len(payload)} < {int(min_rows)})", False
        if isinstance(payload, list):
            details[f"{aid}_content_rows"] = len(payload)

        min_count_field = str(config.get("min_count_field") or "").strip()
        if min_count_field:
            count_value = ArtifactFreshnessDetector._resolve_field(payload, min_count_field)
            try:
                count_int = int(count_value)
            except (TypeError, ValueError):
                details[f"{aid}_content_status"] = "invalid_count"
                return f"{aid}: invalid count field {min_count_field}", False
            details[f"{aid}_{min_count_field}"] = count_int
            min_count = int(config.get("min_count") or 0)
            if count_int < min_count:
                details[f"{aid}_content_status"] = "insufficient_count"
                return f"{aid}: insufficient {min_count_field} ({count_int} < {min_count})", False

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
            return f"{aid}: content date is in the future ({content_date.date().isoformat()})", False
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
