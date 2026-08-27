# 2026-08-27 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-08-26` postclose -> `2026-08-27`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0827] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-08-27`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-26.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0827] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-08-27`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-08-26.json), [code_improvement_workorder_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-26.json), [threshold_apply_2026-08-27.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-27.json), [threshold_runtime_env_2026-08-27.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-27.json), [threshold_runtime_env_verify_2026-08-27.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-08-27.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`1`, forced_scout_with_post_sell_count=`0`, post_sell_join_coverage_pct=`0`, outcome_coverage_state=`no_closed_outcome`, profitable_forced_scout_count=`0`, loss_or_flat_forced_scout_count=`0`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0827] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-08-27`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-26.json)
  - 전일 postclose candidate_selected_families=entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, post_probe_winner_recovery, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0827] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-08-27`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-26.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [x] `[IntradaySourceQualityGateCheck0827] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-08-27`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-27.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-27.jsonl), [threshold_events_2026-08-27.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-27.jsonl), [observation_source_quality_audit_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-27.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-08-27 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.
  - 2026-08-27 16:25 재감사: `status=pass`, event=`177427`, stage=`176`, warning stage=`0`, hard blocking gap=`0`, current-scan hard-blocking excluded row=`0`, unknown token stage=`0`, review warning=`0`, `raw_row_exclusion_applied=true`, `tuning_input_allowed=true`로 `defective_rows_excluded` 처리 후 장중 gate를 닫았다. 기존 제외 9행은 5개 invalid `minute_candle_window_fresh_contract`와 4개 missing `ai_score_source`이며 재발 행은 없었다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0827] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-08-27`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-27.json), [threshold_cycle_ev_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-27.json), [code_improvement_workorder_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-27.json), [threshold_cycle_postclose_verification_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-27.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.
  - 16:25 interim gate는 `defective_rows_excluded_and_ev_allowed`다. 다만 20:10 postclose EV·verification consumer가 아직 생성 전이므로 이 항목은 소비 전후 재검증이 끝날 때까지 OPEN으로 유지한다.

- [ ] `[ThresholdDailyEVReport0827] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-08-27`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-08-26.json), [threshold_cycle_ev_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-26.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0827] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-08-27`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-26.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.
  - 17:00 interim: 당일 `human_intervention_summary`, `threshold_cycle_ev`, `threshold_cycle_postclose_verification`, `code_improvement_workorder`는 모두 미생성이고 오류탐지 일정 계약상 20:10 postclose 이전 `not_yet_due`다. 전일 산출물을 당일 개입사항으로 승격하지 않고 20:10 체인 이후 OPEN 항목으로 재확인한다.

- [ ] `[MainAIQualitySourceGapRuntimeExecutionReceiptCustodyRepair0827] RuntimeExecutionReceiptCustodyRepair main lifecycle source gap 복구 확인` (`Due: 2026-08-27`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-08-26.json)
  - 판정 기준: workorder `main-ai-gap-69986ae0fd7026148b2bcc66`의 owner=`RuntimeExecutionReceiptCustodyRepair`, reason_codes=`real_submitted_lifecycle_count=1, broker_execution_unique_count=0, execution_report_materialized_companion_binding_mismatch_count=1, lifecycle_exact_join_missing_count=7`를 source-only producer 보완으로 닫는다. 공식 raw execution envelope의 order/execution identity를 합성 없이 검증하고 결손 lifecycle만 제외한 뒤 paired producer를 재검증한다.
  - 완료 조건: official raw execution envelope/order/execution identity가 최소 1개 reconciled lifecycle에서 완전하고, materialized execution companion이 exact target/path/hash에 결속되며, carry-in final exit는 전량 broker receipt coverage와 non-promotion blocker를 함께 보존한다. 해당 자연 표본의 postclose R0→R3 재검증에서 `broker_execution_unique_count>0`, lifecycle exact join 및 companion binding이 닫혀야 한다.
  - 구현 상태: prior-day `holding_started_at|buy_time`이 확인된 main-owner carry-in만 pipeline-attested custody로 분리하고 entry fill은 합성하지 않도록 보완했다. exact exit receipt 전량 coverage가 있을 때만 `CUSTODY_CARRY_FINAL_EXIT_RECONCILED`를 허용하고 R2/R3 promotion은 항상 차단한다. Provider floor는 2026-08-25 audit generation과 bridge v1.5 source-contract가 유효한 2026-08-26 이후 표본을 분리했다. 구현·targeted review는 완료됐지만 기존 immutable 2026-08-26 산출물은 재작성하지 않았으므로 이 항목은 2026-08-27 자연 표본 acceptance까지 OPEN이다.
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[CodeImprovementWorkorderReview0827] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-08-27`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-08-26.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-08-26.md), [code_improvement_workorder_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-26.json)
  - 판정 기준: selected_order_count=58와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0827] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-08-27`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-26.json), [runtime_apply_gap_audit_2026-08-26.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-26.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`430`, rollup_required_count=`430`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 429}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[MachineLifecycleTurnoverObjectiveFollowup0827] 위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인` (`Due: 2026-08-27`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_policy_approval_postclose_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_2026-08-26.json), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 판정 기준: 승인 후보 수와 무관하게 `followup_required=true`인 미완료 목적 항목 `machine_lifecycle_turnover_policy_research_v1`(status=`EVIDENCE_ACCUMULATING`, next_action=`continue_exact_date_collection_and_rolling_readiness_review`)의 상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.
  - 상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, `EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. `CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.
  - 권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.

