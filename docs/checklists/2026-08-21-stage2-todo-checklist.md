# 2026-08-21 Stage2 To-Do Checklist

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

- [x] `[PostcloseTuningSemanticIntegrity0821] 장후 튜닝 결과 의미계약·generation·consumer 검증 보강` (`Due: 2026-08-21`, `Slot: POSTCLOSE`, `TimeWindow: 23:20~23:59`, `Track: RuntimeStability`)
  - Source: [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [threshold_cycle_ev_report.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_ev_report.py), [verify_threshold_cycle_postclose_chain.py](/home/ubuntu/KORStockScan/src/engine/verify_threshold_cycle_postclose_chain.py), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: same-day와 rolling source split을 분리하고, provisional bad-entry volume은 terminal executable counterfactual EV 전까지 runtime apply 표본으로 금지하며, parsed AI guard effective state를 runtime approval에 반영한다. 최종 EV 뒤 workorder content fingerprint를 재생성하고 calibration/AI/EV/runtime generation 및 실제 swing 실행 범위와 strategy scope 일치를 verifier가 확인한다.
  - 금지: raw 후보 이벤트 수를 terminal outcome 표본으로 사용하거나, AI가 `exclude_from_threshold_candidate_review`로 보낸 family를 deterministic `adjust_up`만으로 PREOPEN eligible로 표시하거나, 오래된 workorder fingerprint를 DONE으로 인정하지 않는다.

- [ ] `[LowPriceTwoLeg0821InstallVerify0824] 8월 21일 승인 14프로필 서비스 설치 및 PREOPEN 검증` (`Due: 2026-08-24`, `Slot: PREOPEN`, `TimeWindow: 08:40~09:10`, `Track: ScalpingLogic`)
  - Source: [low_price_two_leg_expanded_profile_evidence_2026-08-21.json](/home/ubuntu/KORStockScan/data/config/low_price_two_leg_expanded_profile_evidence_2026-08-21.json), [low-price-two-leg-machines.md](/home/ubuntu/KORStockScan/docs/low-price-two-leg-machines.md), [install_low_price_two_leg_systemd.sh](/home/ubuntu/KORStockScan/deploy/install_low_price_two_leg_systemd.sh)
  - 판정 기준: review gate가 닫힌 소스를 main에 반영한 뒤 별도 운영 승인으로 installer를 실행하고, 35개 profile의 preflight/live timer 70개가 enabled 상태인지, exact-date applied policy와 authority artifact가 2026-08-24 generation을 선택하는지, 기존 HELD/주문 custody가 보존되는지 확인한다. 설치·기동 전까지 이번 소스 변경은 runtime effect가 없다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-08-20` postclose -> `2026-08-21`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0821] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-08-21`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-20.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0821] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-08-21`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-08-20.json), [code_improvement_workorder_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-20.json), [threshold_apply_2026-08-21.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-21.json), [threshold_runtime_env_2026-08-21.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-21.json), [threshold_runtime_env_verify_2026-08-21.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-08-21.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`5`, forced_scout_with_post_sell_count=`12`, post_sell_join_coverage_pct=`2.643172`, outcome_coverage_state=`partial`, profitable_forced_scout_count=`11`, loss_or_flat_forced_scout_count=`1`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0821] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-08-21`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-20.json)
  - 전일 postclose candidate_selected_families=entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0821] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-08-21`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-20.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0821] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-08-21`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-21.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-21.jsonl), [threshold_events_2026-08-21.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-21.jsonl), [observation_source_quality_audit_2026-08-21.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-21.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-08-21 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0821] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-08-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-08-21.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-21.json), [threshold_cycle_ev_2026-08-21.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-21.json), [code_improvement_workorder_2026-08-21.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-21.json), [threshold_cycle_postclose_verification_2026-08-21.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-21.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0821] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-08-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-08-20.json), [threshold_cycle_ev_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-20.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0821] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-08-21`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-20.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0821] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-08-21`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-08-20.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-08-20.md), [code_improvement_workorder_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-20.json)
  - 판정 기준: selected_order_count=61와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0821] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-08-21`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-20.json), [runtime_apply_gap_audit_2026-08-20.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-20.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`293`, rollup_required_count=`293`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 292}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[MachineLifecycleTurnoverObjectiveFollowup0821] 위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인` (`Due: 2026-08-21`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_policy_approval_postclose_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_2026-08-20.json), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 판정 기준: 승인 후보 수와 무관하게 `followup_required=true`인 미완료 목적 항목 `machine_lifecycle_turnover_policy_research_v1`(status=`EVIDENCE_ACCUMULATING`, next_action=`quarantine_current_source_date_and_continue_next_exact_date_collection`)의 상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.
  - 상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, `EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. `CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.
  - 권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[AutomationTriggerDecisionSummary0821] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-08-21`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-08-20.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`9`, skip_count=`0`, source_missing_count=`4`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:8, disabled_by_runtime_policy:5, upstream_drift_signal:5, source_missing_or_unreadable:4, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->





## 사용자 지시 구현

- [x] `[LogCleanupGenerationAndIncidentFingerprint0821] 숫자 slot generation 압축·writer defer 누적·중복 incident 경보 보완` (`Due: 2026-08-21`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~22:20`, `Track: RuntimeStability`)
  - Source: [run_logs_rotation_cleanup_cron.sh](/home/ubuntu/KORStockScan/deploy/run_logs_rotation_cleanup_cron.sh), [notify_error_detection_admin.py](/home/ubuntu/KORStockScan/src/engine/notify_error_detection_admin.py), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정: 숫자 slot을 영속 archive identity로 사용하던 계약과 일시 writer-active defer의 즉시 cleanup 실패, 동일 활성 incident의 반복 Telegram 발송을 분리 보완했다.
  - 구현: `name.log.N`은 숫자 slot을 제거한 content-hash generation gzip으로 검증하고, writer-active는 로그 계열 identity별 `deferred_writer_active` 상태를 원자 누적한다. 기본 3회 연속 defer만 cleanup failure로 승격하며 stable pass가 누적을 초기화한다. detector는 정규화 fingerprint별 활성 set을 보존하여 신규 incident만 알리고 정상 report 뒤 재발은 다시 알린다.
  - 권한 경계: 운영 cleanup/notification 계약만 변경했으며 trading runtime, 주문, threshold, provider, bot process에는 영향이 없다. 실제 cleanup wrapper 실행과 bot 재기동은 수행하지 않는다.

