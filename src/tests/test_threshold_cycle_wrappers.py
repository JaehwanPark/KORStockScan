from pathlib import Path


def test_postclose_wrapper_runs_pattern_labs_before_automation_and_ev_report():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    gemini_idx = script.index("analysis/gemini_scalping_pattern_lab/run.sh")
    claude_idx = script.index("analysis/claude_scalping_pattern_lab/run_all.sh")
    automation_idx = script.index("src.engine.scalping_pattern_lab_automation")
    currentness_idx = script.index("src.engine.pattern_lab_currentness_audit")
    ev_idx = script.index('run_threshold_cycle_ev_and_wait "pre_workorder"')

    assert "ANALYSIS_START_DATE=\"$PATTERN_LAB_START_DATE\" ANALYSIS_END_DATE=\"$TARGET_DATE\"" in script
    assert gemini_idx < automation_idx
    assert claude_idx < automation_idx
    assert automation_idx < currentness_idx < ev_idx
    assert 'RUN_PATTERN_LAB_CURRENTNESS_AUDIT="${THRESHOLD_CYCLE_RUN_PATTERN_LAB_CURRENTNESS_AUDIT:-true}"' in script


def test_scalp_sim_overnight_preclose_wrapper_uses_live_openai_and_bedrock_lite_shadow():
    script = Path("deploy/run_scalp_sim_overnight_preclose.sh").read_text(encoding="utf-8")

    assert "PYTHONPATH=." in script
    assert "src.engine.scalp_sim_overnight --date \"$TARGET_DATE\" --live-openai" in script
    assert "--report-only" not in script
    assert 'KORSTOCKSCAN_SCALPING_AI_ROUTE="${KORSTOCKSCAN_SCALPING_AI_ROUTE:-openai}"' in script
    assert 'KORSTOCKSCAN_BEDROCK_NOVA_LITE_SHADOW_ENABLED="${KORSTOCKSCAN_BEDROCK_NOVA_LITE_SHADOW_ENABLED:-true}"' in script
    assert 'KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE="${KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE:-shadow}"' in script


def test_threshold_cycle_cron_installs_scalp_sim_overnight_preclose_once():
    script = Path("deploy/install_threshold_cycle_cron.sh").read_text(encoding="utf-8")

    assert "SCALP_SIM_OVERNIGHT_PRECLOSE" in script
    assert "20 15 * * 1-5" in script
    assert "deploy/run_scalp_sim_overnight_preclose.sh" in script
    assert "!/SCALP_SIM_OVERNIGHT_PRECLOSE/" in script


def test_postclose_wrapper_runs_swing_daily_simulation_before_lifecycle_audit():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    simulation_idx = script.index('deploy/run_swing_daily_simulation_report.sh" "$TARGET_DATE"')
    simulation_wait_idx = script.index('"$PROJECT_DIR/data/report/swing_daily_simulation/swing_daily_simulation_${TARGET_DATE}.json"')
    discovery_idx = script.index("src.engine.swing_strategy_discovery_sim")
    label_idx = script.index("src.engine.swing_strategy_discovery_label_builder")
    discovery_ev_idx = script.index("src.engine.swing_strategy_discovery_ev_report")
    audit_idx = script.index("src.engine.swing_lifecycle_audit")
    resource_idx = script.index('wait_for_postclose_resources "swing_lifecycle_audit"')

    assert simulation_idx < audit_idx
    assert simulation_idx < simulation_wait_idx < discovery_idx < label_idx < discovery_ev_idx < audit_idx
    assert resource_idx < audit_idx
    assert 'run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.swing_lifecycle_audit' in script
    assert 'SWING_THRESHOLD_AI_REVIEW_PROVIDER="${SWING_THRESHOLD_AI_REVIEW_PROVIDER:-none}"' in script
    assert 'RUN_SWING_STRATEGY_DISCOVERY="${THRESHOLD_CYCLE_RUN_SWING_STRATEGY_DISCOVERY:-true}"' in script


