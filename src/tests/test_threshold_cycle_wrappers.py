from pathlib import Path
import json
import os
import subprocess


def test_postclose_wrapper_runs_pattern_labs_before_automation_and_ev_report():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    claude_idx = script.index("analysis/claude_scalping_pattern_lab/run_all.sh")
    automation_idx = script.index("src.engine.scalping_pattern_lab_automation")
    currentness_idx = script.index("src.engine.pattern_lab_currentness_audit")
    ai_review_idx = script.index("src.engine.pattern_lab_ai_review")
    ev_idx = script.index('run_threshold_cycle_ev_and_wait "pre_workorder"')

    assert "ANALYSIS_START_DATE=\"$PATTERN_LAB_START_DATE\" ANALYSIS_END_DATE=\"$TARGET_DATE\"" in script
    assert 'PATTERN_LAB_START_DATE="${PATTERN_LAB_ANALYSIS_START_DATE:-${KORSTOCKSCAN_CLEAN_TUNING_BASELINE_DATE:-2026-06-04}}"' in script
    assert "analysis/gemini_scalping_pattern_lab/run.sh" not in script
    assert "retired_from_automatic_execution" in script
    assert claude_idx < automation_idx
    assert automation_idx < currentness_idx < ai_review_idx < ev_idx
    assert 'RUN_PATTERN_LAB_CURRENTNESS_AUDIT="${THRESHOLD_CYCLE_RUN_PATTERN_LAB_CURRENTNESS_AUDIT:-true}"' in script
    assert 'RUN_PATTERN_LAB_AI_REVIEW="${THRESHOLD_CYCLE_RUN_PATTERN_LAB_AI_REVIEW:-true}"' in script
    assert 'PATTERN_LAB_AI_REVIEW_PROVIDER="${KORSTOCKSCAN_PATTERN_LAB_AI_REVIEW_PROVIDER:-openai}"' in script


def test_scalp_sim_overnight_preclose_wrapper_uses_live_openai_without_bedrock_lite_shadow():
    script = Path("deploy/run_scalp_sim_overnight_preclose.sh").read_text(encoding="utf-8")

    assert "PYTHONPATH=." in script
    assert "src.engine.scalp_sim_overnight --date \"$TARGET_DATE\" --live-openai" in script
    assert "--report-only" not in script
    assert "KORSTOCKSCAN_BEDROCK_NOVA_LITE_SHADOW_ENABLED" not in script
    assert "KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE=off" in script


def test_threshold_cycle_cron_installs_scalp_sim_overnight_preclose_once():
    script = Path("deploy/install_threshold_cycle_cron.sh").read_text(encoding="utf-8")

    assert "SCALP_SIM_OVERNIGHT_PRECLOSE" in script
    assert "10 15 * * 1-5" in script
    assert "deploy/run_scalp_sim_overnight_preclose.sh" in script
    assert "!/SCALP_SIM_OVERNIGHT_PRECLOSE/" in script


def test_postclose_done_controller_wrapper_runs_controller_and_skips_codex_runner_by_default():
    script = Path("deploy/run_postclose_done_controller.sh").read_text(encoding="utf-8")

    controller_idx = script.index("src.engine.automation.postclose_done_controller")
    codex_idx = script.index("src.engine.automation.codex_workorder_runner")

    assert "[START] postclose_done_controller" in script
    assert "[DONE] postclose_done_controller" in script
    assert "--allow-wrapper-rerun" in script
    assert "--predecessor-timeout-sec" in script
    assert "POSTCLOSE_DONE_CONTROLLER_PREDECESSOR_TIMEOUT_SEC" in script
    assert "$PROJECT_DIR/venv/Scripts/python.exe" in script
    assert 'RUN_CODEX="${POSTCLOSE_DONE_CONTROLLER_RUN_CODEX:-false}"' in script
    assert "POSTCLOSE_DONE_CONTROLLER_CODEX_MODEL_POLICY" in script
    assert 'CODEX_MODEL_POLICY="${POSTCLOSE_DONE_CONTROLLER_CODEX_MODEL_POLICY:-credit_min}"' in script
    assert "POSTCLOSE_DONE_CONTROLLER_CODEX_MODEL" in script
    assert "POSTCLOSE_DONE_CONTROLLER_CODEX_EFFORT" in script
    assert "POSTCLOSE_DONE_CONTROLLER_CODEX_BATCH_SIZE" in script
    assert "POSTCLOSE_DONE_CONTROLLER_AUTO_PUSH_MAIN" in script
    assert "POSTCLOSE_DONE_CONTROLLER_REQUIRE_CODEX_COMPLETED" in script
    assert 'REQUIRE_CODEX_COMPLETED="${POSTCLOSE_DONE_CONTROLLER_REQUIRE_CODEX_COMPLETED:-false}"' in script
    assert "--model-policy" in script
    assert "--model" in script
    assert "--effort" in script
    assert "--auto-push-main" in script
    assert "--no-auto-push-main" in script
    assert "--require-codex-completed" in script
    assert "codex_workorder_runner disabled while strict completion is required" not in script
    assert 'VENV_PY="python"' in script
    assert "controller_report=" in script
    assert "controller_status" in script
    assert "[SKIP] codex_workorder_runner" in script
    assert "disabled_by_default" in script
    assert "[WARN] codex_workorder_runner" not in script
    assert 'codex_status" != "completed"' in script
    assert controller_idx < codex_idx


def test_postclose_done_controller_cron_installs_2010_once():
    script = Path("deploy/install_postclose_done_controller_cron.sh").read_text(encoding="utf-8")

    assert "POSTCLOSE_DONE_CONTROLLER" in script
    assert "10 20 * * 1-5" in script
    assert "40 21 * * 1-5" not in script
    assert "deploy/run_postclose_done_controller.sh" in script


