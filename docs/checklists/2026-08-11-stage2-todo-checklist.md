# 2026-08-11 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-08-10` postclose -> `2026-08-11`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0811] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-08-11`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-10.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0811] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-08-11`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-08-10.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-08-10.json), [code_improvement_workorder_2026-08-10.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-10.json), [threshold_apply_2026-08-11.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-11.json), [threshold_runtime_env_2026-08-11.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-11.json), [threshold_runtime_env_verify_2026-08-11.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-08-11.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`1`, forced_scout_with_post_sell_count=`0`, post_sell_join_coverage_pct=`0`, outcome_coverage_state=`no_closed_outcome`, profitable_forced_scout_count=`0`, loss_or_flat_forced_scout_count=`0`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0811] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-08-11`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-10.json)
  - 전일 postclose candidate_selected_families=entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0811] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-08-11`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-08-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-10.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0811] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-08-11`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-11.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-11.jsonl), [threshold_events_2026-08-11.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-11.jsonl), [observation_source_quality_audit_2026-08-11.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-11.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-08-11 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0811] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-08-11`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-08-11.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-11.json), [threshold_cycle_ev_2026-08-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-11.json), [code_improvement_workorder_2026-08-11.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-11.json), [threshold_cycle_postclose_verification_2026-08-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-11.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0811] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-08-11`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-08-10.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-08-10.json), [threshold_cycle_ev_2026-08-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-10.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0811] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-08-11`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-10.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0811] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-08-11`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-08-10.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-08-10.md), [code_improvement_workorder_2026-08-10.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-10.json)
  - 판정 기준: selected_order_count=66와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0811] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-08-11`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-08-10.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-10.json), [runtime_apply_gap_audit_2026-08-10.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-10.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`340`, rollup_required_count=`340`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'positive_source_only_keep_collecting': 340}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0811] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-08-11`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-08-10.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-08-10.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`15`, run_count=`15`, skip_count=`0`, source_missing_count=`4`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`upstream_drift_signal:10, output_missing_or_unreadable:6, upstream_artifact_newer:6, source_missing_or_unreadable:4`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 구현 보완 (`2026-08-11`): trigger decision이 wrapper enable flag를 받아 OFF step을 `disabled_success`로 분리하고 force가 OFF를 재활성화하지 않도록 했다. 동일 날짜 `failed` 복구 실행은 target/report/status 계약이 유효한 opening-rotation·avg-down recovery·one-share 완료 artifact만 재사용하며, verbosity는 완료된 common-minute watermark와 미완료 tail을 분리한다. 실제 당일 postclose 재생성 전이므로 이 항목은 새 summary/marker 대조가 끝날 때까지 OPEN을 유지한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

- [ ] `[EntrySetupV214PredecessorRecovery0811] Entry Setup V2.14 predecessor 복구 대기 결함 보완 및 재확인` (`Due: 2026-08-11`, `Slot: POSTCLOSE`, `TimeWindow: 21:05~22:05`, `Track: ScalpingLogic`)
  - Source: [entry_setup_paired_replay_batch.py](/home/ubuntu/KORStockScan/src/engine/scalping/entry_setup_paired_replay_batch.py), [run_ai_entry_setup_paired_replay_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_ai_entry_setup_paired_replay_postclose.sh), [threshold_cycle_postclose_2026-08-11.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_2026-08-11.status.json)
  - 판정 기준: 현재 구현은 predecessor의 일시적 `failed|error|blocked` 상태에서 최대 4시간 대기 계약과 달리 즉시 종료한다. 상태 전환을 복구 가능하게 처리하는 최소 보완과 회귀 테스트를 별도 승인 범위에서 닫은 뒤, 21:05 runner가 최대 4시간 안의 `succeeded` 전환을 기다리는지 확인한다. 이후 replay batch와 activation artifact를 분리해 `succeeded`, `blocked_predecessor_timeout`, `blocked_promotion_guard`, `inactive_fallback_v2_13` 중 실제 상태를 기록한다.
  - 금지: predecessor 복구 대기 통과만으로 V2.14를 live activation으로 간주하거나 promotion/source-quality/누적 EV/risk guard를 우회하지 않는다.
  - 다음 액션: `recovered_then_evaluated`, `predecessor_timeout`, `promotion_guard_blocked`, `activated_and_preopen_pending`, `runner_failed_needs_fix` 중 하나로 닫는다.

