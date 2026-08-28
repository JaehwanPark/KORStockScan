# 2026-08-28 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime 변경은 사용자 명시 지시가 있을 때만 기존 `bounded_tunable` 단일 축에 한해 허용한다. fresh/conflict-free source, 유효 effective price, 단일 blocker 인과, same-stage owner 비충돌, before/after·PID/env provenance·rollback·즉시 attribution을 모두 남긴다. hard safety, stale/conflict, price freshness, broker/account/order/quantity/cooldown, provider, bot, cap, 요청수량은 변경하거나 우회하지 않는다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-05`, `clean_tuning_baseline_ts_kst=2026-06-05T00:00:00+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.
- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-08-27` postclose -> `2026-08-28`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0828] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-08-28`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-27.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0828] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-08-28`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-08-27.json), [code_improvement_workorder_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-27.json), [threshold_apply_2026-08-28.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-28.json), [threshold_runtime_env_2026-08-28.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-28.json), [threshold_runtime_env_verify_2026-08-28.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-08-28.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`4`, forced_scout_with_post_sell_count=`2`, post_sell_join_coverage_pct=`0.527704`, outcome_coverage_state=`partial`, profitable_forced_scout_count=`2`, loss_or_flat_forced_scout_count=`0`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0828] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-08-28`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-27.json)
  - 전일 postclose candidate_selected_families=entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, post_probe_winner_recovery, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0828] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-08-28`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-27.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0828] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-08-28`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-28.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-28.jsonl), [threshold_events_2026-08-28.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-28.jsonl), [observation_source_quality_audit_2026-08-28.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-28.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-08-28 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

- [ ] `[LatencyDirectRecheckRetirementAcceptance0828] 은퇴한 latency direct-canary 재검사 키의 다음 PREOPEN 제거·PID 반영 확인` (`Due: 2026-08-31`, `Slot: PREOPEN`, `TimeWindow: 08:45~09:00`, `Track: RuntimeStability`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [threshold_runtime_env_2026-08-28.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-28.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [runtime_flags.py](/home/ubuntu/KORStockScan/src/utils/runtime_flags.py)
  - 판정 기준: Plan Rebase의 post-block submit retry 제거 계약에 따라 `KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_{ENABLED,ACTIVE_DATE,MIN_WAIT_SEC,TTL_SEC,SPREAD_WORSEN_BPS}`가 operator/runtime env와 새 PID env에 없고 PREOPEN handoff verify가 pass인지 확인한다. 2026-08-28 PID `13273`은 기동 커밋 `7b8e59fcd8236bf8ff4270247f70dd4b2a419d9d`에서 authority key 두 개를 보유했고 `tp1_direct_recheck_expired`가 실제 관측되어 현재 PID 미반영 상태로 분리한다.
  - 금지: 현재 PID env 수동 변경, broker/order/quantity/threshold/provider 변경, 미체결·독립 owner custody를 대사하지 않은 재기동, 은퇴 키를 PREOPEN/operator override에 재등록하지 않는다.
  - 완료 조건: review finding 0과 targeted validation 통과, operator/runtime env recheck namespace key 0건, PREOPEN verify pass, 새 PID env 동일 key 0건, 새 PID 이후 `tp1_direct_recheck_*` enforcement event 0건을 같은 source/provenance 창에서 확인한다.
  - 다음 액션: operator override 정리는 PREOPEN 권한 owner가 수행하고, 새 PID가 없으면 `implemented_but_current_pid_not_reflected`, verify가 차단되면 `retired_override_fail_closed`, 새 PID 수용까지 닫히면 `retirement_reflected`로 기록한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0828] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-08-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-08-28.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-28.json), [threshold_cycle_ev_2026-08-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-28.json), [code_improvement_workorder_2026-08-28.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-28.json), [threshold_cycle_postclose_verification_2026-08-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-28.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0828] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-08-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-08-27.json), [threshold_cycle_ev_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-27.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0828] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-08-28`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-27.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[MainAIQualitySourceGapRuntimeExecutionReceiptCustodyRepair0828] RuntimeExecutionReceiptCustodyRepair main lifecycle source gap 복구 확인` (`Due: 2026-08-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-08-27.json)
  - 판정 기준: workorder `main-ai-gap-dd22e1405110d777f3f467fb`의 owner=`RuntimeExecutionReceiptCustodyRepair`, reason_codes=`real_submitted_lifecycle_count=5, broker_execution_unique_count=4, execution_report_materialized_companion_binding_mismatch_count=1, lifecycle_exact_join_missing_count=7`를 source-only producer 보완으로 닫는다. 공식 raw execution envelope의 order/execution identity를 합성 없이 검증하고 결손 lifecycle만 제외한 뒤 paired producer를 재검증한다.
  - 완료 조건: official raw execution envelope/order/execution identity is complete for at least one reconciled lifecycle; materialized execution companions bind to their exact request census; custody and order authority remain unchanged
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[CodeImprovementWorkorderReview0828] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-08-28`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-08-27.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-08-27.md), [code_improvement_workorder_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-27.json)
  - 판정 기준: selected_order_count=49와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0828] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-08-28`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-27.json), [runtime_apply_gap_audit_2026-08-27.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-27.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`308`, rollup_required_count=`308`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 307}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[MachineLifecycleTurnoverObjectiveFollowup0828] 위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인` (`Due: 2026-08-28`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_policy_approval_postclose_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_2026-08-27.json), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 판정 기준: 승인 후보 수와 무관하게 `followup_required=true`인 미완료 목적 항목 `machine_lifecycle_turnover_policy_research_v1`(status=`EVIDENCE_ACCUMULATING`, next_action=`reconcile_exact_owner_terminal_outcomes_before_waiting`)의 상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.
  - 상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, `EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. `CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.
  - 권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[AutomationTriggerDecisionSummary0828] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-08-28`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-08-27.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`9`, skip_count=`0`, source_missing_count=`4`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:8, disabled_by_runtime_policy:5, upstream_drift_signal:5, source_missing_or_unreadable:4, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

- [x] `[LogWriterOwnedRollover0828] 반복 writer-defer 구조 결함의 owner-controlled rollover 구현` (`Due: 2026-08-28`, `Slot: POSTCLOSE`, `TimeWindow: 22:00~23:30`, `Track: RuntimeStability`)
  - Source: [run_owned_log_rotation.sh](/home/ubuntu/KORStockScan/deploy/run_owned_log_rotation.sh), [run_with_owned_log.sh](/home/ubuntu/KORStockScan/deploy/run_with_owned_log.sh), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정: cleanup이 unknown writer active pathname을 임의 rename/truncate하지 않는 기존 fail-closed 경계는 유지하고, error detector·panic-sell defense·rising-missed feedback·threshold preopen/postclose·cleanup cron의 실제 writer가 파일을 열기 전에 자기 log만 rollover하는 owner 경로를 구현했다. owner/path lock, open inode 0건, pre/post metadata·원문 SHA-256, no-clobber gzip generation, decoded SHA-256 roundtrip과 append-only receipt를 강제한다.
  - 권한 경계: filesystem instrumentation/provenance 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.
  - 검증: shell syntax, quiescent/open-inode/동일-generation test, cron installer 문자열 검사, review finding 0과 targeted validation으로 닫는다.

- [x] `[MarketWeaknessObservationHysteresis0828] 시장 약세·패닉 관찰 분리와 해제 정확성 보완` (`Due: 2026-08-28`, `Slot: POSTCLOSE`, `TimeWindow: 22:00~23:30`, `Track: RuntimeStability`)
  - Source: [market_panic_breadth_collector.py](/home/ubuntu/KORStockScan/src/engine/market_panic_breadth_collector.py), [panic_sell_defense_report.py](/home/ubuntu/KORStockScan/src/engine/panic_sell_defense_report.py), [notify_panic_state_transition.py](/home/ubuntu/KORStockScan/src/engine/notify_panic_state_transition.py), [run_panic_sell_defense_intraday.sh](/home/ubuntu/KORStockScan/deploy/run_panic_sell_defense_intraday.sh)
  - 판정: `PANIC_SELL`과 broad/single-market weakness 알림 owner를 분리했다. 약세 시작은 같은 날짜의 KOSPI·KOSDAQ+최소 3개 업종 fresh 고유 snapshot 2회, 해제는 명시적 recovery margin을 통과한 고유 snapshot 3회로 고정했으며 duplicate/60초 미만/stale/source-quality·identity·authority-blocked/`NEAR_WEAKNESS_BOUNDARY`는 streak를 전진시키지 않는다. 동일 broker sell order에 연결된 반복 exit signal은 1회만 panic count에 포함한다.
  - 권한 경계: source-only 관찰·알림·반사실 수집이며 위젯/에피소드 신규매수 차단, 미체결 취소, 기존 target/holding/exit 변경, 수량·가격·threshold/provider/bot 변경 권한이 없다.
  - 검증: collector/report/notifier targeted test, wrapper syntax, parser validation, compile 및 review finding 0으로 닫는다.

- [ ] `[WeakDayOwnerResponseCounterfactual0904] 약세일 owner별 신규진입 대응 반사실 평가` (`Due: 2026-09-04`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:30`, `Track: ScalpingLogic`)
  - Source: [market_weakness_observations](/home/ubuntu/KORStockScan/data/report/market_weakness_observations), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py), [widget_auto_trade](/home/ubuntu/KORStockScan/src/trading/widget_auto_trade), [regular_two_leg_machine.py](/home/ubuntu/KORStockScan/src/trading/order/regular_two_leg_machine.py)
  - 판정 기준: main/widget/episode owner를 분리하고 `current control`, `delay until recovery confirmed`, `skip during confirmed weakness`, `relative-strength+liquidity exception`을 executable entry/exit와 고정 비용으로 비교한다. 비용차감 EV, adverse-first, missed upside, fill feasibility, 자본점유시간을 broad/single-market 및 KOSPI/KOSDAQ constituent별로 산출한다.
  - 표본 조건: clean baseline 이후의 immutable observation과 exact owner terminal outcome만 사용하고, weak window 안의 completed와 HELD/right-censored를 분리한다. 거래일·owner·시장별 표본 floor가 닫히기 전에는 `EVIDENCE_ACCUMULATING`으로 유지한다.
  - 금지: 일중 final snapshot만으로 event-time 약세를 소급 추정하거나, source-only 결과로 신규매수 차단·미체결 취소·forced exit·수량/가격/target/holding 계약을 자동 변경하지 않는다.
  - 다음 액션: owner별 비용차감 EV와 missed-upside 비훼손을 통과한 단일 신규진입 축만 별도 사용자 승인 후보로 만들고, 기존 보유·target 주문은 모든 arm에서 그대로 유지한다.