def test_postclose_wrapper_runs_swing_daily_simulation_before_lifecycle_audit():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    simulation_idx = script.index('deploy/run_swing_daily_simulation_report.sh" "$TARGET_DATE"')
    simulation_wait_idx = script.index('"$PROJECT_DIR/data/report/swing_daily_simulation/swing_daily_simulation_${TARGET_DATE}.json"')
    discovery_idx = script.index("src.engine.swing_strategy_discovery_sim")
    label_idx = script.index("src.engine.swing_strategy_discovery_label_builder")
    discovery_ev_idx = script.index("src.engine.swing_strategy_discovery_ev_report")
    swing_ldm_idx = script.index("src.engine.swing_lifecycle_decision_matrix")
    swing_bucket_idx = script.index("src.engine.swing_lifecycle_bucket_discovery")
    audit_idx = script.index("src.engine.swing_lifecycle_audit")
    resource_idx = script.index('wait_for_postclose_resources "swing_lifecycle_audit"')

    assert simulation_idx < audit_idx
    assert simulation_idx < simulation_wait_idx < discovery_idx < label_idx < discovery_ev_idx < swing_ldm_idx < swing_bucket_idx < audit_idx
    assert resource_idx < audit_idx
    assert 'run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.swing_lifecycle_audit' in script
    assert 'SWING_THRESHOLD_AI_REVIEW_PROVIDER="${SWING_THRESHOLD_AI_REVIEW_PROVIDER:-openai}"' in script
    assert 'RUN_SWING_STRATEGY_DISCOVERY="${THRESHOLD_CYCLE_RUN_SWING_STRATEGY_DISCOVERY:-true}"' in script
    assert 'RUN_SWING_LIFECYCLE_MATRIX="${THRESHOLD_CYCLE_RUN_SWING_LIFECYCLE_MATRIX:-$RUN_SWING_STRATEGY_DISCOVERY}"' in script
    assert 'RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY="${THRESHOLD_CYCLE_RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY:-$RUN_SWING_LIFECYCLE_MATRIX}"' in script


def test_swing_ldm_rolling_backfill_waits_for_postclose_and_skips_holidays():
    script = Path("deploy/run_swing_ldm_rolling_backfill_once.sh").read_text(encoding="utf-8")

    assert "threshold_cycle_postclose_${POSTCLOSE_DATE}.status.json" in script
    assert 'if [ "$status" = "succeeded" ]; then' in script
    assert "2026-05-18 2026-05-19 2026-05-20 2026-05-21 2026-05-22 2026-05-26 2026-05-27 2026-05-28 2026-05-29 2026-06-01" in script
    assert "2026-05-23" not in script
    assert "2026-05-24" not in script
    assert "2026-05-25" not in script
    assert "2026-05-30" not in script
    assert "2026-05-31" not in script
    assert "src.engine.swing_lifecycle_decision_matrix" in script
    assert "src.engine.swing_lifecycle_bucket_discovery --date" in script
    assert "--ai-provider openai" in script
    assert "src.engine.swing_lifecycle_audit --date" in script
    assert "--ai-review-provider openai" in script


def test_postclose_wrapper_includes_valid_bottom_rebound_source_for_swing_discovery():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    contract_idx = script.index("bottom_rebound_source_contract_ok()")
    source_path_idx = script.index("swing_bottom_rebound_candidate_source_${TARGET_DATE}.json")
    include_idx = script.index("--include-bottom-rebound-source")
    fallback_idx = script.index("safe_pool_only=true")
    discovery_idx = script.index("src.engine.swing_strategy_discovery_sim")

    assert contract_idx < source_path_idx < discovery_idx
    assert discovery_idx < include_idx
    assert source_path_idx < fallback_idx
    assert "bottom_rebound_source_contract=pass" in script
    assert "bottom_rebound_source_contract=missing_or_invalid" in script
    assert 'payload.get("report_type") == "swing_bottom_rebound_candidate_source"' in script
    assert 'payload.get("runtime_effect") is False' in script
    assert 'payload.get("broker_order_forbidden") is True' in script
    assert 'payload.get("allowed_runtime_apply") is False' in script


def test_swing_live_dry_run_defaults_ai_review_provider_to_none():
    script = Path("deploy/run_swing_live_dry_run_report.sh").read_text(encoding="utf-8")

    assert 'SWING_THRESHOLD_AI_REVIEW_PROVIDER="${SWING_THRESHOLD_AI_REVIEW_PROVIDER:-none}"' in script
    assert '--ai-review-provider "$SWING_THRESHOLD_AI_REVIEW_PROVIDER"' in script