- [x] `[WidgetEpisodeMicroCollectionCoverage0827] active 위젯·에피소드 전 종목 micro-entry 수집 대상 보장` (`Due: 2026-08-27`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:45`, `Track: ScalpingLogic`)
  - Source: [collection_targets.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/collection_targets.py), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 완료 판정: active widget/episode 고유 symbol은 일 4종목 prospective research budget을 우회해 전량 선택하고 `active_owner_candidate_count == selected_active_owner_count`, `active_owner_overflow_count=0`을 exact-date v2 artifact와 loader가 검증한다. prospective 종목만 active 선택 후 남는 research budget에서 회전한다.
  - 권한 경계: 이 변경은 0B/0D source-only market-data 수집 대상만 넓힌다. BUY/SELL, target, stop, quantity, cooldown, daily cap, provider/bot, broker guard와 실주문 권한은 변경하지 않는다.

- [x] `[WidgetEpisodeMicroEntryTiming0827] 위젯·에피소드 진입시점 bounded 튜닝·runtime recheck 연결` (`Due: 2026-08-27`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:50`, `Track: ScalpingLogic`)
  - Source: [machine_entry_timing_tuning.py](/home/ubuntu/KORStockScan/src/engine/automation/machine_entry_timing_tuning.py), [machine_entry_timing_policy.py](/home/ubuntu/KORStockScan/src/trading/config/machine_entry_timing_policy.py), [regular_two_leg_machine.py](/home/ubuntu/KORStockScan/src/trading/order/regular_two_leg_machine.py), [engine.py](/home/ubuntu/KORStockScan/src/trading/widget_auto_trade/engine.py), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 완료 판정: clean baseline의 exact owner·scope·symbol·session·entry-state별 실제 판단시각, 1/3/5초 executable ask·depth·0B/0D와 completed owner outcome을 결속한다. 당일 completed holdout을 포함한 5 observed dates·20 unique lifecycle·20 completed outcome·BBO 95%·depth 90%·delayed-entry feasibility 90%·completed paired coverage 95%·right-censored 20% 이하, 완전한 5/10/20-day positive/improved EV, 0.005%p uplift와 p10 guard를 통과한 전체 동일 entry stage 중 최대 한 scope만 다음 exact-date `entry_confirmation_delay_sec`에 반영하고, 미달이면 `0초` baseline을 유지한다.
  - runtime 판정: 위젯·episode owner는 1/3/5초 확인 만료 시 같은 원천 signal/session/route와 기존 entry guard를 다시 검증하고, 신호 소멸·변경 또는 recheck window 만료 시 주문 없이 pending confirmation을 폐기한다. 6초 steady poll인 저가주 서비스도 pending deadline에는 짧게 깨워 실제 선택시각을 재평가한다. episode의 legacy 완성봉 timestamp는 timing evidence에서 제외하고 신규 `signal_decision_at`만 사용하며 삼성전자 morning/morning-reentry/midday/afternoon도 동일 attribution에 포함한다.
  - 권한 경계: 수량·주문방식·가격·target·stop·holding/exit·provider/bot/cap·broker/hard safety와 owner별 state/order/custody는 변경하거나 공유하지 않는다.
  - 리뷰/검증: review-fix 루프에서 원천 report의 `broker_order_forbidden`·clean-baseline 명시 검증 누락, malformed next-date 위젯 정책의 동일-stage 충돌 우회, 6초 poll의 1초 지연 무효화, scope 자체의 당일 holdout 누락, 실제 목표 체결을 입증할 수 없는 불리한 에피소드 delayed fill 포함, KRX 호가단위 경계에서 위젯 비율 target·에피소드 tick target을 비실행 가격으로 계산하던 문제, 소수 표본 수·100% 초과 evidence rate 허용, runtime loader의 source-ready·동일-stage·exact report path 방어 공백을 보완했다. 관련 producer/runtime/attribution/wrapper/verifier/location-gate 회귀 `599 passed`, Black/Ruff/compile, shell syntax, checklist parser와 `git diff --check`를 통과했고 최종 미해결 finding은 `0`이다. 2026-08-26 read-only 재생은 신규 실제 판단시각 표본이 없어 `winner=null`, `baseline_immediate_entry_carry_forward`로 정상 rollback됐다.

