# 2026-06-24 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-04`, `clean_tuning_baseline_ts_kst=2026-06-04T14:29:09+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.
- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-06-23` postclose -> `2026-06-24`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[SwingPreFinalAutoAndFinalApprovalPreopen0624] 스윙 pre-final auto state 및 final approval artifact 확인` (`Due: 2026-06-24`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-23.json), [threshold_cycle_ev_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-23.json)
  - 판정 기준: pre-final은 parsed AI Tier2 auto state가 있어야 하고, final-stage는 사용자 승인 artifact가 있어야 한다.
  - 금지: 스윙 full-live 전환, cap release, provider/bot 변경, hard-safety 완화를 pre-final auto state로 처리하지 않는다.
  - 다음 액션: `pre_final_auto_selected`, `final_approval_artifact_present`, `blocked_by_policy` 중 하나로 닫는다.
  - 판정: `pre_final_auto_selected`
  - 근거: [swing_runtime_approval_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-23.json) `approval_requests`에 `swing_model_floor`, `swing_market_regime_sensitivity` 2건이 있고 둘 다 `auto_approval_state=ai_tier2_auto_approved`, `auto_promotion_contract.state=dry_run_auto_apply_ready`, `approval_artifact_required=false`, `approval_runtime_scope=swing_dry_run_env_only`로 닫혔다. [threshold_apply_2026-06-24.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-24.json)도 `swing_runtime_approval.requested=2`, `approved=2`, `selected=1`, `approval_artifact=null`이며 full-live final approval artifact 요구는 없다. 다만 실제 bot PID `10567`의 `/proc/10567/environ`에는 `KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_ENABLED=false`가 로드돼 있고, 이는 [operator_runtime_overrides.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/operator_runtime_overrides.env)에서 같은 key를 `false`로 덮어쓴 결과라 pre-final auto selected 상태가 그대로 runtime에 유지되지는 않는다.
  - 다음 액션: 스윙은 오늘도 dry-run/pre-final 범위로만 취급하고 full-live 전환은 열지 않는다. 장중에는 [RuntimeEnvIntradayObserve0624](/home/ubuntu/KORStockScan/docs/checklists/2026-06-24-stage2-todo-checklist.md:47)에서 operator override로 인한 swing sim auto policy 비활성 상태를 provenance와 함께 재확인한다.

- [x] `[ThresholdEnvAutoApplyPreopen0624] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-06-24`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-23.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 판정: `applied_guard_passed_env`
  - 근거: [threshold_cycle_preopen_2026-06-24.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-06-24.status.json)이 `status=succeeded`, `reason=completed`, `apply_plan_exists=true`, `runtime_env_exists=true`, `runtime_env_manifest_exists=true`, `updated_at=2026-06-24T07:35:01+09:00`로 닫혔다. [threshold_runtime_env_2026-06-24.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-24.json)은 selected family 22개와 `runtime_apply_bridge_family=null`, `operator_runtime_env_lock=null`을 기록하고, [threshold_runtime_env_verify_2026-06-24.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-06-24.json)은 `status=pass`, `passed=true`, `pid_passed=true`, `missing_family_count=0`이다. 실제 bot PID `10567`는 env 생성 시각 이후인 `07:44`에 기동됐고 `/proc/10567/environ`에서 `KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE=2026-06-24`, `KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_ENABLED=true`, `KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_ENABLED=true`, `KORSTOCKSCAN_SCALP_SIM_AI_BUDGET_ENABLED=true`, `KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED=true`, `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true`가 확인됐다. 다만 [operator_runtime_overrides.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/operator_runtime_overrides.env)이 env source 뒤에 적용되면서 `KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_ENABLED=false`로 일부 후속 개입이 있었다.
  - 다음 액션: threshold preopen apply 산출물 자체는 정상으로 유지하되, 장중 관찰에서는 runtime env manifest와 실제 `/proc/<pid>/environ` 차이를 분리 기록한다. bridge family와 blocked-by-policy 후보는 수동 env override로 열지 않고 장후 `HumanInterventionSummary0624`에서 다시 분류한다.