def test_postclose_wrapper_runs_threshold_ev_before_and_after_workorder():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    sim_post_sell_idx = script.index("src.engine.sniper_post_sell_feedback")
    rising_missed_feedback_idx = script.index("src.engine.monitoring.rising_missed_intraday_feedback")
    rising_missed_scout_idx = script.index("src.engine.monitoring.rising_missed_scout_workorder")
    rising_missed_first_touch_calibration_idx = script.index(
        "src.engine.monitoring.rising_missed_first_touch_calibration"
    )
    scalping_pyramid_feedback_idx = script.index("src.engine.monitoring.scalping_pyramid_intraday_feedback")
    scalping_pyramid_calibration_idx = script.index("src.engine.monitoring.scalping_pyramid_quality_calibration")
    one_share_threshold_idx = script.index("src.engine.monitoring.one_share_threshold_opportunity")
    entry_adm_idx = script.index("src.engine.scalp_entry_action_decision_matrix")
    entry_ai_gate_idx = script.index("src.engine.scalping.entry_ai_gate_backtest")
    ai_score_optimization_idx = script.index("src.engine.scalping.ai_score_optimization_backtest")
    microstructure_idx = script.index("src.engine.scalping.microstructure_reaction_context")
    observation_preflight_idx = script.index("observation_source_quality_preflight")
    scale_in_cf_idx = script.index("src.engine.lifecycle.scale_in_incremental_counterfactual")
    lifecycle_matrix_idx = script.index("src.engine.lifecycle_decision_matrix")
    context_attribution_idx = script.index("src.engine.lifecycle_ai_context --date \"$TARGET_DATE\" --mode attribution")
    context_idx = script.index("src.engine.lifecycle_ai_context --date \"$TARGET_DATE\" --mode context")
    assert observation_preflight_idx < scale_in_cf_idx < lifecycle_matrix_idx
    assert (
        rising_missed_feedback_idx
        < rising_missed_scout_idx
        < rising_missed_first_touch_calibration_idx
        < scalping_pyramid_feedback_idx
        < scalping_pyramid_calibration_idx
        < one_share_threshold_idx
        < entry_adm_idx
    )
    discovery_idx = script.index("src.engine.lifecycle_bucket_discovery")
    bridge_idx = script.index("src.engine.runtime_apply_bridge")
    verbosity_idx = script.index("src.engine.pipeline_event_verbosity_report")
    observation_audit_idx = script.index("src.engine.observation_source_quality_audit", verbosity_idx)
    perf_source_idx = script.index("src.engine.codebase_performance_workorder_report")
    watching_smoothing_idx = script.index("src.engine.scalping.watching_score_smoothing")
    time_window_idx = script.index("src.engine.automation.time_window_regime_counterfactual")
    producer_gap_source_idx = script.index("src.engine.automation.producer_gap_source_bundle")
    producer_gap_idx = script.index("src.engine.automation.producer_gap_discovery")
    stage_hook_idx = script.index("src.engine.automation.stage_hook_workorder_discovery")
    stage_hook_scaffold_idx = script.index("src.engine.automation.stage_hook_runtime_scaffold")
    pre_ev_idx = script.index('run_threshold_cycle_ev_and_wait "pre_workorder"')
    workorder_idx = script.index("src.engine.build_code_improvement_workorder")
    post_ev_idx = script.index('run_threshold_cycle_ev_and_wait "post_workorder_refresh"')
    propagation_idx = script.index("src.engine.pattern_lab_propagation_audit")
    post_propagation_ev_idx = script.index('run_threshold_cycle_ev_and_wait "post_propagation_audit_refresh"')
    runtime_summary_idx = script.index("src.engine.runtime_approval_summary")
    runtime_gap_idx = script.index("src.engine.runtime_apply_gap_audit")
    conversion_lane_idx = script.index("src.engine.automation.conversion_lane")
    rising_missed_prior_idx = script.index("src.engine.monitoring.rising_missed_classifier_prior")
    post_conversion_workorder_idx = script.index(
        "code_improvement_workorder_post_conversion_lane"
    )
    next_checklist_idx = script.rindex("src.engine.build_next_stage2_checklist")
    pending_verify_idx = script.index("src.engine.verify_threshold_cycle_postclose_chain --date \"$TARGET_DATE\" --allow-pending-done-marker")
    final_verify_idx = script.index("src.engine.verify_threshold_cycle_postclose_chain --date \"$TARGET_DATE\"", pending_verify_idx + 1)
    tuning_control_idx = script.index("src.engine.automation.tuning_performance_control_tower")

    assert (
        sim_post_sell_idx
        < rising_missed_feedback_idx
        < rising_missed_scout_idx
        < rising_missed_first_touch_calibration_idx
        < scalping_pyramid_feedback_idx
        < scalping_pyramid_calibration_idx
        < entry_adm_idx
        < entry_ai_gate_idx
        < ai_score_optimization_idx
        < microstructure_idx
        < observation_preflight_idx
        < lifecycle_matrix_idx
        < context_attribution_idx
        < context_idx
        < discovery_idx
        < bridge_idx
        < verbosity_idx
        < observation_audit_idx
        < watching_smoothing_idx
        < perf_source_idx
        < time_window_idx
        < producer_gap_source_idx
        < producer_gap_idx
        < stage_hook_idx
        < stage_hook_scaffold_idx
        < pre_ev_idx
        < workorder_idx
        < post_ev_idx
        < propagation_idx
        < post_propagation_ev_idx
        < runtime_summary_idx
        < runtime_gap_idx
        < conversion_lane_idx
        < rising_missed_prior_idx
        < post_conversion_workorder_idx
        < next_checklist_idx
        < pending_verify_idx
        < final_verify_idx
        < tuning_control_idx
    )
    assert 'RUN_PATTERN_LAB_PROPAGATION_AUDIT="${THRESHOLD_CYCLE_RUN_PATTERN_LAB_PROPAGATION_AUDIT:-true}"' in script
    assert 'RUN_TIME_WINDOW_REGIME_COUNTERFACTUAL="${THRESHOLD_CYCLE_RUN_TIME_WINDOW_REGIME_COUNTERFACTUAL:-true}"' in script
    assert 'RUN_AI_WATCHING_SCORE_SMOOTHING_DIAGNOSTIC="${THRESHOLD_CYCLE_RUN_AI_WATCHING_SCORE_SMOOTHING_DIAGNOSTIC:-true}"' in script
    assert 'RUN_PRODUCER_GAP_DISCOVERY="${THRESHOLD_CYCLE_RUN_PRODUCER_GAP_DISCOVERY:-true}"' in script
    assert 'RUN_RISING_MISSED_INTRADAY_FEEDBACK_POSTCLOSE="${THRESHOLD_CYCLE_RUN_RISING_MISSED_INTRADAY_FEEDBACK_POSTCLOSE:-true}"' in script
    assert 'RUN_RISING_MISSED_SCOUT_WORKORDER="${THRESHOLD_CYCLE_RUN_RISING_MISSED_SCOUT_WORKORDER:-true}"' in script
    assert 'RUN_RISING_MISSED_FIRST_TOUCH_CALIBRATION="${THRESHOLD_CYCLE_RUN_RISING_MISSED_FIRST_TOUCH_CALIBRATION:-true}"' in script
    assert 'RUN_SCALPING_PYRAMID_INTRADAY_FEEDBACK_POSTCLOSE="${THRESHOLD_CYCLE_RUN_SCALPING_PYRAMID_INTRADAY_FEEDBACK_POSTCLOSE:-true}"' in script
    assert 'RUN_SCALPING_PYRAMID_QUALITY_CALIBRATION="${THRESHOLD_CYCLE_RUN_SCALPING_PYRAMID_QUALITY_CALIBRATION:-true}"' in script
    assert 'RUN_RISING_MISSED_CLASSIFIER_PRIOR="${THRESHOLD_CYCLE_RUN_RISING_MISSED_CLASSIFIER_PRIOR:-true}"' in script
    assert 'RUN_STAGE_HOOK_WORKORDER_DISCOVERY="${THRESHOLD_CYCLE_RUN_STAGE_HOOK_WORKORDER_DISCOVERY:-true}"' in script
    assert 'RUN_STAGE_HOOK_RUNTIME_SCAFFOLD="${THRESHOLD_CYCLE_RUN_STAGE_HOOK_RUNTIME_SCAFFOLD:-true}"' in script
    assert 'RUN_SCALP_ENTRY_ADM="${THRESHOLD_CYCLE_RUN_SCALP_ENTRY_ADM:-true}"' in script
    assert 'RUN_ENTRY_AI_GATE_BACKTEST="${THRESHOLD_CYCLE_RUN_ENTRY_AI_GATE_BACKTEST:-true}"' in script
    assert 'RUN_AI_SCORE_OPTIMIZATION_BACKTEST="${THRESHOLD_CYCLE_RUN_AI_SCORE_OPTIMIZATION_BACKTEST:-true}"' in script
    assert 'RUN_MICROSTRUCTURE_REACTION_CONTEXT="${THRESHOLD_CYCLE_RUN_MICROSTRUCTURE_REACTION_CONTEXT:-true}"' in script
    assert 'RUN_LIFECYCLE_DECISION_MATRIX="${THRESHOLD_CYCLE_RUN_LIFECYCLE_DECISION_MATRIX:-true}"' in script
    assert 'RUN_LIFECYCLE_AI_CONTEXT="${THRESHOLD_CYCLE_RUN_LIFECYCLE_AI_CONTEXT:-true}"' in script
    assert 'RUN_LIFECYCLE_BUCKET_DISCOVERY="${THRESHOLD_CYCLE_RUN_LIFECYCLE_BUCKET_DISCOVERY:-$RUN_LIFECYCLE_DECISION_MATRIX}"' in script
    assert 'RUN_RUNTIME_APPLY_BRIDGE="${THRESHOLD_CYCLE_RUN_RUNTIME_APPLY_BRIDGE:-$RUN_LIFECYCLE_BUCKET_DISCOVERY}"' in script
    assert 'RUN_TUNING_PERFORMANCE_CONTROL_TOWER="${THRESHOLD_CYCLE_RUN_TUNING_PERFORMANCE_CONTROL_TOWER:-true}"' in script
    assert "lifecycle_ai_context=$RUN_LIFECYCLE_AI_CONTEXT" in script
    assert "lifecycle_bucket_discovery=$RUN_LIFECYCLE_BUCKET_DISCOVERY" in script
    assert "runtime_apply_bridge=$RUN_RUNTIME_APPLY_BRIDGE" in script
    assert "tuning_performance_control_tower=$RUN_TUNING_PERFORMANCE_CONTROL_TOWER" in script
    assert "entry_ai_gate_backtest=$RUN_ENTRY_AI_GATE_BACKTEST" in script
    assert "ai_score_optimization_backtest=$RUN_AI_SCORE_OPTIMIZATION_BACKTEST" in script
    assert "time_window_regime_counterfactual=$RUN_TIME_WINDOW_REGIME_COUNTERFACTUAL" in script
    assert "producer_gap_discovery=$RUN_PRODUCER_GAP_DISCOVERY" in script
    assert "stage_hook_workorder_discovery=$RUN_STAGE_HOOK_WORKORDER_DISCOVERY" in script
    assert "stage_hook_runtime_scaffold=$RUN_STAGE_HOOK_RUNTIME_SCAFFOLD" in script
    assert "swing_lifecycle_matrix=$RUN_SWING_LIFECYCLE_MATRIX" in script
    assert "swing_lifecycle_bucket_discovery=$RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY" in script
    assert "microstructure_reaction_context=$RUN_MICROSTRUCTURE_REACTION_CONTEXT" in script
    assert "ai_watching_score_smoothing_diagnostic=$RUN_AI_WATCHING_SCORE_SMOOTHING_DIAGNOSTIC" in script
    assert "optional microstructure_reaction_context failed" in script
    assert "optional microstructure_reaction_context artifact wait failed" in script