def test_swing_live_dry_run_defaults_ai_review_provider_to_none():
    script = Path("deploy/run_swing_live_dry_run_report.sh").read_text(encoding="utf-8")

    assert 'SWING_THRESHOLD_AI_REVIEW_PROVIDER="${SWING_THRESHOLD_AI_REVIEW_PROVIDER:-none}"' in script
    assert '--ai-review-provider "$SWING_THRESHOLD_AI_REVIEW_PROVIDER"' in script


def test_postclose_wrapper_runs_threshold_ev_before_and_after_workorder():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    sim_post_sell_idx = script.index("src.engine.sniper_post_sell_feedback")
    entry_adm_idx = script.index("src.engine.scalp_entry_action_decision_matrix")
    lifecycle_matrix_idx = script.index("src.engine.lifecycle_decision_matrix")
    context_attribution_idx = script.index("src.engine.lifecycle_ai_context --date \"$TARGET_DATE\" --mode attribution")
    context_idx = script.index("src.engine.lifecycle_ai_context --date \"$TARGET_DATE\" --mode context")
    discovery_idx = script.index("src.engine.lifecycle_bucket_discovery")
    bridge_idx = script.index("src.engine.runtime_apply_bridge")
    verbosity_idx = script.index("src.engine.pipeline_event_verbosity_report")
    observation_audit_idx = script.index("src.engine.observation_source_quality_audit")
    perf_source_idx = script.index("src.engine.codebase_performance_workorder_report")
    pre_ev_idx = script.index('run_threshold_cycle_ev_and_wait "pre_workorder"')
    workorder_idx = script.index("src.engine.build_code_improvement_workorder")
    post_ev_idx = script.index('run_threshold_cycle_ev_and_wait "post_workorder_refresh"')
    propagation_idx = script.index("src.engine.pattern_lab_propagation_audit")
    post_propagation_ev_idx = script.index('run_threshold_cycle_ev_and_wait "post_propagation_audit_refresh"')
    runtime_summary_idx = script.index("src.engine.runtime_approval_summary")
    next_checklist_idx = script.rindex("src.engine.build_next_stage2_checklist")

    assert (
        sim_post_sell_idx
        < entry_adm_idx
        < lifecycle_matrix_idx
        < context_attribution_idx
        < context_idx
        < discovery_idx
        < bridge_idx
        < verbosity_idx
        < observation_audit_idx
        < perf_source_idx
        < pre_ev_idx
        < workorder_idx
        < post_ev_idx
        < propagation_idx
        < post_propagation_ev_idx
        < runtime_summary_idx
        < next_checklist_idx
    )
    assert 'RUN_PATTERN_LAB_PROPAGATION_AUDIT="${THRESHOLD_CYCLE_RUN_PATTERN_LAB_PROPAGATION_AUDIT:-true}"' in script
    assert 'RUN_SCALP_ENTRY_ADM="${THRESHOLD_CYCLE_RUN_SCALP_ENTRY_ADM:-true}"' in script
    assert 'RUN_LIFECYCLE_DECISION_MATRIX="${THRESHOLD_CYCLE_RUN_LIFECYCLE_DECISION_MATRIX:-true}"' in script
    assert 'RUN_LIFECYCLE_AI_CONTEXT="${THRESHOLD_CYCLE_RUN_LIFECYCLE_AI_CONTEXT:-true}"' in script
    assert 'RUN_LIFECYCLE_BUCKET_DISCOVERY="${THRESHOLD_CYCLE_RUN_LIFECYCLE_BUCKET_DISCOVERY:-$RUN_LIFECYCLE_DECISION_MATRIX}"' in script
    assert 'RUN_RUNTIME_APPLY_BRIDGE="${THRESHOLD_CYCLE_RUN_RUNTIME_APPLY_BRIDGE:-$RUN_LIFECYCLE_BUCKET_DISCOVERY}"' in script
    assert "lifecycle_ai_context=$RUN_LIFECYCLE_AI_CONTEXT" in script
    assert "lifecycle_bucket_discovery=$RUN_LIFECYCLE_BUCKET_DISCOVERY" in script
    assert "runtime_apply_bridge=$RUN_RUNTIME_APPLY_BRIDGE" in script


