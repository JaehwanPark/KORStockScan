# 2026-08-20 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-08-19` postclose -> `2026-08-20`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0820] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-08-20`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-19.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0820] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-08-20`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-08-19.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-08-19.json), [code_improvement_workorder_2026-08-19.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-19.json), [threshold_apply_2026-08-20.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-20.json), [threshold_runtime_env_2026-08-20.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-20.json), [threshold_runtime_env_verify_2026-08-20.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-08-20.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`3`, forced_scout_with_post_sell_count=`5`, post_sell_join_coverage_pct=`1.404494`, outcome_coverage_state=`partial`, profitable_forced_scout_count=`4`, loss_or_flat_forced_scout_count=`1`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0820] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-08-20`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-19.json)
  - 전일 postclose candidate_selected_families=entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0820] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-08-20`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-08-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-19.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0820] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-08-20`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-20.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-20.jsonl), [threshold_events_2026-08-20.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-20.jsonl), [observation_source_quality_audit_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-20.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-08-20 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[MainAIQualityCollectorContinuity0820] 8월 19일 observer 조기종료 보완의 당일 자연수집 및 R0→R3 원인분류 확인` (`Due: 2026-08-20`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~20:35`, `Track: ScalpingLogic`)
  - Source: [latest.json](/home/ubuntu/KORStockScan/data/runtime/scalp_micro_reversion_forward_collector/latest.json), [ai_quality_cycle.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/ai_quality_cycle.py), [main_ai_quality_r0_r3_cycle_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-08-20.json), [micro_reversion_ai_quality_bridge_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/micro_reversion_ai_quality_bridge/micro_reversion_ai_quality_bridge_2026-08-20.json), [main_scalping_lifecycle_paired_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/main_scalping_lifecycle_paired/main_scalping_lifecycle_paired_2026-08-20.json)
  - 판정 기준: canary가 장마감까지 `stop_required=false`를 유지하고 queue loss가 없으면 Bridge의 `past_market_row_missing`이 전일 870건처럼 전면화되지 않으며 clean micro eligible row가 남아야 한다. Queue loss가 있으면 collector는 계속 수집하되 exact scoped exclusion receipt가 없으므로 해당 날짜 Provider replay는 fail closed해야 한다. Eligible=0이면 cycle의 `observer_canary`, `source_gap_diagnostics`, `source_only_gap_workorders`가 collector continuity, integrated-route proof, broker execution provenance를 별도 owner/reason으로 기록해야 한다.
  - 금지: queue-loss row를 정상 row로 보간하거나 다른 clean lifecycle을 전역 제외하지 않는다. 이 보완과 source-only workorder로 runtime prompt, provider, threshold, 주문, 수량/cap, bot, broker/hard-safety 권한을 열지 않는다.
  - 다음 액션: `collector_continuous_clean_rows_eligible`, `queue_loss_collector_continued_provider_replay_held`, `collector_or_route_proof_repair_still_open`, `broker_execution_provenance_repair_still_open`, `cycle_artifact_missing_or_invalid` 중 하나로 닫는다.

- [ ] `[MainLifecycleBrokerRawProvenance0821] 공식 type 00 raw FID lifecycle provenance 자연행 검증` (`Due: 2026-08-21`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~20:35`, `Track: ScalpingLogic`)
  - Source: [kiwoom_websocket.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py), [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py), [main_scalping_lifecycle_paired_2026-08-21.json](/home/ubuntu/KORStockScan/data/report/main_scalping_lifecycle_paired/main_scalping_lifecycle_paired_2026-08-21.json), [main_ai_quality_r0_r3_cycle_2026-08-21.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-08-21.json)
  - 판정 기준: 다음 정상 bot load 이후 발생한 BUY/ADD/SELL execution row가 공식 WebSocket type `00` raw-envelope marker와 native FID `9203/9001/913/900/902/903/905/907/908/909/910/911/914/915/2134/2135/2136`를 lifecycle pipeline에 손실 없이 보존해야 한다. 완전한 raw execution은 `broker_execution_provenance_state=complete`와 exact order/execution identity를 가져야 하며 불완전 row는 해당 row만 explicit exclusion되어야 한다. 2026-08-20 변경 load 전 과거 row를 보간하거나 complete로 재분류하지 않는다.
  - 금지: raw provenance를 custody, 주문, 수량, provider, threshold, bot, broker/hard-safety 권한으로 사용하지 않는다. type `00` marker가 없는 name-only fallback이나 이전 receipt FID를 현재 receipt에 혼합하지 않는다.
  - 다음 액션: `natural_raw_provenance_complete`, `natural_rows_absent_recheck_next_postclose`, `raw_provenance_row_excluded_with_reason`, `runtime_not_loaded`, `cycle_artifact_missing_or_invalid` 중 하나로 닫는다.

- [ ] `[PostcloseSourceQualityGateReview0820] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-08-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-20.json), [threshold_cycle_ev_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-20.json), [code_improvement_workorder_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-20.json), [threshold_cycle_postclose_verification_2026-08-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-20.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0820] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-08-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-08-19.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-08-19.json), [threshold_cycle_ev_2026-08-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-19.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0820] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-08-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-19.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0820] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-08-20`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-08-19.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-08-19.md), [code_improvement_workorder_2026-08-19.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-19.json)
  - 판정 기준: selected_order_count=68와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0820] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-08-20`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-08-19.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-19.json), [runtime_apply_gap_audit_2026-08-19.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-19.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`249`, rollup_required_count=`249`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 248}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[MachineLifecycleTurnoverObjectiveFollowup0820] 위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인` (`Due: 2026-08-20`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_policy_approval_postclose_2026-08-19.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_2026-08-19.json), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 판정 기준: 승인 후보 수와 무관하게 `followup_required=true`인 미완료 목적 항목 `machine_lifecycle_turnover_policy_research_v1`(status=`EVIDENCE_ACCUMULATING`, next_action=`repair_current_attribution_source_contract_and_rerun`)의 상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.
  - 상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, `EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. `CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.
  - 권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[AutomationTriggerDecisionSummary0820] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-08-20`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-08-19.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-08-19.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`9`, skip_count=`0`, source_missing_count=`4`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:8, disabled_by_runtime_policy:5, upstream_drift_signal:5, source_missing_or_unreadable:4, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 사용자 지시 구현