def test_postclose_wrapper_treats_producer_gap_fail_closed_as_report_artifact():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    producer_gap_idx = script.index("src.engine.automation.producer_gap_discovery")
    nonfatal_idx = script.index("producer gap discovery returned fail-closed report (non-fatal)")
    artifact_idx = script.index('"$PROJECT_DIR/data/report/producer_gap_discovery/producer_gap_discovery_${TARGET_DATE}.json"')
    ev_idx = script.index('run_threshold_cycle_ev_and_wait "pre_workorder"')

    assert producer_gap_idx < nonfatal_idx < artifact_idx < ev_idx
    assert "downstream verification will consume artifact" in script


def test_postclose_wrapper_treats_stage_hook_fail_closed_as_report_artifact():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    producer_gap_idx = script.index("src.engine.automation.producer_gap_discovery")
    stage_hook_idx = script.index("src.engine.automation.stage_hook_workorder_discovery")
    nonfatal_idx = script.index("stage hook workorder discovery returned fail-closed report (non-fatal)")
    artifact_idx = script.index('"$PROJECT_DIR/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_${TARGET_DATE}.json"')
    ev_idx = script.index('run_threshold_cycle_ev_and_wait "pre_workorder"')

    assert producer_gap_idx < stage_hook_idx < nonfatal_idx < artifact_idx < ev_idx
    assert "downstream verification will consume artifact" in script