def test_postclose_wrapper_refreshes_market_breadth_before_panic_reports():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    breadth_idx = script.index("src.engine.market_panic_breadth_collector")
    breadth_wait_idx = script.index("market_panic_breadth_postclose")
    panic_sell_idx = script.index("src.engine.panic_sell_defense_report")
    panic_buy_idx = script.index("src.engine.panic_buying_report")

    assert 'RUN_MARKET_PANIC_BREADTH_REPORT="${THRESHOLD_CYCLE_RUN_MARKET_PANIC_BREADTH_REPORT:-true}"' in script
    assert breadth_idx < breadth_wait_idx < panic_sell_idx < panic_buy_idx
    assert "market_panic_breadth=$RUN_MARKET_PANIC_BREADTH_REPORT" in script


def test_panic_buying_wrapper_collects_market_breadth_independently():
    script = Path("deploy/run_panic_buying_intraday.sh").read_text(encoding="utf-8")

    breadth_idx = script.index("[START] market panic breadth collect")
    report_idx = script.index('if "${cmd[@]}"')

    assert 'MARKET_BREADTH_COLLECT_ENABLED="${PANIC_MARKET_BREADTH_COLLECT_ENABLED:-true}"' in script
    assert "market panic breadth collect failed" in script
    assert breadth_idx < report_idx


def test_postclose_wrapper_waits_for_prerequisite_artifacts_before_downstream_steps():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert 'ARTIFACT_WAIT_SEC="${THRESHOLD_CYCLE_ARTIFACT_WAIT_SEC:-600}"' in script
    assert 'AI_CORRECTION_MAX_ATTEMPTS="${THRESHOLD_CYCLE_AI_CORRECTION_MAX_ATTEMPTS:-2}"' in script
    assert 'AI_CORRECTION_RETRY_DELAY_SEC="${THRESHOLD_CYCLE_AI_CORRECTION_RETRY_DELAY_SEC:-20}"' in script
    assert 'AI_CORRECTION_REUSE_IF_VALID="${THRESHOLD_CYCLE_REUSE_AI_REVIEW_IF_VALID:-true}"' in script
    assert "--reuse-ai-review-if-valid" in script
    assert "wait_for_json_artifact()" in script
    assert "wait_for_report_artifact()" in script
    assert "threshold_cycle_ai_review_status()" in script
    assert "next_stage2_checklist_path()" in script
    assert '"$PROJECT_DIR/data/report/code_improvement_workorder/code_improvement_workorder_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/runtime_apply_bridge/runtime_apply_bridge_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/runtime_approval_summary/runtime_approval_summary_${TARGET_DATE}.json"' in script
    assert 'wait_for_file_artifact "$(next_stage2_checklist_path)" "next_stage2_checklist"' in script
    assert "src.engine.verify_threshold_cycle_postclose_chain" in script
    assert "--allow-pending-done-marker" in script
    assert "run_postclose_cmd env PYTHONPATH=. \"$VENV_PY\" -m src.engine.verify_threshold_cycle_postclose_chain" in script
    assert '"$PROJECT_DIR/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_${TARGET_DATE}.json"' in script
    assert "pattern_lab_currentness_audit=$RUN_PATTERN_LAB_CURRENTNESS_AUDIT" in script
    assert "pattern_lab_propagation_audit=$RUN_PATTERN_LAB_PROPAGATION_AUDIT" in script
    assert "scalp_entry_adm=$RUN_SCALP_ENTRY_ADM" in script
    assert "lifecycle_decision_matrix=$RUN_LIFECYCLE_DECISION_MATRIX" in script
    assert "lifecycle_bucket_discovery=$RUN_LIFECYCLE_BUCKET_DISCOVERY" in script
    assert "runtime_apply_bridge=$RUN_RUNTIME_APPLY_BRIDGE" in script
    assert "ai correction retry target_date=$TARGET_DATE" in script
    assert "ai correction final unavailable" in script


def test_postclose_wrapper_marks_availability_guard_pause_as_fail():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert "[PAUSED] threshold-cycle postclose" in script
    assert "[FAIL] threshold-cycle postclose" in script
    assert "paused_by_availability_guard" in script
    assert 'if [ "${completed:-false}" != "true" ]; then' in script
    assert "compact collection incomplete" in script