- [ ] `[WidgetEpisodeLiquidityGuardPreopenAcceptance0831] 위젯·에피소드 신규매수 양방향 잔량·체결속도 가드 설치·기동 반영 확인` (`Due: 2026-08-31`, `Slot: PREOPEN`, `TimeWindow: 08:45~09:00`, `Track: ScalpingLogic`)
  - Source: [entry_liquidity_guard.py](/home/ubuntu/KORStockScan/src/trading/order/entry_liquidity_guard.py), [regular_two_leg_machine.py](/home/ubuntu/KORStockScan/src/trading/order/regular_two_leg_machine.py), [engine.py](/home/ubuntu/KORStockScan/src/trading/widget_auto_trade/engine.py), [test_entry_liquidity_guard.py](/home/ubuntu/KORStockScan/src/tests/test_entry_liquidity_guard.py)
  - 판정 기준: 신규 위젯 초기·추가매수와 독립 에피소드 첫 매수 전에 fresh `ka10004` venue-qualified 호가를 한 번만 읽고, 최우선 매수·매도 잔량이 각각 `max(100주, 해당 신규 주문 총수량×5)` 이상일 때만 다음 가드로 진행하는지 확인한다. 이어서 route-qualified `ka10003` 최근 10체결이 최신 5초 이내, 10체결 span 20초 이내, 합산 체결량 `max(20주, 신규 주문 총수량×2)` 이상일 때만 주문 owner가 진행해야 한다. `181710` NHN의 97주/93주 경계와 CJ CGV·영원무역·NHN의 10체결 span 45초/35초/29초 fixture는 모두 주문 0건으로 재현되어야 한다.
  - 금지: 체결방향이나 체결강도를 체결속도로 대체하지 않는다. 기존 보유, TARGET_OPEN, 매도·취소·reprice·청산 owner에 잔량·체결속도 가드를 소급 적용하거나 main/widget/episode custody를 합치지 않는다. 현재 장중 process를 이 항목만으로 임의 재기동하지 않는다.
  - 현재 반영 상태 (`2026-08-28 15:32 KST`): production source는 위젯 초기·추가매수, 삼성 morning/reentry/midday/afternoon 및 `LowPriceTwoLegMachine` 전체 profile에 연결됐고 review fixture가 이를 전수 경로 기준으로 검증한다. 당일 07:58 기동 widget PID `13858`과 custody-only 한국전력 morning/afternoon PID `52387`/`198660`은 변경 전 process이므로 `implemented_not_runtime_reflected`다. 한국전력 두 process는 `attempt_consumed=true`와 `TARGET_OPEN`만 관리하므로 신규매수 경로가 없으며, owner별 broker 대사 없이 재기동하지 않는다.
  - 완료 조건: review finding 0, targeted validation 통과, 설치 revision과 다음 기동 process revision 일치, 첫 eligible 자연표본의 `entry_liquidity_guard_passed|entry_execution_velocity_guard_passed|entry_blocked_liquidity_guard|entry_blocked_execution_velocity_guard|entry_liquidity_blocked_before_buy|entry_execution_velocity_blocked_before_buy` provenance 확인, 기존 owner 미체결·보유·target 비변경, 중복 신규주문 0건.
  - 다음 액션: 설치 또는 새 process 반영 전에는 `implemented_not_runtime_reflected`, 반영 후 자연표본이 없으면 `runtime_reflected_no_natural_sample`, pass/block provenance와 주문 0/정상 제출이 일치하면 `runtime_reflected_and_verified`로 닫는다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