def test_postclose_wrapper_runs_stage_hook_scaffold_before_workorder_ev():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    stage_hook_idx = script.index("src.engine.automation.stage_hook_workorder_discovery")
    scaffold_idx = script.index("src.engine.automation.stage_hook_runtime_scaffold")
    nonfatal_idx = script.index("stage hook runtime scaffold returned fail-closed report (non-fatal)")
    artifact_idx = script.index('"$PROJECT_DIR/data/report/stage_hook_runtime_scaffold/stage_hook_runtime_scaffold_${TARGET_DATE}.json"')
    ev_idx = script.index('run_threshold_cycle_ev_and_wait "pre_workorder"')

    assert stage_hook_idx < scaffold_idx < nonfatal_idx < artifact_idx < ev_idx


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
    assert '"$PROJECT_DIR/data/report/pattern_lab_ai_review/pattern_lab_ai_review_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/producer_gap_discovery/producer_gap_discovery_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/stage_hook_runtime_scaffold/stage_hook_runtime_scaffold_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/ai_watching_score_smoothing_diagnostic/ai_watching_score_smoothing_diagnostic_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/entry_ai_gate_backtest/entry_ai_gate_backtest_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/ai_score_optimization_backtest/ai_score_optimization_backtest_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/rising_missed_first_touch_calibration/rising_missed_first_touch_calibration_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/scalping_pyramid_quality_calibration/scalping_pyramid_quality_calibration_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/rising_missed_classifier_prior/rising_missed_classifier_prior_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/one_share_threshold_opportunity/one_share_threshold_opportunity_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/runtime_apply_bridge/runtime_apply_bridge_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/runtime_approval_summary/runtime_approval_summary_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/tuning_performance_control_tower/tuning_performance_control_tower_${TARGET_DATE}.json"' in script
    assert '"$PROJECT_DIR/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_${TARGET_DATE}.json"' in script
    assert 'wait_for_file_artifact "$(next_stage2_checklist_path)" "next_stage2_checklist"' in script
    assert "src.engine.verify_threshold_cycle_postclose_chain" in script
    assert "--allow-pending-done-marker" in script
    assert "run_postclose_cmd env PYTHONPATH=. \"$VENV_PY\" -m src.engine.verify_threshold_cycle_postclose_chain" in script
    assert 'run_threshold_cycle_ev_and_wait "post_conversion_lane_workorder_refresh"' in script
    assert 'runtime_approval_summary_post_conversion_lane_workorder' in script
    assert '"$PROJECT_DIR/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_${TARGET_DATE}.json"' in script
    assert "pattern_lab_currentness_audit=$RUN_PATTERN_LAB_CURRENTNESS_AUDIT" in script
    assert "pattern_lab_ai_review=$RUN_PATTERN_LAB_AI_REVIEW" in script
    assert "pattern_lab_ai_review_provider=$PATTERN_LAB_AI_REVIEW_PROVIDER" in script
    assert "time_window_regime_counterfactual=$RUN_TIME_WINDOW_REGIME_COUNTERFACTUAL" in script
    assert "producer_gap_discovery=$RUN_PRODUCER_GAP_DISCOVERY" in script
    assert "producer_gap_discovery_ai_provider=$PRODUCER_GAP_DISCOVERY_AI_PROVIDER" in script
    assert "--rolling-sim-scan" in script
    assert "pattern_lab_propagation_audit=$RUN_PATTERN_LAB_PROPAGATION_AUDIT" in script
    assert "scalp_entry_adm=$RUN_SCALP_ENTRY_ADM" in script
    assert "entry_ai_gate_backtest=$RUN_ENTRY_AI_GATE_BACKTEST" in script
    assert "ai_score_optimization_backtest=$RUN_AI_SCORE_OPTIMIZATION_BACKTEST" in script
    assert "rising_missed_intraday_feedback_postclose=$RUN_RISING_MISSED_INTRADAY_FEEDBACK_POSTCLOSE" in script
    assert "rising_missed_scout_workorder=$RUN_RISING_MISSED_SCOUT_WORKORDER" in script
    assert "rising_missed_first_touch_calibration=$RUN_RISING_MISSED_FIRST_TOUCH_CALIBRATION" in script
    assert "scalping_pyramid_intraday_feedback_postclose=$RUN_SCALPING_PYRAMID_INTRADAY_FEEDBACK_POSTCLOSE" in script
    assert "scalping_pyramid_quality_calibration=$RUN_SCALPING_PYRAMID_QUALITY_CALIBRATION" in script
    assert "rising_missed_classifier_prior=$RUN_RISING_MISSED_CLASSIFIER_PRIOR" in script
    assert "one_share_threshold_opportunity=$RUN_ONE_SHARE_THRESHOLD_OPPORTUNITY" in script
    assert "one_share_threshold_opportunity_ai_provider=$ONE_SHARE_THRESHOLD_OPPORTUNITY_AI_PROVIDER" in script
    assert "lifecycle_decision_matrix=$RUN_LIFECYCLE_DECISION_MATRIX" in script
    assert "lifecycle_bucket_discovery=$RUN_LIFECYCLE_BUCKET_DISCOVERY" in script
    assert "runtime_apply_bridge=$RUN_RUNTIME_APPLY_BRIDGE" in script
    assert "tuning_performance_control_tower=$RUN_TUNING_PERFORMANCE_CONTROL_TOWER" in script
    assert "runtime_apply_gap_audit=true" in script
    assert "swing_lifecycle_matrix=$RUN_SWING_LIFECYCLE_MATRIX" in script
    assert "swing_lifecycle_bucket_discovery=$RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY" in script
    assert (
        'SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_PROVIDER="${KORSTOCKSCAN_SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_PROVIDER:-$SWING_THRESHOLD_AI_REVIEW_PROVIDER}"'
        in script
    )
    assert '--ai-provider "$SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_PROVIDER"' in script
    assert "swing_lifecycle_bucket_discovery_ai_provider=$SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_PROVIDER" in script
    assert "ai correction retry target_date=$TARGET_DATE" in script
    assert "ai correction final unavailable" in script


def test_stage2_ops_cron_installs_pyramid_intraday_feedback_5min():
    script = Path("deploy/install_stage2_ops_cron.sh").read_text(encoding="utf-8")

    assert "SCALPING_PYRAMID_INTRADAY_FEEDBACK_5MIN" in script
    assert "deploy/run_scalping_pyramid_intraday_feedback.sh" in script
    assert "!/SCALPING_PYRAMID_INTRADAY_FEEDBACK_5MIN/" in script


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
    assert 'wait_for_postclose_resources "gemini_scalping_pattern_lab"' not in script
    assert 'wait_for_postclose_resources "threshold_cycle_ev_${pass_label}"' in script
    assert 'run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.backfill_threshold_cycle_events' in script
    assert 'run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.daily_threshold_cycle_report' in script


def test_manual_calibration_wrapper_limits_resource_pressure():
    script = Path("deploy/run_threshold_cycle_calibration.sh").read_text(encoding="utf-8")
    installer = Path("deploy/install_threshold_cycle_cron.sh").read_text(encoding="utf-8")

    assert 'RUN_PHASE="${THRESHOLD_CYCLE_CALIBRATION_PHASE:-postclose}"' in script
    assert 'CALIBRATION_TIMEOUT_SEC="${THRESHOLD_CYCLE_CALIBRATION_TIMEOUT_SEC:-600}"' in script
    assert 'LOCK_FILE="${THRESHOLD_CYCLE_CALIBRATION_LOCK_FILE:-$PROJECT_DIR/tmp/threshold_cycle_calibration_${RUN_PHASE}.lock}"' in script
    assert 'IONICE_LEVEL="${THRESHOLD_CYCLE_CALIBRATION_IONICE_LEVEL:-7}"' in script
    assert 'NICE_LEVEL="${THRESHOLD_CYCLE_CALIBRATION_NICE_LEVEL:-12}"' in script
    assert 'flock -n 9' in script
    assert 'timeout --kill-after=30s "$CALIBRATION_TIMEOUT_SEC"' in script
    assert "5 12 * * 1-5" not in installer
    assert "deploy/run_threshold_cycle_calibration.sh" not in installer
    assert "threshold_cycle_calibration_intraday_cron.log" not in installer