- [x] `[PreopenAutomationHealthCheck20260624] 장전 자동화체인 상태 확인` (`Due: 2026-06-24`, `Slot: PREOPEN`, `TimeWindow: 08:00~09:00`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md:297), [threshold_cycle_preopen_2026-06-24.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-06-24.status.json), [threshold_apply_2026-06-24.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-24.json), [threshold_runtime_env_2026-06-24.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-24.json), [threshold_runtime_env_verify_2026-06-24.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-06-24.json), [ensemble_scanner.log](/home/ubuntu/KORStockScan/logs/ensemble_scanner.log), [threshold_cycle_preopen_cron.log](/home/ubuntu/KORStockScan/logs/threshold_cycle_preopen_cron.log), [bot_history.log](/home/ubuntu/KORStockScan/logs/bot_history.log:1), [daily_recommendations_v2.csv](/home/ubuntu/KORStockScan/data/daily_recommendations_v2.csv), [daily_recommendations_v2_diagnostics.json](/home/ubuntu/KORStockScan/data/daily_recommendations_v2_diagnostics.json), [operator_runtime_overrides.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/operator_runtime_overrides.env)
  - 판정: `warning`
  - 근거: runbook 장전 확인 절차 기준으로 preopen wrapper와 scanner freshness는 통과했다. [threshold_cycle_preopen_cron.log](/home/ubuntu/KORStockScan/logs/threshold_cycle_preopen_cron.log)에 `[DONE] threshold-cycle preopen target_date=2026-06-24 finished_at=2026-06-24T07:35:01+0900`가 있고, [ensemble_scanner.log](/home/ubuntu/KORStockScan/logs/ensemble_scanner.log)에도 `[DONE] final_ensemble_scanner target_date=2026-06-24 finished_at=2026-06-24T07:20:52+0900`가 남아 있다. [daily_recommendations_v2_diagnostics.json](/home/ubuntu/KORStockScan/data/daily_recommendations_v2_diagnostics.json)은 `latest_date=2026-06-23`, `selected_count=2`, `selection_mode=SELECTED`, `fallback_written_to_recommendations=false`이고, [daily_recommendations_v2.csv](/home/ubuntu/KORStockScan/data/daily_recommendations_v2.csv)에는 `2026-06-23` 추천 2건이 존재한다. [threshold_runtime_env_verify_2026-06-24.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-06-24.json) `status=pass`와 `bash deploy/run_error_detection.sh full` 결과 `summary_severity=pass`도 확보됐다. 다만 [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)가 daily runtime env source 뒤에 [operator_runtime_overrides.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/operator_runtime_overrides.env)를 다시 로드하고, 실제 `/proc/10567/environ`에서는 runtime env artifact의 `KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_ENABLED=true`가 `false`로 바뀌어 있다. 즉 자동화체인 자체는 정상이나 PREOPEN artifact와 실제 프로세스 env가 일부 분기돼 `pass`로 닫기 어렵다.
  - 다음 액션: 같은 날짜 PREOPEN backlog는 재실행하지 않는다. 장중 [RuntimeEnvIntradayObserve0624](/home/ubuntu/KORStockScan/docs/checklists/2026-06-24-stage2-todo-checklist.md:47)에서 operator override가 남긴 실제 runtime provenance 차이를 추적하고, 장후 `HumanInterventionSummary0624`에는 자동 apply 성공과 별도 operator override 개입을 분리 기록한다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0624] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-06-24`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-23.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, lifecycle_decision_matrix_runtime, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, weak_context_late_entry_guard_runtime가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0624] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-06-24`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-23.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0624] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-06-24`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-06-24.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-24.jsonl), [threshold_events_2026-06-24.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-06-24.jsonl), [observation_source_quality_audit_2026-06-24.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-24.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-06-24 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (21:40~23:05)

- [ ] `[PostcloseSourceQualityGateReview0624] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-06-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-06-24.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-24.json), [threshold_cycle_ev_2026-06-24.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-24.json), [code_improvement_workorder_2026-06-24.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-24.json), [threshold_cycle_postclose_verification_2026-06-24.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-24.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0624] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-06-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-23.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0624] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-06-24`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-23.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0624] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-06-24`, `Slot: POSTCLOSE`, `TimeWindow: 22:05~22:20`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-06-23.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-23.md), [code_improvement_workorder_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-23.json)
  - 판정 기준: selected_order_count=132와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0624] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-06-24`, `Slot: POSTCLOSE`, `TimeWindow: 22:35~22:50`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-23.json), [runtime_apply_gap_audit_2026-06-23.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-23.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`402`, rollup_required_count=`402`, sim_live_connected_quiet_gap_count=`3`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'exclusion_dimension_candidate': 6, 'parent_conflict_child': 29, 'positive_source_only_keep_collecting': 393}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0624] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-06-24`, `Slot: POSTCLOSE`, `TimeWindow: 22:50~23:05`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-06-23.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`16`, run_count=`16`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, scalp_sim_ai_deferred_review, pattern_lab_currentness_audit`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:15, source_missing_or_unreadable:7, upstream_drift_signal:7, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-06-24 15:47:17`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-06-24.md`
- `Trade Review`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