- [x] `[SmoothingRollingDecisionConsumerImplementation0811] exact-path rolling 의사결정 consumer 구현·리뷰` (`Due: 2026-08-11`, `Slot: PREOPEN`, `TimeWindow: 08:20~09:10`, `Track: TuningAutomation`)
  - Source: [daily/rolling report](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [postclose verifier](/home/ubuntu/KORStockScan/src/engine/verify_threshold_cycle_postclose_chain.py), [traceability](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 완료 결과 (`2026-08-11`): `smoothing_source_only_rolling_decision_v1` consumer가 soft-stop 10건·OFI 20건 floor, rolling 5/10/20일 90초 source-quality-adjusted EV, downside p10, guarded-terminal 비율/EV, phase/exclusion을 함께 판정한다. 표본·EV·downside 근거가 모두 완성되고 세 window가 양수일 때만 `source_only_bounded_review_ready`를 내며, 이 상태도 단일 same-stage bounded-canary 설계 검토만 열고 runtime/PREOPEN 권한은 갖지 않는다. verifier는 ready/hold 상태 drift와 권한·metric contract 결손을 fail로 닫는다.
  - 리뷰/검증: 1차 리뷰에서 downside evidence 미완성 통과, 보수적 오분류 미검출, metric contract 누락, R1/R2 traceability 귀속 오류를 보완했다. 최종 리뷰에서 verifier의 metric contract 누락과 downside readiness 플래그 신뢰를 독립 재계산으로 보완했다. 재리뷰 미해결 finding=`0`; daily/verifier pytest=`294 passed`, smoothing runtime/source-quality integration pytest=`216 passed`, checklist parser pytest=`60 passed`, Ruff/Black/compileall/`git diff --check`=`pass`다. Bot/PID/runtime env와 실주문 상태는 변경하지 않았다.

- [ ] `[SmoothingRollingDecisionConsumer0812] exact-path rolling 의사결정 consumer 최초 검증` (`Due: 2026-08-12`, `Slot: POSTCLOSE`, `TimeWindow: 21:00~21:20`, `Track: TuningAutomation`)
  - Source: [daily/rolling report](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [postclose verifier](/home/ubuntu/KORStockScan/src/engine/verify_threshold_cycle_postclose_chain.py), [threshold_cycle_cumulative_2026-08-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_2026-08-11.json)
  - 판정 기준: `smoothing_source_only_path_journal_v3`와 `smoothing_source_only_rolling_decision_v1`이 soft-stop 10건·OFI 20건 floor, rolling 5/10/20일 90초 source-quality-adjusted EV, downside p10, guarded-terminal 비율/EV, holding/revive/non-revive phase와 exclusion을 함께 보존하는지 확인한다. 세 rolling window가 모두 양수이면 `source_only_bounded_review_ready`, 일부만 양수이면 `hold_direction_conflict`, 전부 비양수이면 `hold_no_edge`, 표본 미달이면 `hold_sample`로 닫는다.
  - 금지: source-only decision을 standalone live promotion, PREOPEN env mutation, hard/protect/emergency 우회, provider/bot/cap/quantity 변경 근거로 사용하지 않는다. `source_only_bounded_review_ready`는 동일 holding/exit stage 단일 bounded-canary 설계 검토만 열 수 있다.
  - 다음 액션: `source_quality_blocked`, `hold_sample`, `hold_outcome`, `hold_direction_conflict`, `hold_no_edge`, `source_only_bounded_review_ready` 중 하나로 닫는다.

- [x] `[SamsungMorningOneShareMachineImplementation0811] 삼성전자 오전 1주 독립 상태기계와 추가 1개월 분석 구현·리뷰` (`Due: 2026-08-11`, `Slot: INTRADAY`, `TimeWindow: 09:30~11:30`, `Track: ScalpingLogic`)
  - Source: [samsung-morning-one-share-machine.md](/home/ubuntu/KORStockScan/docs/samsung-morning-one-share-machine.md), [machine.py](/home/ubuntu/KORStockScan/src/trading/samsung_morning_one_share/machine.py), [gateway.py](/home/ubuntu/KORStockScan/src/trading/samsung_morning_one_share/gateway.py), [test_samsung_morning_one_share.py](/home/ubuntu/KORStockScan/src/tests/test_samsung_morning_one_share.py)
  - 완료 결과 (`2026-08-11`, 후속 정정 반영): 기존 entry/holding/exit/ADM/LDM/AI/수량결정과 분리한 `005930` 1주 전용 NXT PREMARKET-first/SOR-regular-fallback 상태기계를 추가했다. 2026-05-06~08-10 공통 완전일 64일 중 고정 정책 진입 49일·+2호가 12분 내 관측 도달 49일이며, clean baseline 44일은 진입 35·도달 35, archive-only 추가월 20일은 진입 14·도달 14다. 12분은 과거 도달시간 진단값일 뿐 runtime 청산 제한이 아니며, pre-baseline은 archive/audit로만 유지한다.
  - 안전/권한: 기본 OFF, env+CLI 확인문구+production endpoint+명시적 manual-operator exclusion+당일 PREOPEN authority가 모두 있어야 broker write가 가능하다. 전일 전용기계 미해결 주문/보유, 수량·응답 계약 이상, write 중단·모호 응답은 fail-closed다. 모든 주문은 1주로 하드코딩했다. widget 자동매매와 전용기계는 서로의 주문을 차단하거나 청산하지 않고 각자 broker 주문번호·체결수량만 소유한다.
  - 리뷰/검증: write-ahead 중복주문 방지, 독립 전략 장부 경계, 라이브 `--once`/임의 state 경로 금지, 당일 authority gate를 보완했다. 전용 pytest=`23 passed`, 수동제외·기존 widget 회귀 포함 pytest=`79 passed`, checklist parser pytest=`58 passed`, Ruff/Black/compile/systemd/shell/`git diff --check`=`pass`다. 최종 재리뷰 미해결 finding=`0`이다.

- [x] `[SamsungMorningOneShareNoStopSorCorrection0811] 오전 1주 기계 무손절 보유·SOR 정규장 라우트 정정` (`Due: 2026-08-11`, `Slot: INTRADAY`, `TimeWindow: 11:40~12:20`, `Track: ScalpingLogic`)
  - Source: [samsung-morning-one-share-machine.md](/home/ubuntu/KORStockScan/docs/samsung-morning-one-share-machine.md), [policy.py](/home/ubuntu/KORStockScan/src/trading/samsung_morning_one_share/policy.py), [machine.py](/home/ubuntu/KORStockScan/src/trading/samsung_morning_one_share/machine.py), [gateway.py](/home/ubuntu/KORStockScan/src/trading/samsung_morning_one_share/gateway.py), [preflight.py](/home/ubuntu/KORStockScan/src/trading/samsung_morning_one_share/preflight.py)
  - 완료 결과 (`2026-08-11`): 사용자 정정에 따라 08:00 구간만 NXT PREMARKET으로 유지하고 09:00 정규장 fallback 주문은 `SOR`로 변경했다. 목표가 +2호가 주문은 시간 제한 없이 유지하며 브로커가 미체결 종료로 확정한 경우 `HELD`로 닫아 1주를 보유한다. 12분 목표 취소, 최우선 지정가 강제매도, 다음 날 자동 목표 재주문, 보유 중 신규매수 경로는 제거·금지했다.
  - 권한/참조: PREOPEN authority schema를 `v2`로 올리고 SOR 정규장·무시간청산 정책을 필수 검증한다. 키움 공식 `Kiwoom-Securities/Kiwoom-REST-API` commit `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`의 `주문.md`, `계좌.md`, `차트.md`, API spec, Postman에서 `kt10000/kt10001/kt10003/kt00007`의 SOR 계약을 2026-08-11 11:43:54 KST에 재확인했다.
  - 리뷰/검증: 1차 리뷰에서 authority v2가 SOR·무시간청산 policy payload를 직접 검증하지 않던 누락을 보완했고, 2차 리뷰에서 전용 gateway의 KRX 직접 라우트 우회 가능성을 제거했다. 전용 pytest=`30 passed`, manual-exclusion/widget 독립성/live trade 회귀 포함 pytest=`122 passed`, checklist/Project·Calendar parser pytest=`84 passed`, checklist print-backlog parser, Ruff/Black/compileall/`git diff --check`=`pass`다. 최종 재리뷰 미해결 finding=`0`이며 Bot/PID/runtime env와 실주문 상태는 변경하지 않았다.

- [ ] `[SamsungMorningOneShareLiveStart0812] 삼성전자 오전 2-leg 독립 기계 최초 실운용·귀속 확인` (`Due: 2026-08-12`, `Slot: PREOPEN`, `TimeWindow: 07:55~09:35`, `Track: ScalpingLogic`)
  - Source: [samsung-morning-one-share-machine.md](/home/ubuntu/KORStockScan/docs/samsung-morning-one-share-machine.md), [preflight.py](/home/ubuntu/KORStockScan/src/trading/samsung_morning_one_share/preflight.py), [service.py](/home/ubuntu/KORStockScan/src/trading/samsung_morning_one_share/service.py)
  - 판정 기준: 새 unit 설치 뒤 07:57 PREOPEN authority v3가 당일 메인 봇·공유토큰·manual-operator exclusion, leg당 1주·총 2주 50:50, `SOR` 정규장 fallback, 무시간청산·미청산 보유 정책을 PASS하고 07:59 전용 서비스가 시작되는지 확인한다. 기존 widget과 전용기계가 모두 독립 활성 상태이며, NXT/SOR 각 leg가 자기 주문번호·체결수량만 취소·매도하는지 최초 episode attribution으로 확인한다. NXT는 base/base+1호가, SOR fallback도 미체결 leg별 base/base+1호가, 각 체결가 +2호가 목표 유지와 `HELD` 종결을 검증한다.
  - 금지: 코드 변경만으로 기존 unit을 재기동하거나 active legacy 1주 상태를 자동 변환하지 않는다. 목표가 미체결을 이유로 목표 주문을 시간 취소하거나 최우선 지정가로 강제매도하지 않는다. 한 전략의 삼성전자 총보유수량·주문을 다른 전략의 장부로 간주하거나 상대 주문을 취소·청산하지 않는다. widget 중지·삼성 제외·재기동, 총 2주·leg당 1주 상한 완화, threshold/provider/cap/hard-safety 변경을 열지 않는다.
  - 다음 액션: `parallel_independent_episode_pass`, `target_open_continues`, `target_closed_unfilled_position_held`, `no_entry_condition`, `opening_source_missing`, `preflight_authority_blocked`, `independent_ledger_breach_disable_one_share_only`, `state_or_lock_failure` 중 하나로 닫는다.

- [x] `[SamsungAfternoonOneShareMachineImplementation0811] 삼성전자 오후 SOR 1주 독립 기계 구현·리뷰` (`Due: 2026-08-11`, `Slot: INTRADAY`, `TimeWindow: 12:20~14:50`, `Track: ScalpingLogic`)
  - Source: [samsung-afternoon-one-share-machine.md](/home/ubuntu/KORStockScan/docs/samsung-afternoon-one-share-machine.md), [policy.py](/home/ubuntu/KORStockScan/src/trading/samsung_afternoon_one_share/policy.py), [machine.py](/home/ubuntu/KORStockScan/src/trading/samsung_afternoon_one_share/machine.py), [gateway.py](/home/ubuntu/KORStockScan/src/trading/samsung_afternoon_one_share/gateway.py), [preflight.py](/home/ubuntu/KORStockScan/src/trading/samsung_afternoon_one_share/preflight.py)
  - 완료 결과 (`2026-08-11`): 정규장 `005930_AL` SOR 완성 1분봉의 14:00~14:40 최신 봉만 평가하고, 최근 연속 30봉 고점 대비 -1.25% 이하·저점 대비 +0.20% 이내이면 신호 종가 -1호가에 1주를 하루 1회 주문한다. 신호 뒤 5개 완성봉 동안 미체결인 매수 주문만 자기 주문번호로 취소하며, 체결 뒤 실제 체결가 +2호가 목표 매도는 시간 취소·손절·강제청산 없이 유지하고 브로커 미체결 종료 시 `HELD`로 보유한다.
  - 독립성/권한: 오전·widget과 상태·lock·당일 authority·정확 주문번호 원장을 분리했고 계좌 총보유량을 매도 수량으로 사용하지 않는다. 기본 OFF이며 env+CLI 확인문구+production endpoint+manual-operator exclusion+당일 authority가 모두 있어야 broker write가 가능하다. 키움 공식 upstream commit `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`의 차트·주문·계좌 계약을 12:04:45 KST에 확인했다.
  - 리뷰/검증: PREOPEN 메인 봇 실측 래퍼, 30봉 연속성, 상태 불변식, authority 전필드 검증, pagination fail-closed를 보완했다. 최초 배포 smoke에서 preflight `PrivateTmp`가 기존 tmux 소켓을 격리하는 결함을 확인해 preflight unit에서만 제거하고 live service 격리는 유지했다. 오후 전용 pytest=`33 passed`, 오전 회귀 포함 pytest=`63 passed`, manual-exclusion/widget 독립성 회귀 포함 pytest=`136 passed`, checklist parser pytest=`58 passed`, Ruff/Black/compile/systemd/shell/`git diff --check`=`pass`다. 최종 재리뷰 미해결 finding=`0`이며 결함 발견 시점에는 authority·live service·실주문이 열리지 않았다.

- [ ] `[SamsungAfternoonOneShareLiveStart0811] 삼성전자 오후 2-leg 독립 기계 재설치 후 최초 실운용·귀속 확인` (`Due: 2026-08-12`, `Slot: INTRADAY`, `TimeWindow: 13:50~15:20`, `Track: ScalpingLogic`)
  - Source: [samsung-afternoon-one-share-machine.md](/home/ubuntu/KORStockScan/docs/samsung-afternoon-one-share-machine.md), [preflight.py](/home/ubuntu/KORStockScan/src/trading/samsung_afternoon_one_share/preflight.py), [service.py](/home/ubuntu/KORStockScan/src/trading/samsung_afternoon_one_share/service.py)
  - 기동 상태 (`2026-08-11 12:29 KST`): PR `#33/#34` main 병합 후 오후 전용 systemd unit을 설치·enable했다. 당일 authority=`ready`, service PID=`223895`, state=`READY`, attempt_consumed=`false`, position_qty=`0`, buy/target order number=`empty`, last_action=`waiting_for_afternoon_scan_window`다. 14:00~14:40 최초 episode attribution은 계속 OPEN이다.
  - 판정 기준: 새 unit 설치 뒤 13:57 authority v2가 메인 봇·공유토큰·manual-operator exclusion, SOR 통합 정규장, 신호종가 1주+신호종가-1호가 1주, 5개 완성봉 유효기간, leg별 +2호가 무손절 보유 정책을 PASS하고 13:59 서비스가 시작되는지 확인한다. 오전·midday·widget·오후가 각자 주문번호와 체결수량만 소유하는지 최초 episode attribution으로 확인한다.
  - 금지: 코드 변경만으로 기존 unit을 재기동하거나 active legacy 1주 상태를 자동 변환하지 않는다. 오후 정규장을 KRX/NXT 별도 시장으로 분리하거나 목표 매도를 시간 취소·최우선 지정가 강제매도·손절하지 않는다. 다른 기계 주문 또는 계좌 총보유량을 오후 장부로 간주하지 않으며 총 2주·leg당 1주 상한·hard safety·provider·bot·cap을 변경하지 않는다.
  - 다음 액션: `parallel_independent_episode_pass`, `target_open_continues`, `target_closed_unfilled_position_held`, `no_signal`, `source_stale_or_gap`, `preflight_authority_blocked`, `independent_ledger_breach_disable_afternoon_only`, `state_or_lock_failure` 중 하나로 닫는다.

- [x] `[SamsungMiddayOneShareMachineImplementation0811] 삼성전자 13:15~13:55 SOR 1주 독립 기계 구현·리뷰` (`Due: 2026-08-11`, `Slot: INTRADAY`, `TimeWindow: 12:40~14:10`, `Track: ScalpingLogic`)
  - Source: [samsung-midday-one-share-machine.md](/home/ubuntu/KORStockScan/docs/samsung-midday-one-share-machine.md), [policy.py](/home/ubuntu/KORStockScan/src/trading/samsung_midday_one_share/policy.py), [machine.py](/home/ubuntu/KORStockScan/src/trading/samsung_midday_one_share/machine.py), [gateway.py](/home/ubuntu/KORStockScan/src/trading/samsung_midday_one_share/gateway.py), [preflight.py](/home/ubuntu/KORStockScan/src/trading/samsung_midday_one_share/preflight.py)
  - 완료 결과 (`2026-08-11`): clean baseline 46거래일 탐색에서 선택한 반개구간 `[13:15, 13:55)`를 runtime 13:15~13:54 완성봉으로 고정했다. 최근 연속 30봉 고점 대비 -1.25% 이하·저점 대비 +0.20% 이내이면 신호 종가 -1호가에 SOR 1주를 하루 1회 주문한다. 신호 뒤 5개 완성봉 동안 미체결인 자기 매수 주문만 취소하고, 체결 뒤 실제 체결가 +2호가 목표 매도는 손절·시간취소·강제청산 없이 유지하며 브로커 미체결 종료 시 `HELD`로 보유한다.
  - 독립성/권한: 오전·기존 오후·widget과 process/state/lock/당일 authority/정확 주문번호 원장을 모두 분리했고 계좌 총보유량을 청산 수량으로 사용하지 않는다. 기본 OFF이며 env+CLI 확인문구+production endpoint+manual-operator exclusion+당일 authority를 모두 통과해야 broker write가 가능하다. 키움 공식 upstream commit `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`의 차트·주문·계좌·spec/core/Postman 계약을 12:44:57 KST에 재확인했다.
  - 리뷰/검증: 1차 리뷰에서 공식 참조 경로 provenance와 기존 오후 서비스 비변경 안내 누락을 보완하고 SOR 1주 매도·정확 매수취소·연속 체결조회·수량 위반 fail-closed 테스트를 추가했다. midday 전용 pytest=`39 passed`, 오전·오후·manual-exclusion·widget 독립성 회귀 포함 pytest=`158 passed`, checklist/Project·Calendar parser pytest=`84 passed`, checklist print-backlog parser, Ruff/Black/compile/systemd/shell/`git diff --check`=`pass`다. 최종 재리뷰 미해결 finding=`0`이며 기계는 설치·enable·start하지 않았고 runtime/order 상태를 변경하지 않았다.

- [ ] `[SamsungMiddayOneShareLiveStart0811] 삼성전자 midday 2-leg 독립 기계 재설치 후 최초 실운용·귀속 확인` (`Due: 2026-08-12`, `Slot: INTRADAY`, `TimeWindow: 13:05~14:05`, `Track: ScalpingLogic`)
  - Source: [samsung-midday-one-share-machine.md](/home/ubuntu/KORStockScan/docs/samsung-midday-one-share-machine.md), [preflight.py](/home/ubuntu/KORStockScan/src/trading/samsung_midday_one_share/preflight.py), [service.py](/home/ubuntu/KORStockScan/src/trading/samsung_midday_one_share/service.py)
  - 기동 상태 (`2026-08-11 12:58 KST`): PR `#37` main 병합 후 midday 전용 systemd unit을 설치·enable했다. 당일 authority=`ready`, service PID=`252969`, restart count=`0`, state=`READY`, attempt_consumed=`false`, position_qty=`0`, buy/target order number=`empty`, last_action=`waiting_for_midday_scan_window`다. 기존 오후 PID=`223895`는 재기동 없이 유지됐고, `[13:15,13:55)` 최초 episode attribution은 계속 OPEN이다.
  - 판정 기준: 새 unit 설치 뒤 13:12 authority v2가 메인 봇·공유토큰·manual-operator exclusion, SOR 통합 정규장, `[13:15,13:55)` 신호창, 신호종가 1주+신호종가-1호가 1주, 5개 완성봉 유효기간, leg별 +2호가 무손절 보유 정책을 PASS하고 13:14 서비스가 시작되는지 확인한다. 오전·오후·widget·midday가 각자 주문번호와 체결수량만 소유하는지 state와 최초 episode attribution으로 확인한다.
  - 금지: 코드 변경만으로 기존 unit을 재기동하거나 active legacy 1주 상태를 자동 변환하지 않는다. 설치·기동을 이유로 기존 오전·오후·widget·main bot을 중지·재기동하거나, 다른 기계 주문·계좌 총보유량을 midday 장부로 간주하지 않는다. midday 자체 재기동이 필요하면 미해결 write intent·owned order·position을 먼저 확인하고 상태 파일을 보존한 채 systemd graceful stop/start만 허용한다.
  - 다음 액션: `parallel_independent_episode_pass`, `target_open_continues`, `target_closed_unfilled_position_held`, `no_signal`, `source_stale_or_gap`, `preflight_authority_blocked`, `independent_ledger_breach_disable_midday_only`, `state_or_lock_failure` 중 하나로 닫는다.

- [x] `[SamsungThreeMachineTwoLegAllocation0811] 삼성전자 오전·midday·오후 2주 50:50 분할 진입 구현·리뷰` (`Due: 2026-08-11`, `Slot: INTRADAY`, `TimeWindow: 15:20~17:30`, `Track: ScalpingLogic`)
  - Source: [shared two-leg core](/home/ubuntu/KORStockScan/src/trading/order/regular_two_leg_machine.py), [morning policy](/home/ubuntu/KORStockScan/src/trading/samsung_morning_one_share/policy.py), [midday policy](/home/ubuntu/KORStockScan/src/trading/samsung_midday_one_share/policy.py), [afternoon policy](/home/ubuntu/KORStockScan/src/trading/samsung_afternoon_one_share/policy.py), [morning document](/home/ubuntu/KORStockScan/docs/samsung-morning-one-share-machine.md), [midday document](/home/ubuntu/KORStockScan/docs/samsung-midday-one-share-machine.md), [afternoon document](/home/ubuntu/KORStockScan/docs/samsung-afternoon-one-share-machine.md)
  - 완료 결과 (`2026-08-11`): 세 기계의 하루 1회 episode를 총 2주로 바꾸되 broker 주문은 leg당 1주로 분리했다. midday·오후는 신호종가 1주와 신호종가-1호가 1주, 오전은 기존 base 1주와 base+1호가 1주를 사용하며 NXT 미체결 leg만 동일 역할의 SOR fallback으로 넘긴다. 각 체결은 실제 체결가 +2호가 목표를 독립 소유하고 손절·시간청산·강제매도 없이 미청산 보유한다. package/unit 경로는 호환성을 유지하지만 state/authority/confirmation schema는 two-leg 버전으로 올렸다.
  - 안전/리뷰: active legacy state는 자동 변환하지 않고 manual reconciliation으로 차단하며, broker write intent는 leg와 집계 상태를 함께 원자 저장한다. leg별 정확 주문번호·1주 수량·중복 주문번호 금지·집계 수량/상태 정합성을 검증한다. 1차 재리뷰에서 오전 프로세스가 08:10 이후 최초 시작되면 SOR fallback 대신 NXT leg를 `NO_FILL`로 닫을 수 있는 결함을 찾아, 08:10~09:00에는 SOR leg를 대기시키고 09:00 이후에는 SOR 시가로 직접 제출하도록 보완했다. 기존 설치 unit은 자동 재기동하지 않았고 새 confirmation 계약으로 별도 재설치 전까지 fail-closed다. 공식 키움 upstream commit `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`의 주문·계좌·spec/API/Postman 계약을 15:30:19 KST에 재확인했다.
  - 검증: 세 기계·preflight·gateway/service targeted pytest=`113 passed`, Samsung/widget/manual-exclusion 회귀 pytest=`352 passed`; Ruff/Black/compileall/systemd verify/shell syntax/checklist parser/`git diff --check`=`pass`, 최종 재리뷰 미해결 finding=`0`이다. runtime/order/provider/main bot/widget 상태는 변경하지 않았다.

- [x] `[ErrorDetectorInvocationContract0811] 에러디텍터 silent fail·stale report DONE·장중 artifact 오탐 보완` (`Due: 2026-08-11`, `Slot: INTRADAY`, `TimeWindow: 16:10~17:00`, `Track: ScalpingLogic`)
  - Source: [error_detector.py](/home/ubuntu/KORStockScan/src/engine/error_detector.py), [run_error_detection.sh](/home/ubuntu/KORStockScan/deploy/run_error_detection.sh), [artifact_freshness.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/artifact_freshness.py), [time-based operations runbook](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 완료 결과 (`2026-08-11`): detector 생성 예외와 필수 detector 미등록을 report의 FAIL result와 initialization accounting에 포함하고, 모든 report를 atomic replace로 기록한다. cron wrapper는 고유 `run_id` 임시 report의 schema/mode/date/detector 집합/runtime 권한을 검증한 뒤에만 canonical report 승격·Telegram 알림·`[DONE]`을 허용하며, 누락·이전 실행·부분 JSON은 `[FAIL]`로 닫는다. 전략 runtime mutation은 none으로 유지하면서 실제 bounded 운영 조치는 `operational_mutations`로 분리했다. 20:10 postclose wrapper가 생산하는 pattern-lab propagation artifact의 freshness window를 잘못된 16:10~17:10에서 20:10~21:40으로 정렬해 장중 반복 warning 오탐을 제거했다.
  - 권한/롤백: `runtime_effect=false`, `runtime_mutation=none`이며 threshold·주문·provider·bot 상태를 변경하지 않는다. rollback은 wrapper의 invocation validation 변경만 되돌리되 detector 생성 실패 FAIL 표면화와 atomic write는 유지한다.
  - 리뷰/검증: 에러디텍터 전체 회귀, report 계약·생성 실패·explicit invocation path·artifact window 테스트, shell syntax, compile, checklist parser, `git diff --check`를 통과한 뒤 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->



## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