def test_postclose_wrapper_reuses_existing_snapshot_when_checkpoint_exists():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert 'CHECKPOINT_PATH="$PROJECT_DIR/data/threshold_cycle/checkpoints/${TARGET_DATE}.json"' in script
    assert 'MAX_CPU_BUSY_PCT="${THRESHOLD_CYCLE_MAX_CPU_BUSY_PCT:-95}"' in script
    assert '-name "pipeline_events_${TARGET_DATE}_*.jsonl.gz"' in script
    assert '--max-cpu-busy-pct "$MAX_CPU_BUSY_PCT"' in script
    assert '[ -f "$CHECKPOINT_PATH" ] && [ -n "$EXISTING_SNAPSHOT_PATH" ]' in script
    assert 'echo "[threshold-cycle] reusing immutable snapshot source=$EXISTING_SNAPSHOT_PATH checkpoint=$CHECKPOINT_PATH"' in script
    assert '[ "${REUSE_EXISTING_SNAPSHOT:-false}" != "true" ]' in script


def test_postclose_wrapper_resource_guards_heavy_steps():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert 'POSTCLOSE_RESOURCE_GUARD="${THRESHOLD_CYCLE_POSTCLOSE_RESOURCE_GUARD:-true}"' in script
    assert 'POSTCLOSE_NICE_LEVEL="${THRESHOLD_CYCLE_POSTCLOSE_NICE_LEVEL:-10}"' in script
    assert 'POSTCLOSE_IONICE_LEVEL="${THRESHOLD_CYCLE_POSTCLOSE_IONICE_LEVEL:-7}"' in script
    assert 'POSTCLOSE_MIN_SWAP_FREE_MB="${THRESHOLD_CYCLE_POSTCLOSE_MIN_SWAP_FREE_MB:-256}"' in script
    assert 'POSTCLOSE_MAX_SAMPLE_AGE_SEC="${THRESHOLD_CYCLE_POSTCLOSE_MAX_SAMPLE_AGE_SEC:-180}"' in script
    assert 'POSTCLOSE_MAX_LOAD1="${THRESHOLD_CYCLE_POSTCLOSE_MAX_LOAD1:-64}"' in script
    assert 'POSTCLOSE_BOT_ACTION="${THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION:-none}"' in script
    assert 'COMPACT_AVAILABILITY_WAIT_SEC="${THRESHOLD_CYCLE_COMPACT_AVAILABILITY_WAIT_SEC:-900}"' in script
    assert "run_postclose_cmd()" in script
    assert "mark_postclose_failed()" in script
    assert "stop_postclose_bot_if_requested()" in script
    assert "restart_postclose_bot_if_requested()" in script
    assert "stopping bot for postclose resource isolation" in script
    assert "restarting bot after postclose" in script
    assert "starting bot after postclose" in script
    assert "reason=restart_action_requested" in script
    assert "wait_for_postclose_resources()" in script
    assert "sample_age_sec=" in script
    assert "swap_free_mb=" in script
    assert "cpu_busy_pct=" in script
    assert "load1=" in script
    assert "sampler_missing" in script
    assert "availability guard wait" in script
    assert 'wait_for_postclose_resources "daily_threshold_cycle_report"' in script
    assert 'wait_for_postclose_resources "swing_lifecycle_audit"' in script
    assert 'wait_for_postclose_resources "gemini_scalping_pattern_lab"' in script
    assert 'wait_for_postclose_resources "threshold_cycle_ev_${pass_label}"' in script
    assert 'run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.backfill_threshold_cycle_events' in script
    assert 'run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.daily_threshold_cycle_report' in script


def test_threshold_cycle_cron_restarts_bot_around_postclose():
    script = Path("deploy/install_threshold_cycle_cron.sh").read_text(encoding="utf-8")

    assert "THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=restart" in script
    assert "THRESHOLD_CYCLE_POSTCLOSE" in script