def test_threshold_cycle_cron_stops_bot_for_postclose_without_restart():
    script = Path("deploy/install_threshold_cycle_cron.sh").read_text(encoding="utf-8")

    assert "THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=stop" in script
    assert "THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=restart" not in script
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
    assert "analysis/gemini_scalping_pattern_lab/run.sh" not in script
    assert 'record_step "gemini_scalping_pattern_lab" "skipped" 0 0 "retired_from_automatic_execution"' in script


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
    assert "./deploy/promote_gcp_preopen_artifacts.sh" in script
    assert "./deploy/run_threshold_cycle_preopen.sh" in script
    assert "threshold runtime env 미생성으로 봇 기동 중단" in script
    assert script.index('wait_for_threshold_runtime_env "$THRESHOLD_RUNTIME_ENV"') < script.index("../.venv/bin/python bot_main.py")
    assert "operator_runtime_overrides.env" in script
    assert script.index('OPERATOR_RUNTIME_OVERRIDES="../data/threshold_cycle/runtime_env/operator_runtime_overrides.env"') > script.index('. "$THRESHOLD_RUNTIME_ENV"')
    assert script.index('. "$OPERATOR_RUNTIME_OVERRIDES"') < script.index("../.venv/bin/python bot_main.py")
    assert script.index('BOT_CPU_AFFINITY="${KORSTOCKSCAN_BOT_CPU_AFFINITY:-$DEFAULT_BOT_CPU_AFFINITY}"') > script.index('. "$OPERATOR_RUNTIME_OVERRIDES"')


def test_preopen_wrapper_uses_lock_to_avoid_duplicate_bootstrap_run():
    script = Path("deploy/run_threshold_cycle_preopen.sh").read_text(encoding="utf-8")

    assert "threshold_cycle_preopen.lock" in script
    assert "flock -n 9" in script
    assert "threshold-cycle preopen already running" in script


def test_preopen_wrapper_treats_operator_lock_ready_manifest_as_succeeded():
    script = Path("deploy/run_threshold_cycle_preopen.sh").read_text(encoding="utf-8")

    assert "MANIFEST_CAPTURE_FILE" in script
    assert "handle_preopen_apply_result" in script
    assert "operator_runtime_env_lock_ready_missing_source_report" in script
    assert "operator_runtime_env_lock_preserved_missing_source_report" in script