- [x] `[PostSellExecutableBboRetention0821] 매도 후 1·3·5·10분 exact-route executable BBO 경로 보강` (`Due: 2026-08-21`, `Slot: INTRADAY`, `TimeWindow: 09:45~10:30`, `Track: ScalpingLogic`)
  - Source: [post_sell_candidates_2026-08-21.jsonl](/home/ubuntu/KORStockScan/data/post_sell/post_sell_candidates_2026-08-21.jsonl), [sniper_post_sell_feedback.py](/home/ubuntu/KORStockScan/src/engine/sniper_post_sell_feedback.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [kiwoom-api-data-contract.md](/home/ubuntu/KORStockScan/docs/kiwoom-api-data-contract.md)
  - 판정: 기존 기본값 `POST_SELL_WS_RETAIN_MINUTES=0`으로 인해 삼성공조 매도 뒤 inactive prune이 구독을 제거해 3·5·10분 연속 executable 경로가 단절됐다. 10분 bounded retention, active 8건 cap, 15초 final grace를 적용하고 실제 매도 영수증의 canonical broker route 및 venue/session을 고정했다.
  - 구현: 기존 구독을 새 owner 없이 유지하며 1·3·5·10분마다 실제 subscribed 상태와 same-symbol/session exact-route fresh 0D BBO를 함께 검증한다. horizon의 15초 관측창 안에서 유효한 bid return과 continuity count/gap을 source-only event로 남기고 unsubscribe/stale/late-arrival/route-session/BBO 결손은 explicit missing으로 닫는다. official Kiwoom reference는 `2026-08-21T10:01:17+09:00`, upstream `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`의 `실시간시세.md`, realtime packets/client, Postman을 확인했다.
  - 권한 경계: 현재 PID에는 미반영이며 봇 재기동은 수행하지 않았다. 이 observer는 REG/REMOVE나 broker 주문·취소를 호출하지 않고 `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`를 유지한다. 현재는 자연표본 검증용 producer-only 계측이며 exact-route join·표본 acceptance가 닫히기 전에는 tuning 소비자가 없다. threshold/provider/bot/cap/quantity/entry·exit authority 및 stale·broker·hard-safety guard는 변경하지 않는다.
  - 운영 반영 (`2026-08-21 10:35~10:36 KST`): review gate와 commit `b5b6c4d6`을 닫은 뒤 `restart.flag` 표준 경로로 PID `472633 -> 527953`을 교체했다. 새 PID는 `KORSTOCKSCAN_RUNTIME_GIT_COMMIT=b5b6c4d680d5bb54d8ff88f5f40065943a591406`, `KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY=false`, 당일 runtime env를 로드했고 handoff verify와 health-only detector가 pass였다. 계좌/DB 대사 일치, Kiwoom WS 로그인·첫 실시간 수신, OpenAI main route 활성도 확인했다. 실제 post-sell horizon 효과 판정은 `PostSellExecutableBboNaturalValidation0824` 자연 매도 표본에만 귀속한다.

- [ ] `[PostSellExecutableBboNaturalValidation0824] 재기동 후 자연 매도 exact-route BBO 연속성 확인` (`Due: 2026-08-24`, `Slot: INTRADAY`, `TimeWindow: 09:00~15:20`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-08-24.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-24.jsonl), [post_sell_candidates_2026-08-24.jsonl](/home/ubuntu/KORStockScan/data/post_sell/post_sell_candidates_2026-08-24.jsonl), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: 다음 정상 기동 이후 첫 confirmed real sell에서 observer가 등록되고, 1·3·5·10분 각 horizon이 `fresh_executable_bbo_observed` 또는 명시적 결손 상태로 정확히 한 번씩 종료되는지 확인한다. fresh 표본은 실제 subscription present, sell route/venue/session 일치, quote age 1초 이하를 모두 충족해야 한다.
  - 금지: 자연 표본 전 기존 8월 21일 mark-price/minute-candle 결과를 executable BBO로 재분류하거나, source-only receipt를 실주문·exit/threshold/provider/bot/cap/quantity 또는 safety guard 변경 근거로 사용하지 않는다.

- [x] `[MicroPremarketIntegratedBBOProvenanceRepair0821] PREMARKET_KRX_LIKE micro executable BBO route-depth 귀속 보완` (`Due: 2026-08-21`, `Slot: INTRADAY`, `TimeWindow: 08:30~09:20`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-08-21.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-21.jsonl), [market_depth_stream.jsonl](/home/ubuntu/KORStockScan/data/observations/scalp_micro_reversion_forward/trade_date=2026-08-21/venue=SOR/session=SOR_PREMARKET/market_depth_stream.jsonl), [kiwoom_websocket.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정: 장중 risky-micro 14건의 분류는 `excluded_excessive_risk=8`, `source_quality_blocked=4`, `recheck_required=1`, `excluded_uneconomic_spread=1`로 정상 작동했다. BBO 34건의 `exact_0d_route_snapshot_missing`은 0D 수집 누락이 아니라 `_AL|krx_nxt_integrated` snapshot이 route별 depth provenance를 runtime snapshot에 보존하지 않아 안전한 venue 확정을 못 한 producer-consumer 결손이었다. 실제 08:07 에스투더블유 0D 187행은 모두 `KRX ask/bid=0`, `NXT ask/bid>0`, `combined=NXT`를 만족했다.
  - 구현: 0D route snapshot에 같은 raw callback의 `route_depth_totals`와 호가시각을 보존한다. PREMARKET cohort는 exact `_NX|nxt_only` 또는 exact `_AL|krx_nxt_integrated`이면서 공식 0D 총잔량 FID로 `KRX=0`, `NXT>0`, `combined=NXT`가 증명된 경우만 executable BBO로 인정한다. proof가 없거나 KRX 잔량이 양수이면 `integrated_0d_route_depth_proof_missing_or_invalid`로 fail-closed하며 `_AL` 자체를 NXT로 추측하지 않는다.
  - 공식 reference gate: `2026-08-21T08:49:37+09:00`, upstream `Kiwoom-Securities/Kiwoom-REST-API` main `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`; `kiwoom_docs/실시간시세.md`, `kiwoom/realtime/packets.py`, `kiwoom/core/ws_client.py`를 확인했다. 공식 0D 계약의 KRX 총잔량 `6064/6065`, NXT 총잔량 `6086/6087`, KRX/NXT/SOR item suffix 계약을 사용한다.
  - 권한 경계: source-only BBO 계측과 반사실 입력 provenance만 보완한다. runtime/order/threshold/provider/bot/cap/수량/entry·exit authority 및 stale·broker·hard-safety guard는 변경하지 않으며 8월 21일 기존 missing event를 소급해 양성 표본으로 바꾸지 않는다.

- [ ] `[MicroPremarketIntegratedBBONaturalValidation0824] route-depth proof 적용 후 PREMARKET 자연 BBO·passive-fill 귀속 확인` (`Due: 2026-08-24`, `Slot: INTRADAY`, `TimeWindow: 08:00~08:20`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-08-24.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-24.jsonl), [rising_missed_intraday_feedback_2026-08-24.json](/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-08-24.json), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: 다음 정상 bot 시작 이후 PREMARKET risky-micro observer에서 `exact_0d_integrated_route_nxt_only_depth_proven`과 fresh BBO가 생성되고, 동일 symbol/cohort의 passive-fill 반사실이 3/10/20/30초 horizon으로 연결되는지 확인한다. proof 누락·KRX/NXT 혼합 depth는 계속 fail-closed여야 한다.
  - 금지: 자연 검증 전에 8월 21일 missing event를 재분류하거나, integrated BBO를 real execution quality·실주문·threshold/provider/bot/cap/수량 변경 근거로 사용하지 않는다.

- [x] `[PostcloseProducerConsumerConsistencyRepair0821] 장후 생산자·소비자 논리 모순 우선 보완 및 재리뷰` (`Due: 2026-08-21`, `Slot: POSTCLOSE`, `TimeWindow: 00:00~01:30`, `Track: RuntimeStability`)
  - Source: [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [entry_split_order_plan.py](/home/ubuntu/KORStockScan/src/engine/scalping/entry_split_order_plan.py), [lifecycle_bucket_discovery.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_bucket_discovery.py), [artifact_freshness.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/artifact_freshness.py), [run_logs_rotation_cleanup_cron.sh](/home/ubuntu/KORStockScan/deploy/run_logs_rotation_cleanup_cron.sh)
  - 판정: same-date rising-missed prior가 최초 scalp sim catalog보다 늦게 생성되던 순서를 prior 직후 deterministic refresh로 닫고, lifecycle direct/entry-only/flow sim 승인과 전체 policy 승인 합계를 분리했다. entry split의 기존 `runtime_apply_allowed`는 구조 exploration seed와 EV 검증 variant의 호환 합집합으로만 유지하고, 단일 authority 계약을 daily/EV/PREOPEN/runtime loader가 함께 검증해 구조 seed를 양의 EV 승인으로 오인하지 않도록 했다.
  - 운영 결함: 기본 OFF `codebase_performance_workorder_report`를 detector가 disabled parent로 인식하며, 숫자 로그 archive의 canonical gzip 충돌은 기존 gzip·원본을 덮어쓰거나 삭제하지 않고 source hash 기반 generation gzip을 검증·재사용한다.
  - 리뷰/검증: producer-only 수정 뒤 daily/EV 소비자의 의미 누수와 세 군데 중복 authority 검증을 발견해 단일 owner로 통합했다. 재리뷰에서 명시 authority boolean/class 타입을 consumer별로 다르게 해석할 수 있는 결함을 추가로 fail-closed하고 declared/effective 권한을 분리했다. 관련 report/runtime/wrapper/detector/log 회귀 `834 passed`, Ruff, Black, compile, Bash syntax, checklist parser, `git diff --check` 통과 후 최종 finding 0으로 닫는다.
  - 권한 경계: source/report/provenance·자동화 순서·보존 로직만 보완했다. 실주문, threshold, requested quantity, provider, bot, cap, broker/account/order/cooldown/stale/hard-safety guard 변경이나 재기동·비용 큰 장후 리포트 재생성은 수행하지 않았다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