def test_postclose_wrapper_cleans_up_snapshot_duplicates_with_retention():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert 'SNAPSHOT_RETENTION_DAYS="${THRESHOLD_CYCLE_SNAPSHOT_RETENTION_DAYS:-7}"' in script
    assert "cleanup_threshold_cycle_snapshots()" in script
    assert 'cleanup_threshold_cycle_snapshots "$SNAPSHOT_DIR" "$SNAPSHOT_RETENTION_DAYS"' in script
    assert 'pipeline_events_(\\d{4}-\\d{2}-\\d{2})_(\\d{8}_\\d{6})\\.jsonl(?:\\.gz)?$' in script
    assert 'retention_days={retention_days}' in script
    assert 'removed_bytes={removed_bytes}' in script


def test_tuning_monitoring_wrapper_skips_pattern_labs_by_default():
    script = Path("deploy/run_tuning_monitoring_postclose.sh").read_text(encoding="utf-8")

    assert 'RUN_PATTERN_LABS="${TUNING_MONITORING_RUN_PATTERN_LABS:-false}"' in script
    assert 'canonical_runner=THRESHOLD_CYCLE_POSTCLOSE' in script
    assert 'if [[ "$RUN_PATTERN_LABS" == "1" || "$RUN_PATTERN_LABS" == "true" ]]' in script


def test_calibration_wrapper_retries_and_fails_unavailable_ai_correction():
    script = Path("deploy/run_threshold_cycle_calibration.sh").read_text(encoding="utf-8")

    assert 'AI_CORRECTION_MAX_ATTEMPTS="${THRESHOLD_CYCLE_AI_CORRECTION_MAX_ATTEMPTS:-2}"' in script
    assert 'AI_CORRECTION_RETRY_DELAY_SEC="${THRESHOLD_CYCLE_AI_CORRECTION_RETRY_DELAY_SEC:-20}"' in script
    assert 'AI_CORRECTION_REUSE_IF_VALID="${THRESHOLD_CYCLE_REUSE_AI_REVIEW_IF_VALID:-true}"' in script
    assert "--reuse-ai-review-if-valid" in script
    assert "threshold_cycle_ai_review_status()" in script
    assert "ai correction retry target_date=$TARGET_DATE phase=$RUN_PHASE" in script
    assert "ai correction final unavailable target_date=$TARGET_DATE phase=$RUN_PHASE" in script
    assert 'exit 1' in script


def test_tuning_monitoring_waits_for_threshold_postclose_done_by_default():
    script = Path("deploy/run_tuning_monitoring_postclose.sh").read_text(encoding="utf-8")

    assert 'REQUIRE_THRESHOLD_POSTCLOSE_DONE="${TUNING_MONITORING_REQUIRE_THRESHOLD_POSTCLOSE_DONE:-true}"' in script
    assert "wait_for_threshold_postclose_done" in script
    assert "threshold_postclose_terminal_marker" in script
    assert "reason=threshold_cycle_postclose_not_done" in script
    assert "reason=threshold_cycle_postclose_failed" in script


def test_run_bot_waits_for_threshold_runtime_env_before_launching_bot():
    script = Path("src/run_bot.sh").read_text(encoding="utf-8")

    assert "wait_for_threshold_runtime_env" in script
    assert "KORSTOCKSCAN_THRESHOLD_RUNTIME_ENV_REQUIRED" in script
    assert "KORSTOCKSCAN_THRESHOLD_RUNTIME_ENV_BOOTSTRAP" in script
    assert "./deploy/run_threshold_cycle_preopen.sh" in script
    assert "threshold runtime env 미생성으로 봇 기동 중단" in script
    assert script.index('wait_for_threshold_runtime_env "$THRESHOLD_RUNTIME_ENV"') < script.index("../.venv/bin/python bot_main.py")


def test_preopen_wrapper_uses_lock_to_avoid_duplicate_bootstrap_run():
    script = Path("deploy/run_threshold_cycle_preopen.sh").read_text(encoding="utf-8")

    assert "threshold_cycle_preopen.lock" in script
    assert "flock -n 9" in script
    assert "threshold-cycle preopen already running" in script