- [x] `[WidgetEpisodePostcloseRecommendationImplementation0827] 위젯·에피소드 장후 추천 사용자 승인 구현` (`Due: 2026-08-27`, `Slot: POSTCLOSE`, `TimeWindow: 22:15~22:50`, `Track: ScalpingLogic`)
  - Source: [widget_collector_expansion_recommendation_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/widget_collector_expansion_recommendation/widget_collector_expansion_recommendation_2026-08-27.json), [widget_research_watch_symbols.json](/home/ubuntu/KORStockScan/data/config/widget_research_watch_symbols.json), [low_price_two_leg_expanded_candidate_research_2026-08-27.json](/home/ubuntu/KORStockScan/data/report/low_price_two_leg_expanded_candidate_research/low_price_two_leg_expanded_candidate_research_2026-08-27.json), [low_price_two_leg_expanded_profile_evidence_2026-08-27.json](/home/ubuntu/KORStockScan/data/config/low_price_two_leg_expanded_profile_evidence_2026-08-27.json)
  - 구현 판정: 위젯은 `implementation_review_candidate_count=0`이므로 실매매 policy를 만들지 않고 기존 11종목 누적 관찰에 `361610`, `488280`만 exact report SHA로 추가해 13종목 source-only collector로 유지했다. 에피소드는 사용자 승인된 9개 행을 2026-08-28 exact-date 세대로 분리해 기존 profile 8개를 갱신하고 `sk_telecom_morning`을 추가했다.
  - 계약: 2026-08-27까지 45-profile 세대는 불변이며 2026-08-28부터 46-profile 세대만 선택한다. 수량은 10주+10주, 무손절·시간청산 없음, owner/custody 분리, target·route·broker/hard-safety 경계를 추천 증거대로 유지한다. 위젯 research watch는 `runtime_effect=false`, `allowed_runtime_apply=false`, `broker_order_forbidden=true`다.
  - 리뷰/검증: 1차 review에서 신규 profile operational-date 누락과 test import/format 결함을 보완했다. 관련 위젯·에피소드·microstructure·timing 회귀 `500 passed`, exact-date applied-policy 45→46 전환, 9개 evidence/preflight, 13개 위젯 lineage, Ruff/Black/compile, shell/systemd 구문을 재검증했고 최종 미해결 finding은 `0`이다.

- [ ] `[WidgetEpisodePostcloseRecommendationPreopen0828] 승인 추천 service 설치·exact-date 자연기동 수용검증` (`Due: 2026-08-28`, `Slot: PREOPEN`, `TimeWindow: 08:40~09:15`, `Track: ScalpingLogic`)
  - Source: [install_low_price_two_leg_systemd.sh](/home/ubuntu/KORStockScan/deploy/install_low_price_two_leg_systemd.sh), [korstockscan-low-price-two-leg-sk-telecom-morning-preflight.timer](/home/ubuntu/KORStockScan/deploy/systemd/korstockscan-low-price-two-leg-sk-telecom-morning-preflight.timer), [widget_research_watch_symbols.json](/home/ubuntu/KORStockScan/data/config/widget_research_watch_symbols.json)
  - acceptance: 별도 service 설치 지시 후에만 46개 episode timer 설치를 수행한다. 09:05 SK텔레콤 morning preflight와 09:09 live timer가 각 1회 등록되고, 2026-08-28 applied policy가 46개 profile·9개 revision·정확한 evidence hash로 검증되며, 08:58 위젯 research collector가 13개 lineage를 읽는지 확인한다.
  - custody 경계: 설치 전후 main/widget/episode/manual owner의 잔고·미체결을 대사하고 기존 HELD/target 주문을 취소·재제출·흡수하지 않는다. 설치·daemon-reload 자체를 신규 주문 권한이나 정상 체결 증거로 간주하지 않는다.