- [x] `[EpisodeExactCostReconciliation0820] SK텔레콤 episode 실현손익 비용 귀속 보완 및 코드리뷰` (`Due: 2026-08-20`, `Slot: INTRADAY`, `TimeWindow: 14:45~16:10`, `Track: ScalpingLogic`)
  - Source: [low_price_two_leg_tuning.py](/home/ubuntu/KORStockScan/src/engine/monitoring/low_price_two_leg_tuning.py), [low-price-two-leg-machines.md](/home/ubuntu/KORStockScan/docs/low-price-two-leg-machines.md), [test_low_price_two_leg.py](/home/ubuntu/KORStockScan/src/tests/test_low_price_two_leg.py)
  - 판정: SK텔레콤 017670의 96,600원 4주 매수·96,800원 4주 매도는 `ka10073` 기준 수수료 100원·세금 773원·실현손익 -73원이다. 장후 producer는 단일 episode owner와 symbol-day 수량·평균가격·gross-cost 정합성이 모두 일치할 때만 exact PnL을 사용하고 그 외에는 0.23% 비용 추정으로 fail-safe한다.
  - 리뷰/검증: 1차 리뷰에서 report v4 candidate consumer 누락, 2차 리뷰에서 ineligible 동일-symbol owner 모호성 및 microstructure 후행 consumer의 v3-only 계약을 찾아 보완했다. 에피소드·microstructure·postclose verifier 회귀 `286 passed`, checklist parser 회귀 `91 passed`, Ruff, compile, `git diff --check`를 통과했으며 최종 미해결 finding은 0이다.
  - 권한 경계: POSTCLOSE 보고서·후보 EV의 비용 인식만 보완했으며 주문, target tick, 수량, 보유/손절, provider, bot, cap, broker guard는 변경하지 않았다.

- [x] `[LowPriceRecommendationImplementation0819] 2026-08-19 장후 추천 11프로필 구현 및 리뷰` (`Due: 2026-08-20`, `Slot: INTRADAY`, `TimeWindow: 13:15~15:20`, `Track: ScalpingLogic`)
  - Source: [low_price_two_leg_expanded_candidate_research_2026-08-19.json](/home/ubuntu/KORStockScan/data/report/low_price_two_leg_expanded_candidate_research/low_price_two_leg_expanded_candidate_research_2026-08-19.json), [low_price_two_leg_expanded_profile_evidence_2026-08-19.json](/home/ubuntu/KORStockScan/data/config/low_price_two_leg_expanded_profile_evidence_2026-08-19.json), [profiles.py](/home/ubuntu/KORStockScan/src/trading/low_price_two_leg/profiles.py)
  - 판정: 기존 8프로필 로직개선과 신규 3프로필을 2026-08-21 exact-date 세대로 결속하고, 2026-08-20 세대와 prior-date custody를 유지했다. 더본코리아는 source-only에서 승격하지 않았다.
  - 리뷰: 첫 pass에서 8월 20일 장후 tuning producer가 latest 23-profile inventory를 조기 소비할 수 있는 결함을 발견해 target-date profile/baseline/bounds로 보완했다. 오늘 report/candidate는 20개, 8월 21일부터 23개로 검증된다.
  - 권한 경계: service 설치·enable/start와 실주문은 수행하지 않았다. 본 후속 리뷰에서 관련 파일만 별도 브랜치에 커밋·푸시한다.

- [ ] `[LowPriceRecommendationActivation0821] 신규 3프로필 timer 설치 및 23-profile PREOPEN 적용 검증` (`Due: 2026-08-21`, `Slot: PREOPEN`, `TimeWindow: 08:45~09:05`, `Track: RuntimeStability`)
  - Source: [install_low_price_two_leg_systemd.sh](/home/ubuntu/KORStockScan/deploy/install_low_price_two_leg_systemd.sh), [low_price_two_leg_policy_apply.py](/home/ubuntu/KORStockScan/src/engine/automation/low_price_two_leg_policy_apply.py), [low-price-two-leg-machines.md](/home/ubuntu/KORStockScan/docs/low-price-two-leg-machines.md)
  - 판정 기준: 별도 사용자 지시 후 reviewed installer를 실행하고, exact-date applied artifact가 23프로필·추천 11개 transition hash를 가지며 신규 timer 6개가 enable 상태인지 확인한다.
  - 금지: 오늘 장중 timer 재설치, 기존 profile service 재기동, prior-date 주문 취소·교체, 수량/stop/provider/bot/broker guard 변경을 하지 않는다.
  - 다음 액션: `installed_and_preopen_verified`, `implementation_only_not_installed`, `exact_date_policy_blocked`, `timer_or_owner_marker_missing` 중 하나로 닫는다.




## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