def test_preopen_wrapper_smoke_allows_operator_lock_runtime_env_without_source_report(tmp_path):
    project = tmp_path / "project"
    date = "2026-06-20"
    apply_dir = project / "data/threshold_cycle/apply_plans"
    runtime_dir = project / "data/threshold_cycle/runtime_env"
    engine_dir = project / "src/engine"
    apply_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    engine_dir.mkdir(parents=True)
    (project / "src/__init__.py").write_text("", encoding="utf-8")
    (engine_dir / "__init__.py").write_text("", encoding="utf-8")
    (engine_dir / "threshold_cycle_preopen_apply.py").write_text(
        "import json\n"
        "import sys\n"
        "from pathlib import Path\n"
        "\n"
        "def main():\n"
        "    date = sys.argv[sys.argv.index('--date') + 1]\n"
        "    runtime_dir = Path('data/threshold_cycle/runtime_env')\n"
        "    runtime_dir.mkdir(parents=True, exist_ok=True)\n"
        "    env_path = runtime_dir / f'threshold_runtime_env_{date}.env'\n"
        "    json_path = runtime_dir / f'threshold_runtime_env_{date}.json'\n"
        "    env_path.write_text('export A=1\\n', encoding='utf-8')\n"
        "    json_path.write_text(json.dumps({'target_date': date, 'report_type': 'threshold_runtime_env'}), encoding='utf-8')\n"
        "    print(json.dumps({\n"
        "        'target_date': date,\n"
        "        'status': 'operator_runtime_env_lock_ready_missing_source_report',\n"
        "        'runtime_change': True,\n"
        "        'runtime_env_file': str(env_path),\n"
        "    }, ensure_ascii=False))\n"
        "    return 2\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    raise SystemExit(main())\n",
        encoding="utf-8",
    )
    (apply_dir / f"threshold_apply_{date}.json").write_text(json.dumps({"target_date": date}), encoding="utf-8")

    env = {
        **os.environ,
        "PROJECT_DIR": str(project),
        "VENV_PY": "python3",
    }
    result = subprocess.run(
        ["bash", "deploy/run_threshold_cycle_preopen.sh", date],
        cwd=Path.cwd(),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "[DONE] threshold-cycle preopen" in result.stdout
    status = json.loads(
        (project / f"data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_{date}.status.json").read_text(
            encoding="utf-8"
        )
    )
    assert status["status"] == "succeeded"
    assert status["reason"] == "operator_runtime_env_lock_preserved_missing_source_report"
    assert status["runtime_env_exists"] is True
    assert status["runtime_env_manifest_exists"] is True
    manifest = json.loads(
        (project / f"data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_{date}.manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["status"] == "operator_runtime_env_lock_ready_missing_source_report"


def test_gcp_preopen_push_wrapper_contract_is_fail_closed_and_artifact_only():
    script = Path("deploy/run_push_gcp_preopen_artifacts.sh").read_text(encoding="utf-8")

    assert "GCP_PUSH_HOST" in script
    assert "GCP_PUSH_USER" in script
    assert "GCP_PUSH_PROJECT_DIR" in script
    assert "GCP_PUSH_SSH_KEY" in script
    assert "GCP_PUSH_PORT" in script
    assert 'preopen_status.get("status") != "succeeded"' in script
    assert 'runtime_manifest.get("report_type") != "threshold_runtime_env"' in script
    assert "threshold_apply_${TARGET_DATE}.json" in script
    assert "threshold_runtime_env_${TARGET_DATE}.env" in script
    assert "threshold_runtime_env_${TARGET_DATE}.json" in script
    assert "threshold_runtime_env_verify_${TARGET_DATE}.json" in script
    assert "threshold_cycle_remote/apply_plans" in script
    assert "threshold_cycle_remote/runtime_env" in script
    assert ".tmp.aws_push_${TARGET_DATE}_$$" in script
    assert "mv -f --" in script
    assert "src.engine.threshold_cycle_preopen_apply" not in script
    assert "operator_runtime_env_locks" not in script
    assert "KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY" not in script


def test_gcp_preopen_push_cron_installs_one_post_preopen_entry():
    script = Path("deploy/install_gcp_preopen_push_cron.sh").read_text(encoding="utf-8")

    assert "GCP_PREOPEN_ARTIFACT_PUSH" in script
    assert 'GCP_PUSH_HOST="${GCP_PUSH_HOST:-songstockscan.ddns.net}"' in script
    assert 'GCP_PUSH_USER="${GCP_PUSH_USER:-windy80xyt}"' in script
    assert 'GCP_PUSH_PROJECT_DIR="${GCP_PUSH_PROJECT_DIR:-/home/windy80xyt/KORStockScan}"' in script
    assert "37 7 * * 1-5" in script
    assert "35 7 * * 1-5" not in script
    assert "GCP_PUSH_HOST=$GCP_PUSH_HOST GCP_PUSH_USER=$GCP_PUSH_USER GCP_PUSH_PROJECT_DIR=$GCP_PUSH_PROJECT_DIR" in script
    assert "deploy/run_push_gcp_preopen_artifacts.sh" in script
    assert "!/GCP_PREOPEN_ARTIFACT_PUSH/" in script
    assert script.count("GCP_PREOPEN_ARTIFACT_PUSH") == 2


def test_gcp_preopen_push_wrapper_smoke_with_stubbed_ssh_and_scp(tmp_path):
    project = tmp_path / "project"
    date = "2026-06-20"
    preopen_dir = project / "data/report/threshold_cycle_preopen_status"
    apply_dir = project / "data/threshold_cycle/apply_plans"
    runtime_dir = project / "data/threshold_cycle/runtime_env"
    bin_dir = tmp_path / "bin"
    log_path = tmp_path / "transport.log"
    preopen_dir.mkdir(parents=True)
    apply_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    bin_dir.mkdir()

    (preopen_dir / f"threshold_cycle_preopen_{date}.status.json").write_text(
        json.dumps({"target_date": date, "status": "succeeded"}),
        encoding="utf-8",
    )
    (apply_dir / f"threshold_apply_{date}.json").write_text(
        json.dumps({"target_date": date}),
        encoding="utf-8",
    )
    (runtime_dir / f"threshold_runtime_env_{date}.env").write_text("export A=1\n", encoding="utf-8")
    (runtime_dir / f"threshold_runtime_env_{date}.json").write_text(
        json.dumps({"target_date": date, "report_type": "threshold_runtime_env"}),
        encoding="utf-8",
    )
    (runtime_dir / f"threshold_runtime_env_verify_{date}.json").write_text(
        json.dumps({"target_date": date, "status": "pass"}),
        encoding="utf-8",
    )

    (bin_dir / "ssh").write_text(
        "#!/usr/bin/env bash\n"
        f"printf 'ssh %s\\n' \"$*\" >> {log_path}\n"
        "exit 0\n",
        encoding="utf-8",
    )
    (bin_dir / "scp").write_text(
        "#!/usr/bin/env bash\n"
        f"printf 'scp %s\\n' \"$*\" >> {log_path}\n"
        "exit 0\n",
        encoding="utf-8",
    )
    os.chmod(bin_dir / "ssh", 0o755)
    os.chmod(bin_dir / "scp", 0o755)

    env = {
        **os.environ,
        "PROJECT_DIR": str(project),
        "VENV_PY": "python3",
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "GCP_PUSH_HOST": "gcp.example",
        "GCP_PUSH_USER": "ubuntu",
        "GCP_PUSH_PROJECT_DIR": "/srv/KORStockScan",
    }
    result = subprocess.run(
        ["bash", "deploy/run_push_gcp_preopen_artifacts.sh", date],
        cwd=Path.cwd(),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "[DONE] gcp-preopen-artifact-push" in result.stdout
    log_text = log_path.read_text(encoding="utf-8")
    assert "mkdir -p -- '/srv/KORStockScan/data/threshold_cycle_remote/apply_plans' '/srv/KORStockScan/data/threshold_cycle_remote/runtime_env'" in log_text
    assert "mkdir -p -- '/srv/KORStockScan/data/threshold_cycle_remote/report/threshold_cycle_preopen_status'" in log_text
    assert log_text.count("scp ") == 5
    assert log_text.count("mv -f --") == 5
    assert f"threshold_cycle_preopen_{date}.status.json.tmp.aws_push_{date}_" in log_text
    assert f"threshold_apply_{date}.json.tmp.aws_push_{date}_" in log_text
    status = json.loads((project / f"data/report/gcp_preopen_push_status/gcp_preopen_push_{date}.status.json").read_text(encoding="utf-8"))
    assert status["status"] == "succeeded"
    assert len(status["pushed_files"]) == 5


def test_gcp_preopen_bridge_promotes_staging_artifacts_to_live_runtime_dir(tmp_path):
    project = tmp_path / "project"
    date = "2026-06-20"
    staging_preopen_dir = project / "data/threshold_cycle_remote/report/threshold_cycle_preopen_status"
    staging_apply_dir = project / "data/threshold_cycle_remote/apply_plans"
    staging_runtime_dir = project / "data/threshold_cycle_remote/runtime_env"
    live_apply_dir = project / "data/threshold_cycle/apply_plans"
    live_runtime_dir = project / "data/threshold_cycle/runtime_env"
    live_preopen_dir = project / "data/report/threshold_cycle_preopen_status"
    staging_preopen_dir.mkdir(parents=True)
    staging_apply_dir.mkdir(parents=True)
    staging_runtime_dir.mkdir(parents=True)
    live_apply_dir.mkdir(parents=True)
    live_runtime_dir.mkdir(parents=True)
    live_preopen_dir.mkdir(parents=True)

    (staging_preopen_dir / f"threshold_cycle_preopen_{date}.status.json").write_text(
        json.dumps({"target_date": date, "status": "succeeded"}),
        encoding="utf-8",
    )
    (staging_apply_dir / f"threshold_apply_{date}.json").write_text(
        json.dumps({"target_date": date, "runtime_env_file": f"/tmp/threshold_runtime_env_{date}.env"}),
        encoding="utf-8",
    )
    (staging_runtime_dir / f"threshold_runtime_env_{date}.env").write_text("export A=1\n", encoding="utf-8")
    (staging_runtime_dir / f"threshold_runtime_env_{date}.json").write_text(
        json.dumps({"target_date": date, "report_type": "threshold_runtime_env"}),
        encoding="utf-8",
    )
    (staging_runtime_dir / f"threshold_runtime_env_verify_{date}.json").write_text(
        json.dumps({"target_date": date, "status": "pass"}),
        encoding="utf-8",
    )

    env = {
        **os.environ,
        "PROJECT_DIR": str(project),
        "VENV_PY": "python3",
    }
    result = subprocess.run(
        ["bash", "deploy/promote_gcp_preopen_artifacts.sh", date],
        cwd=Path.cwd(),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "[DONE] gcp-preopen-bridge" in result.stdout
    assert (live_preopen_dir / f"threshold_cycle_preopen_{date}.status.json").exists()
    assert (live_apply_dir / f"threshold_apply_{date}.json").exists()
    assert (live_runtime_dir / f"threshold_runtime_env_{date}.env").read_text(encoding="utf-8") == "export A=1\n"
    assert (live_runtime_dir / f"threshold_runtime_env_{date}.json").exists()
    assert (live_runtime_dir / f"threshold_runtime_env_verify_{date}.json").exists()
    status = json.loads((project / f"data/report/gcp_preopen_bridge_status/gcp_preopen_bridge_{date}.status.json").read_text(encoding="utf-8"))
    assert status["status"] == "succeeded"
    assert len(status["promoted_files"]) == 5


def test_gcp_preopen_bridge_skips_when_staging_artifacts_are_missing(tmp_path):
    project = tmp_path / "project"
    date = "2026-06-20"
    env = {
        **os.environ,
        "PROJECT_DIR": str(project),
        "VENV_PY": "python3",
    }
    result = subprocess.run(
        ["bash", "deploy/promote_gcp_preopen_artifacts.sh", date],
        cwd=Path.cwd(),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "[SKIP] gcp-preopen-bridge" in result.stdout
    status = json.loads((project / f"data/report/gcp_preopen_bridge_status/gcp_preopen_bridge_{date}.status.json").read_text(encoding="utf-8"))
    assert status["status"] == "skipped"
    assert status["reason"] == "no_staging_artifacts"


def test_gcp_preopen_bridge_fails_when_staging_preopen_status_is_missing(tmp_path):
    project = tmp_path / "project"
    date = "2026-06-20"
    staging_apply_dir = project / "data/threshold_cycle_remote/apply_plans"
    staging_runtime_dir = project / "data/threshold_cycle_remote/runtime_env"
    staging_apply_dir.mkdir(parents=True)
    staging_runtime_dir.mkdir(parents=True)

    (staging_apply_dir / f"threshold_apply_{date}.json").write_text(
        json.dumps({"target_date": date}),
        encoding="utf-8",
    )
    (staging_runtime_dir / f"threshold_runtime_env_{date}.env").write_text("export A=1\n", encoding="utf-8")
    (staging_runtime_dir / f"threshold_runtime_env_{date}.json").write_text(
        json.dumps({"target_date": date, "report_type": "threshold_runtime_env"}),
        encoding="utf-8",
    )

    env = {
        **os.environ,
        "PROJECT_DIR": str(project),
        "VENV_PY": "python3",
    }
    result = subprocess.run(
        ["bash", "deploy/promote_gcp_preopen_artifacts.sh", date],
        cwd=Path.cwd(),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode != 0
    assert "[FAIL] gcp-preopen-bridge" in result.stdout
    assert "missing_staging_artifact" in result.stdout


def test_gcp_preopen_push_wrapper_fails_on_missing_or_bad_preopen_status(tmp_path):
    project = tmp_path / "project"
    date = "2026-06-20"
    apply_dir = project / "data/threshold_cycle/apply_plans"
    runtime_dir = project / "data/threshold_cycle/runtime_env"
    apply_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    (apply_dir / f"threshold_apply_{date}.json").write_text(json.dumps({"target_date": date}), encoding="utf-8")
    (runtime_dir / f"threshold_runtime_env_{date}.env").write_text("export A=1\n", encoding="utf-8")
    (runtime_dir / f"threshold_runtime_env_{date}.json").write_text(
        json.dumps({"target_date": date, "report_type": "threshold_runtime_env"}),
        encoding="utf-8",
    )

    env = {
        **os.environ,
        "PROJECT_DIR": str(project),
        "VENV_PY": "python3",
        "GCP_PUSH_HOST": "gcp.example",
        "GCP_PUSH_USER": "ubuntu",
        "GCP_PUSH_PROJECT_DIR": "/srv/KORStockScan",
    }
    result = subprocess.run(
        ["bash", "deploy/run_push_gcp_preopen_artifacts.sh", date],
        cwd=Path.cwd(),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode != 0
    assert "[FAIL] gcp-preopen-artifact-push" in result.stdout
    assert "missing_local_artifact" in result.stdout

    preopen_dir = project / "data/report/threshold_cycle_preopen_status"
    preopen_dir.mkdir(parents=True)
    (preopen_dir / f"threshold_cycle_preopen_{date}.status.json").write_text(
        json.dumps({"target_date": date, "status": "failed"}),
        encoding="utf-8",
    )
    result = subprocess.run(
        ["bash", "deploy/run_push_gcp_preopen_artifacts.sh", date],
        cwd=Path.cwd(),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode != 0
    assert "[FAIL] gcp-preopen-artifact-push" in result.stdout
    assert "preopen_status_not_succeeded:failed" in result.stdout


def test_gcp_preopen_push_wrapper_fails_on_missing_ssh_config_before_transport(tmp_path):
    project = tmp_path / "project"
    date = "2026-06-20"
    env = {**os.environ, "PROJECT_DIR": str(project), "VENV_PY": "python3"}
    result = subprocess.run(
        ["bash", "deploy/run_push_gcp_preopen_artifacts.sh", date],
        cwd=Path.cwd(),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode != 0
    assert "missing_env:GCP_PUSH_HOST" in result.stdout