- [ ] `[WidgetEpisodeMicroCollectionRuntime0828] active owner 전 종목 exact-date v2 manifest·runtime 반영 검증` (`Due: 2026-08-28`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:55`, `Track: ScalpingLogic`)
  - Source: [scalp_micro_reversion_collection_targets_2026-08-27.json](/home/ubuntu/KORStockScan/data/runtime/scalp_micro_reversion_collection_targets/scalp_micro_reversion_collection_targets_2026-08-27.json), [latest.json](/home/ubuntu/KORStockScan/data/runtime/scalp_micro_reversion_forward_collector/latest.json), [collection_targets.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/collection_targets.py)
  - 2026-08-27 16:03 판정: 현재 PID source에는 v2 전 종목 보장 구현이 반영됐지만, 당일 exact-date manifest는 전일 21:35 생성된 v1·4종목 budget artifact라 active episode owner `015760`이 overflow에 남았고 live observer series에도 없다. 따라서 오늘 KEPCO microstructure는 `source_quality + runtime_hook` blocker이며 실주문 runtime 효과와 분리한다.
  - acceptance: 2026-08-28 exact-date v2 manifest에서 `active_owner_candidate_count == selected_active_owner_count`, `active_owner_overflow_count=0`, `015760` 포함을 확인하고, 신규 PID/collector registration receipt와 live 0B·0D series·callback/drop/error를 같은 effective-date provenance로 결속한다.
  - 권한 경계: 현재 장중 manifest 재생성·수동 REG·프로세스 재기동·실주문/취소·target/quantity/provider/broker guard 변경을 수행하지 않는다.

- [ ] `[AutomationTriggerDecisionSummary0827] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-08-27`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-08-26.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-08-26.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`9`, skip_count=`0`, source_missing_count=`4`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:8, disabled_by_runtime_policy:5, upstream_drift_signal:5, source_missing_or_unreadable:4, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 결함 해소 후속 체크리스트

- [ ] `[EntrySetupOneShareAllocatorPreopen0827] V2.14 1주 exploration의 메인 매수·중앙배분 비훼손 수용검증` (`Due: 2026-08-27`, `Slot: PREOPEN`, `TimeWindow: 07:35~15:30`, `Track: ScalpingLogic`)
  - Source: [entry_setup_v2_14_bounded_live_candidate_2026-08-26.json](/home/ubuntu/KORStockScan/data/threshold_cycle/bounded_live_candidates/entry_setup_v2_14_bounded_live_candidate_2026-08-26.json), [entry_setup_live_policy.py](/home/ubuntu/KORStockScan/src/engine/scalping/entry_setup_live_policy.py), [ai_quality_bridge.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/ai_quality_bridge.py), [threshold_runtime_env_2026-08-27.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-27.json)
  - 판정 기준: 07:35 PREOPEN activation이 source/effective date·candidate/file/prompt contract hash·probe-first active date·1주·일 3회 durable cap을 정확히 검증하고, KRX regular 해당 V2.14 cohort 외 normal entry와 `position_sizing_dynamic_formula`를 변경하지 않아야 한다. terminal 1주는 `allocator_provenance_partial_submission_observation_only`로만 귀속하고 notional EV·중앙배분 승격 표본에서 제외한다.
  - 장중 확인: V2.14 eligible/decision/probe-intent/submit 수, 일 cap block, 일반 V2.13/normal submit 수와 오늘의 submit drought를 분리한다. V2.14가 일반 메인 BUY를 대체하거나 partial 표본이 full allocator 표본에 유입되면 fail-closed로 판정한다.
  - 2026-08-27 재리뷰 판정: 현재 source producer/activation/loader는 candidate·activation v2 schema를 일관되게 생성·검증하고 targeted test를 통과했다. 당일 생성된 v1 candidate·activation은 현재 PID 이전 산출물이라 현 loader가 `fallback_activation_contract_invalid`로 V2.13에 fail-closed했으며, v2 exact-date PREOPEN 산출물과 신규 PID 자연 호출 전에는 V2.14 반영으로 판정하지 않는다.
  - 권한 경계: 이 항목은 자연 표본 acceptance이며 PREOPEN env, prompt selection, requested quantity/cap, provider, bot, broker/order/hard-safety를 수동 변경하는 권한이 아니다. 계약 결손은 V2.13 자동 fallback으로 닫고 전략적 비활성·완화는 사용자 지시 후 별도 판정한다.

- [ ] `[WidgetEpisodeExactDatePreopen0827] 위젯·저가주 에피소드 exact-date 기동·custody 수용검증` (`Due: 2026-08-27`, `Slot: PREOPEN`, `TimeWindow: 08:55~14:30`, `Track: ScalpingLogic`)
  - Source: [widget_symbol_runtime_policy_2026-08-27.json](/home/ubuntu/KORStockScan/data/runtime/widget_symbol_runtime_policy/widget_symbol_runtime_policy_2026-08-27.json), [low_price_two_leg_expanded_profile_evidence_2026-08-26.json](/home/ubuntu/KORStockScan/data/config/low_price_two_leg_expanded_profile_evidence_2026-08-26.json), [run_low_price_two_leg_preflight.sh](/home/ubuntu/KORStockScan/deploy/run_low_price_two_leg_preflight.sh)
  - 판정 기준: 장기 실행 위젯 서비스가 날짜 전환 후 verified `080220` policy를 dynamic spec으로 편입하고, 저가주 최초 preflight가 2026-08-27 applied policy 45개·profile revision 12건·evidence hash를 재검증해야 한다. 신규 profile 5개의 preflight/live timer는 정확 시각에 1회만 시작하고 owner 중복주문은 0건이어야 한다.
  - custody 경계: `kepco_afternoon` 2026-08-26 state의 20주·target order 2건은 기존 owner로 대사한다. 미해결·보유가 남아 있으면 해당 profile의 신규 진입을 정상 차단하고 취소·재제출·다른 owner 수량 흡수를 하지 않는다. terminal 영수증 후에만 다음 exact-date attempt를 연다.
  - 2026-08-27 장중 대사: 15:56 KST broker 잔고는 `015760` 20주, 미체결은 SOR 매도정정 `0027998` 20주(`orig_ord_no=0022612`, 34,700원)로 contract-complete였으나 episode state는 전일 target `0047674`·`0047785`를 계속 소유한다. 당일 주문참조에는 `0001934` 20주 원주문 뒤 `0022612`·`0027998` 정정 chain이 확인되지만 전일 두 leg와 `0001934`의 cross-date 전환 근거가 owner artifact에 없으므로 `post_apply_attribution + user_authority`로 열어 둔다.
  - acceptance: broker receipt/order-reference 또는 operator record가 전일 두 target에서 당일 `0001934`로의 custody 전환을 exact하게 입증해 episode ledger에 귀속되거나, 당일 정정 chain을 `manual_operator`로 명시해 episode와 분리해야 한다. 어느 경우든 체결 시 realized PnL·비용·terminal 수량을 단일 owner에 반영하고, 그 전에는 기존 service가 신규 진입·취소·재제출·다른 owner 수량 흡수를 하지 않는지 확인한다.
  - 권한 경계: 이 항목은 자연 기동·broker reconciliation 확인이며 main/widget/episode process 수동 재기동, 실주문·취소, target/quantity/provider/broker guard 변경 권한이 아니다.

- [ ] `[HoldingFlowProviderRouteAuthority0828] holding_flow Provider route Plan/PID 정합성 승인·수용검증` (`Due: 2026-08-28`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:50`, `Track: RuntimeStability`)
  - Source: [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 현재 판정: Plan은 `holding_flow=Bedrock Nova Lite v2 primary -> OpenAI failback`을 소유하지만 launcher/current PID는 `OpenAI primary -> Bedrock Nova Lite v2 fallback`을 사용했고 자연 호출도 OpenAI로 관측됐다. 중앙 router와 양방향 failback 테스트는 정상이라 code transport 결함이 아니라 `env_mapping + user_authority` blocker다.
  - acceptance: 사용자가 Provider route 변경을 별도 승인한 경우에만 launcher before/after·rollback을 기록하고 우아한 재기동 뒤 새 PID env, Bedrock primary provider audit row, OpenAI failback smoke, holding 결과 provenance를 확인한다. 승인 전에는 현재 route와 프로세스를 변경하지 않는다.

- [ ] `[WidgetSorCrossVenueReconcileRuntime0828] 위젯 SOR→NXT 실제 venue 미체결 reconciliation 런타임 수용검증` (`Due: 2026-08-28`, `Slot: PREOPEN`, `TimeWindow: 08:50~09:00`, `Track: ScalpingLogic`)
  - Source: [gateway.py](/home/ubuntu/KORStockScan/src/trading/widget_auto_trade/gateway.py), [engine.py](/home/ubuntu/KORStockScan/src/trading/widget_auto_trade/engine.py), [widget_signal_auto_trade_state.json](/home/ubuntu/KORStockScan/data/runtime/widget_signal_auto_trade_state.json)
  - 2026-08-27 19:30 판정: 삼성전자 위젯 target 20주는 18:17에 기존 KRX/SOR 주문 `0052539`가 terminal 처리된 뒤 동일 가격 268,500원·동일 수량의 신규 주문 `0064588`로 승계됐다. broker `ka10075`는 신규 주문을 NXT 미체결 20주로 반환했지만 현재 service는 `kt00007 dmst_stex_tp=SOR`로 조회해 `reconcile_not_found_count=75`를 누적했다. broker 활성 매도는 종목별 1건으로 중복주문은 아니다.
  - 구현: official `Kiwoom-Securities/Kiwoom-REST-API@e1b32486a2d4c055d78e62d78711133f1458401e`의 `kt00007 dmst_stex_tp=%` 전체 venue 조회 계약을 재확인했다. SOR 주문만 `%`로 read-only 조회하되 exact 주문번호+종목을 유지하고, 동일 identity·정정 descendant가 복수 actual venue에 나타나거나 venue 필드가 invalid/conflict이면 fail-closed하며, venue-only 변경도 event journal에 기록하도록 보완했다. `broker_execution_venue`는 signal venue와 분리해 attribution consumer까지 전달하고 cross-venue lifecycle은 fill/exit anchor를 actual venue로 분리한 뒤 policy tuning에서 제외한다. 제출·취소·가격·수량·owner 권한은 변경하지 않았다.
  - acceptance: 이 주문이 terminal이 되거나 owner별 broker 재대사 후 안전한 신규 process 반영이 허용된 시점에 새 PID/service commit을 확인한다. 그 뒤 exact 주문이 `found=true`, `remaining_qty=20`, `broker_execution_venue=NXT`로 대사되고 `reconcile_not_found_count`가 더 이상 증가하지 않으며, 중복 매도·취소·reprice 0건을 확인한다.
  - 권한 경계: 현재 20주 활성 미체결을 취소·재제출하거나 위젯 service/main bot을 장중 재기동하지 않는다. 이 항목은 `runtime_hook + safety_or_broker_guard`로 열어 두고 현재 프로세스 반영을 실주문 승격 근거로 사용하지 않는다.

- [ ] `[PostcloseWriterOwnedLogRotationContract0828] 21:00 active writer log rotation 장기 반복 blocker 계약 해소` (`Due: 2026-08-28`, `Slot: POSTCLOSE`, `TimeWindow: 20:50~21:10`, `Track: RuntimeStability`)
  - Source: [run_logs_rotation_cleanup_cron.sh](/home/ubuntu/KORStockScan/deploy/run_logs_rotation_cleanup_cron.sh), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [log_rotation_cleanup_cron.log](/home/ubuntu/KORStockScan/logs/log_rotation_cleanup_cron.log), [log_rotation_cleanup_writer_defer_state.json](/home/ubuntu/KORStockScan/tmp/log_rotation_cleanup_writer_defer_state.json)
  - 2026-08-27 판정: 21:00 wrapper는 21:03:49 `[FAIL]`로 종료했고 7개 writer defer가 연속 5회로 escalation 되었다. `active_rotation_status=disabled_pending_writer_owner`라서 active log 6개와 quiet하지 않은 archive 1개를 fail-closed 보존했으며 원본 손상·강제 unlink·불완전 gzip 건수는 0건이다. 이 상태는 최근 10일 창에서 3회 이상 반복된 `repeat_unresolved_structural_blocker`다.
  - 다음 보완: 각 active log의 실제 single writer owner와 reopen/rollover 계약을 registry에 고정하고, writer가 close·rename·reopen 또는 동등한 atomic handoff를 소유하게 한다. cleanup은 owner receipt가 있는 closed generation만 no-clobber gzip/roundtrip 검증하고 active file을 직접 rename·delete하지 않는다.
  - acceptance: 대상 writer 전체가 owner·PID/cgroup·generation·close/reopen receipt를 남기고, 동시 write 중 rotate 0건, loss/duplicate byte 0건, gzip roundtrip/hash pass, `writer_defer_escalated=0`, `writer_defer_state_failures=0`, wrapper latest `[DONE]`을 같은 target date에서 확인한다.
  - 권한 경계: writer owner·atomic rollover 계약이 닫히기 전에 활성 log를 강제 rotate·truncate·delete하지 않고, 이 storage 보완을 bot/provider/order/threshold/safety 변경 근거로 사용하지 않는다.

## 2026-08-27 장후 튜닝결과 점검 기록

- 최종 상태: `YELLOW`. EOD와 main postclose wrapper는 대상일 `[DONE]`, final verifier는 허용 warning 1건(`limit_down_watch_ordered_path_not_observed`), DONE controller는 `status=done`으로 닫혔다. tuning monitoring, 20:10 widget evaluation, 재시도 후 21:15 machine final refresh, paired replay, 20:50 archive와 21:55 detector도 terminal이다.
- source quality: `tuning_input_allowed=true`, event 283,384건·stage 177개, hard-blocking contract gap 0건·unknown-token stage 0개다. invalid scalp-entry action snapshot 3건은 `raw_row_exclusion`으로 격리했고 수익 0 또는 정상 row로 보간하지 않았다.
- 계산·lineage: main lifecycle 1,754건을 보존하면서 invalid transition은 3,212건에서 63건, pipeline lifecycle instrumentation gap은 1건에서 0건으로 줄었다. exact broker-order fill과 broad bundle label의 충돌은 exact receipt를 우선하도록 보완했고 scanner recheck는 submit 이전만 허용했다. 남은 exact venue/custody 결손은 sample/evidence blocker로 유지한다.
- AI·micro: 대상일 AI correction과 paired replay provider는 `openai`이고 parsed/schema/receipt 계약을 확인했으며 `provider=none`은 없었다. R0→R3 재생성은 ask-depletion Provider ablation 표본 floor 미달로 `source_only_candidate_blocked_current_run`에 fail-closed했고 Provider 추가 호출이나 runtime/order authority를 만들지 않았다.
- workorder 2-pass: 최종 `generation_id=2026-08-27-7da7ef4efe38`, `source_hash=7da7ef4efe386033deb624ba58121bbd6ea649f731be52b5185b2a8ad894ccdf`가 두 pass에서 안정됐고 selected 49건은 모두 `attach_existing_family`, `implement_now=0`, `runtime_effect=true=0`, new/removed/decision-changed order 0건이다. 기존 family attribution 46건과 visibility/non-implement 3건을 분리 유지했고 신규 implement 항목은 없으며 review-required 및 sample·handoff 항목만 보류했다.
- process·보관: 예상 process는 terminal 또는 근거 있는 custody/active 상태로 분류했다. 21:00 log rotation은 active writer 7건의 연속 defer 5회로 `[FAIL]`했지만 원본 7건을 보존했고 손상·강제 unlink·불완전 gzip은 0건이다. 이 반복 구조 결함은 `PostcloseWriterOwnedLogRotationContract0828`로 이월했다.
- runtime 경계: 위젯 NXT 미체결 20주와 `kepco_afternoon` HELD 20주가 남아 owner/broker reconciliation 없이 service·bot을 재기동하지 않았다. 실주문·취소·reprice·수량·provider route·threshold·hard safety 변경도 수행하지 않았다.



## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
