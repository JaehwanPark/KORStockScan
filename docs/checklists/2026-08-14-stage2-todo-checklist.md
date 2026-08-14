# 2026-08-14 Stage2 To-Do Checklist

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

## Smoothing exact-path 보완

- [x] `[SmoothingSimTerminalExactObserver0814] sim 즉시종료 source-only exact-path observer bridge 구현·리뷰` (`Due: 2026-08-14`, `Slot: INTRADAY`, `TimeWindow: 11:30~12:30`, `Track: ScalpingLogic`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [test_scalp_live_simulator.py](/home/ubuntu/KORStockScan/src/tests/test_scalp_live_simulator.py), [test_daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/tests/test_daily_threshold_cycle_report.py)
  - 판정 기준: `scalp_sim_sell_order_assumed_filled` 직전의 active smoothing arm을 92초 bounded detached registry에 등록하고, 동일 arm ID로 exact 10/20/40/60/90초 horizon과 등록 실패를 postclose에서 구분한다.
  - 금지: sim terminal observer는 `actual_order_submitted=false`, `broker_order_forbidden=true`, `runtime_effect=false`를 유지하고 매도·취소·threshold·provider·bot 권한을 가지지 않는다.
  - 결과: 기존 non-revive observer/WS retention을 sim terminal에 연결하고 arm ID·등록 상태를 compact threshold source contract에 추가했다.

- [ ] `[SmoothingExactPathPostcloseVerify0814] immutable snapshot 기반 smoothing exact-path postclose 정합성 확인` (`Due: 2026-08-14`, `Slot: POSTCLOSE`, `TimeWindow: 20:55~21:10`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-14.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-14.jsonl), [threshold_cycle_2026-08-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle/threshold_cycle_2026-08-14.json), [threshold_cycle_cumulative_2026-08-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_2026-08-14.json), [threshold_cycle_postclose_verification_2026-08-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-14.json)
  - 판정 기준: postclose immutable snapshot→partition→daily/cumulative→verifier의 smoothing armed/horizon/closed 수량과 `post_sell_non_revive` 등록 상태가 일치하고, exact-path 누락이 정상 표본으로 잘못 포함되지 않아야 한다.
  - 금지: 분 단위 10분 post-sell MFE/MAE를 exact 10/20/40/60/90초 경로로 대체하거나, 일일 표본만으로 runtime apply를 열지 않는다.
  - 다음 액션: `pass_exact_counts_match`, `warning_natural_no_arm`, `hold_sample`, `fail_registration_or_ingestion_gap` 중 하나로 닫고 실패 시 producer/consumer acceptance test를 남긴다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-08-13` postclose -> `2026-08-14`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0814] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-08-14`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-13.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0814] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-08-14`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-08-13.json), [code_improvement_workorder_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-13.json), [threshold_apply_2026-08-14.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-14.json), [threshold_runtime_env_2026-08-14.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-14.json), [threshold_runtime_env_verify_2026-08-14.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-08-14.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`4`, forced_scout_with_post_sell_count=`3`, post_sell_join_coverage_pct=`0.769231`, outcome_coverage_state=`partial`, profitable_forced_scout_count=`2`, loss_or_flat_forced_scout_count=`1`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0814] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-08-14`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-13.json)
  - 전일 postclose candidate_selected_families=entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0814] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-08-14`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-13.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0814] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-08-14`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-14.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-14.jsonl), [threshold_events_2026-08-14.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-14.jsonl), [observation_source_quality_audit_2026-08-14.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-14.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-08-14 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0814] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-08-14`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-08-14.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-14.json), [threshold_cycle_ev_2026-08-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-14.json), [code_improvement_workorder_2026-08-14.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-14.json), [threshold_cycle_postclose_verification_2026-08-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-14.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0814] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-08-14`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-08-13.json), [threshold_cycle_ev_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-13.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0814] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-08-14`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-13.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0814] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-08-14`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-08-13.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-08-13.md), [code_improvement_workorder_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-13.json)
  - 판정 기준: selected_order_count=48와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0814] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-08-14`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-13.json), [runtime_apply_gap_audit_2026-08-13.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-13.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`328`, rollup_required_count=`328`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 327}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0814] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-08-14`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-08-13.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`9`, skip_count=`0`, source_missing_count=`4`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:8, disabled_by_runtime_policy:5, upstream_drift_signal:5, source_missing_or_unreadable:4, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 세션 추가 후속

- [x] `[SamsungEpisodeTargetTicks3OperatorOverride0814] 삼성전자 독립 episode 신규 목표 +3호가 사용자 오버라이드 반영` (`Due: 2026-08-14`, `Slot: INTRADAY`, `TimeWindow: 09:21~13:12`, `Track: RuntimeStability`)
  - Source: [samsung_entry_policy.py](/home/ubuntu/KORStockScan/src/trading/order/samsung_entry_policy.py), [samsung-machine docs](/home/ubuntu/KORStockScan/docs/samsung-morning-one-share-machine.md), [traceability](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정: clean baseline `+3호가` 도달률 91.43%를 삼성전자에서 감당 가능한 위험으로 본 사용자 명시 지시에 따라 `morning`, `morning_reentry`, `midday`, `afternoon`의 2026-08-14 09:21:07 KST 이후 신규 목표만 `+2→+3`으로 변경한다.
  - 귀속: 정확일자 base artifact는 변조하지 않고 effective overlay hash·runtime source는 신호시각별 state에, override id·효력시각·target은 same-day authority에 고정한다. 09:21:07 이전 오전 신호와 이미 접수된 목표주문·기존 `HELD`는 취소·교체하지 않고 +2 provenance를 유지한다.
  - 경계: 수량·50:50 leg·진입·validity·무손절·미청산 보유·provider/bot/cap/broker guard는 변경하지 않았고 widget·메인 봇·삼성중공업은 대상이 아니다.
  - Rollback: 장후 broker-priced attribution 검토 후 사용자가 명시적으로 지시하면 이후 신규 목표만 +2로 복원하며 이미 접수된 목표주문은 유지한다.

- [x] `[ThebornMorningSourceOnlyObservation0814] 더본코리아 morning 고정 에피소드 후보 누적관찰 구현` (`Due: 2026-08-14`, `Slot: INTRADAY`, `TimeWindow: 10:30~13:12`, `Track: ScalpingLogic`)
  - Source: [expanded candidate research](/home/ubuntu/KORStockScan/src/engine/monitoring/low_price_two_leg_expanded_candidate_research.py), [entry-spot research](/home/ubuntu/KORStockScan/src/engine/monitoring/low_price_two_leg_entry_spot_research.py), [lower-price machine runbook](/home/ubuntu/KORStockScan/docs/low-price-two-leg-machines.md)
  - 판정: `2026-06-05~2026-08-13` integrated-SOR 49거래일의 33일 calibration/16일 untouched OOS에서 `09:40~09:59`, L20, DD0.50, NL0.35, `(0,-1)` 2-leg, 5봉 유효, `+4호가`가 calibration 7회·14leg 완료·EV `+0.067163%`, OOS 1회·2leg 완료·EV `+0.091227%`였으나 OOS `3회·4leg` floor 미달이다.
  - 구현: 동일 exact policy만 매일 clean-baseline expanding calibration/latest-16-day OOS로 재평가하는 `source_only_keep_collecting` 관찰 프로필을 장후 후보 연구 체인에 고정했다. moving-grid 재최적화는 차단하고 report/Telegram에 OOS floor 진행도를 표시한다.
  - 경계: `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`, `machine_created=false`, `service_started=false`이며 실기계·timer·PREOPEN policy·계좌/주문·provider/bot/cap/threshold/broker guard는 변경하지 않는다. 분봉 OOS floor를 충족하더라도 fresh-BBO spread·passive-fill·spread/fee 차감 EV 계약이 별도 구현·검증되기 전에는 machine recommendation 목록으로 승격하지 않는다.

- [ ] `[RiskyMicroEpisodeExecutableOutcomeJoin0814] risky rising-missed micro episode 실행가능 결과 결합 및 rolling EV 자격 확인` (`Due: 2026-08-14`, `Slot: POSTCLOSE`, `TimeWindow: 20:05~20:20`, `Track: ScalpingLogic`)
  - Source: [risky_micro_episode policy](/home/ubuntu/KORStockScan/src/engine/scalping/risky_micro_episode/policy.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py), [rising_missed_intraday_feedback.py](/home/ubuntu/KORStockScan/src/engine/monitoring/rising_missed_intraday_feedback.py), [pipeline_events_2026-08-14.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-14.jsonl)
  - 판정 기준: promotion EV에는 `source_only_candidate`와 현재 policy version의 canonical `bid_plus_one_ttl_3s` profile만 1회 포함한다. `recheck_required`는 별도 진단 cohort로 유지하고, 같은 후보의 bid+1 TTL 3/5/10초와 candidate spread 15bp 이하 제한적 ask TTL 3초를 source-only paired counterfactual로 비교한다. clean baseline 이후 rolling resolved opportunity 30건·10 symbols·3 trade dates와 fresh executable ask-touch fill 뒤 target/adverse/timeout으로 종결된 filled-terminal 10건·3 trade dates를 모두 충족한 경우에만 `source_quality_adjusted_ev_pct` review 후보를 만든다.
  - 진행: report-only adapter와 rolling gate 구현·타깃 테스트·당일 실데이터 임시 재생은 완료했다. 전체 리뷰에서 cross-venue/global watermark가 exact-path 미체결을 확정할 수 있던 결함을 제거해 동일 종목·venue·session fresh-BBO watermark만 TTL 성숙을 소유하도록 보완했다. rolling row에 candidate status·policy version·entry profile을 보존하고 tick context·quote freshness·BBO 결손을 canonical instrumentation gap으로 계측한다. 15:00 KST 재생은 1,207 observations, `source_only_candidate=48`, rolling resolved 19건·19 symbols·1 trade date, filled-terminal 0건이며 promotion은 sample floor와 positive cost-adjusted EV 미확정으로 차단됐다. 추가 리뷰에서 전역 pipeline watermark는 성숙했지만 동일 venue/session fresh-BBO가 TTL/exit horizon까지 이어지지 않은 `fill horizon 29건 + exit horizon 10건`을 별도 `matured_pending_outcome_gap`으로 표면화했다. 후속 구현은 runtime explicit `source_only_candidate/recheck_required`만 종목·venue·session별 최대 45초 WS subscription retention에 등록하고, scanner watch 이탈 뒤에도 1초 주기로 exact symbol·venue·session 0D route snapshot의 fresh executable BBO만 report-only event에 남긴다. active symbol cap 16, `runtime_effect=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`를 고정했으며 관련 타깃 테스트 27건이 통과했다. 현재 PID에는 미반영이므로 다음 허용된 재기동 뒤 자연 표본과 POSTCLOSE 정식 산출물 검증 전까지 체크는 OPEN으로 유지한다.
  - 금지: candidate count, `recheck_required`, 복수 entry profile 중복가중, mark-price MFE, daily-only win rate만으로 broker 주문, 취소, 자동매도, 수량/cap, hard safety, provider/bot 또는 PREOPEN live 승격을 열지 않는다. 3거래일 및 두 sample floor 충족 후에도 별도 PREOPEN policy·명시 승인 없이는 `real_order_promotion_allowed=false`를 유지한다. 기존 `position_sizing_dynamic_formula -> probe-first` 수량 owner와 episode/widget order ledger를 변경하거나 공유하지 않는다.
  - 다음 액션: 다음 허용된 재기동 뒤 `horizon_observer_registered_candidate_count`, observer fresh-BBO event count, 동일 venue/session 3/10/20/30초 horizon 완결률과 matured-pending gap 감소를 확인한다. 등록 실패·capacity·WS retention 거절은 결손으로 분리하고 기존 주문·slot·threshold 권한이 불변임을 acceptance test로 재확인한다. POSTCLOSE 정식 재생에서 `outcome_join_ready_positive_ev`, `outcome_join_ready_non_positive_ev`, `fill_feasibility_unresolved`, `source_quality_blocked`, `sample_floor_pending` 중 하나로 닫는다.

- [x] `[OpeningRotationRetirement0814] Opening Rotation 1주 반복매매 전체 폐기` (`Due: 2026-08-14`, `Slot: INTRADAY`, `TimeWindow: 11:40~13:30`, `Track: ScalpingLogic`)
  - Source: [Plan Rebase](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [traceability](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [opening runtime](/home/ubuntu/KORStockScan/src/engine/scalping/opening_rotation.py), [watch budget](/home/ubuntu/KORStockScan/src/engine/scalping/watch_budget.py)
  - 판정: 사용자 명시 지시에 따라 `opening_rotation_full_retirement_20260814`로 scanner owner·2-slot 보호·신규 기계식 BUY·미수 1주 예외·장후 tuning·PREOPEN policy apply/verify를 폐기한다. 과거 event/report/policy는 archive/audit evidence로만 남긴다.
  - 경계: 기존 Opening position tag의 receipt/exit 파싱은 잔존 포지션 custody 호환성으로만 유지하며 신규 진입 권한이 아니다. 현재 봇은 재기동하지 않고, 소스 반영은 다음 명시적으로 허용된 기동부터 적용한다.
  - 재개 조건: 기존 env·dated policy·candidate·과거 artifact로 재활성화하지 않는다. 향후 유사 전략은 신규 workorder·namespace·증거계약·runtime guard와 사용자 명시 권한을 요구한다.

- [x] `[UpperLimitRotationRetirement0814] 전일 상한가 순환관찰·bounded-live 자동전환 전체 폐기` (`Due: 2026-08-14`, `Slot: INTRADAY`, `TimeWindow: 11:40~13:30`, `Track: ScalpingLogic`)
  - Source: [Plan Rebase](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [traceability](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [postclose wrapper](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [scalping scanner](/home/ubuntu/KORStockScan/src/scanners/scalping_scanner.py)
  - 판정: 사용자 명시 지시에 따라 `upper_limit_watch` 후보·WS 관찰·rising 슬롯 회수·scanner 승격·bounded-live 정책·장후 report/verifier/controller 소비자를 제거하고 기존 산출물을 archive/audit evidence로만 고정한다.
  - 적용 경계: 현재 PID `193679`는 11:34:59 KST에 변경 전 코드로 시작했으며 이 작업에서는 bot을 재기동하지 않았다. source tree와 다음 기동 경로에서는 폐기됐지만, 현재 프로세스의 메모리 내 observer 해제는 별도 승인된 우아한 재기동 시점에 완료한다.
  - 경계: 일반 상한가 근접 추격매수 차단, 보유종목 상한가 도달 청산, limit-down 관찰, opening/rising 예산과 provider·bot·수량·broker/hard-safety는 변경하지 않는다.
  - 재개 조건: 기존 플래그나 과거 artifact로 재활성화하지 않으며, 향후 재검토는 신규 workorder·namespace·증거계약·runtime guard를 요구한다.





## Micro-reversion 기계 연결

- [x] `[MachineMicrostructureConsumerBridge0814] 위젯·episode 기계 장후 micro-reversion 진단 연결` (`Due: 2026-08-14`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~20:30`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py), [postclose wrapper](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [traceability](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정: target-date 위젯 calibration/symbol-research/21:15 collector-expansion과 active/expanded episode profile inventory를 매일 동적으로 다시 발견하고, owner report schema/date와 aware timestamp를 검증한 뒤 exact-date micro 0B/0D/event-reference를 `signal -> buy-fill-confirmed -> target-fill-confirmed/exit` lifecycle anchor에 결합한다. actual/counterfactual, realized/right-censored, context-matched/policy-eligible unique decision lifecycle을 분리하며 구조 계약이 유효한 HELD-only lifecycle은 진단 context에 보존하되 정책 readiness 표본에는 넣지 않는다. audit·schema·policy·source-quality 계약 불합격 lifecycle은 context에서도 fail closed한다. 20:10 1차 산출 뒤 widget expansion service가 같은 날짜 artifact를 원자 갱신한다.
  - 소비 계약: 다음 거래일 위젯·episode 장후 report는 직전 owner source date와 일치하는 owner-shaped diagnostic만 읽고 `selection_effect=false`로 보조 지표를 노출한다. missing/invalid/date mismatch는 base EV·policy를 그대로 유지하며, 신규 종목의 micro partition·symbol·anchor 결손은 scope별 producer/consumer gap으로 남기고 0수익으로 보간하지 않는다.
  - 목적 판정: lifecycle duration, 빠른 목표완료, 자본점유, 비용 반영 자본시간당 수익을 계측해 빠른 회전 목적의 관찰 기반은 닫았지만 현재 runtime은 episode 일 1회 attempt와 HELD 종결, widget open episode/cooldown에 묶인다. 따라서 이 연결은 빠른 재진입·TP timeout·target/cooldown/cap을 바꾸는 매매기계가 아니라 `postclose_diagnostic_only`인 부분 구현이다.
  - 금지: `runtime_effect=false`, `allowed_runtime_apply=false`, `broker_order_forbidden=true`를 유지하며 gross/no-slippage 값을 primary EV로 승격하거나 threshold/policy 선택, 실체결 품질 승인, 주문/provider/bot/cap 변경에 사용하지 않는다.

- [x] `[MachineMicrostructureCollectionFeedback0814] micro 결손의 다음 거래일 source-only 수집 되먹임 구현·리뷰` (`Due: 2026-08-14`, `Slot: INTRADAY`, `TimeWindow: 15:20~16:10`, `Track: RuntimeStability`)
  - Source: [collection_targets.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/collection_targets.py), [machine attribution](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py), [Kiwoom WebSocket](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py), [main bot](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py), [Kiwoom contract](/home/ubuntu/KORStockScan/docs/kiwoom-api-data-contract.md)
  - 판정: repairable `micro_symbol_not_observed` 등 결손을 다음 KRX 거래일 exact-date target으로 생성한다. 일회 복구 뒤 표본 누락이 재발하지 않도록 현재 위젯·episode 동적 universe도 `micro_policy_sample_accumulation` 대상으로 계속 회전한다. 기본 일 4종목, stable priority cohort, active owner 우선, budget 2 이상에서 prospective 1-slot, symbol round-robin과 종목별 venue phase를 독립 적용한다. 이는 budget 안의 결정론적 공정 회전이지 overflow가 바로 다음 거래일에 반드시 선택된다는 보장은 아니다.
  - 수동관리 경계: 수동관리 제외 여부는 micro 수집·평가·정책 연구에 적용하지 않고 모든 종목을 동일 취급한다. 해당 제외는 최종 실주문 owner 충돌을 막는 매매 경계에서만 적용한다.
  - runtime 경계: observer 활성 boot에서만 KRX/plain·NXT/`_NX`·SOR/`_AL`의 0B/0D source-only REG를 발행한다. boot의 widget/runtime 우선 등록 code는 source-only 재분류에서 보호한다. micro collector 뒤에서 common trading tick과 다른 전략 observer 전파를 중단하고, 정상 runtime target이 같은 code를 요구하면 REMOVE 후 정상 route/type REG 성공 뒤 suppression을 해제한다. 다음 exact-date set은 이전 source-only set을 교체한다.
  - 금지: 실제 관찰 구독 부하는 `market_data_subscription_effect=true`로 공개한다. target artifact와 runtime event는 `runtime_effect=false`, `trading_runtime_effect=false`, `trading_decision_effect=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`이며 trading target·policy·order/provider/bot/cap 권한을 만들지 않는다.

- [x] `[MicroReversionAIQualitySidecar0814] Exact V2 AI 품질용 past-only micro context sidecar 구현·리뷰` (`Due: 2026-08-14`, `Slot: INTRADAY`, `TimeWindow: 15:20~16:20`, `Track: ScalpingLogic`)
  - Source: [ai_quality_bridge.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/ai_quality_bridge.py), [depth_join.py](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/depth_join.py), [traceability](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정: Exact V2 snapshot watermark 이전의 동일 symbol·venue·session·sequence epoch 0B/0D만 tactical context에 결합하고, 이후 MFE/MAE·first-hit은 별도 outcome label로 유지한다. 원 provider payload와 hash는 변경하지 않는다.
  - 소비 경계: 자동 postclose/runtime consumer는 추가하지 않는다. 명시적 수동/Codex paired-replay 품질 검토에서만 `--write`로 생성하며 verified cost profile이 없으면 비용 반영 승격 판정을 열지 않는다.
  - 금지: `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`, `provider_call_performed=false`를 유지하며 prompt future leakage, 실주문·threshold·TP/stop/trailing·provider·bot·cap 변경에 사용하지 않는다.

- [x] `[MachineMicrostructurePersistentApprovalQueue0814] micro 정책 최초 승인 누락 방지 제어면 구현·리뷰` (`Due: 2026-08-14`, `Slot: INTRADAY`, `TimeWindow: 16:00~17:10`, `Track: RuntimeStability`)
  - Source: [approval ledger](/home/ubuntu/KORStockScan/src/engine/automation/machine_microstructure_policy_approval.py), [postclose wrapper](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [PREOPEN wrapper](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_preopen.sh), [checklist builder](/home/ubuntu/KORStockScan/src/engine/build_next_stage2_checklist.py), [traceability](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정: readiness 계약을 통과한 candidate를 hash별로 영속 보존하고 `DESIGN_REQUIRED -> REVIEW_READY -> USER_APPROVED -> PREOPEN_SCHEDULED -> APPLIED -> POST_APPLY_ATTRIBUTED`로 추적한다. fresh loaded source에서 후보가 사라지거나 intake가 거절되면 `REVALIDATION_REQUIRED`, exact-date PREOPEN handoff가 미적용이면 `PREOPEN_MISSED_REVIEW_REQUIRED`로 전환한다. 진짜 source missing일 때만 기존 pending을 보존하며 후보별 POSTCLOSE/PREOPEN phase별 일 1회 관리자 Telegram과 다음 거래일 parser-friendly checklist에 표면화한다.
  - 승인 경계: source candidate의 `runtime_registry_verified=true` 자기선언은 권한이 아니다. 실제 PREOPEN consumer·apply receipt owner·post-apply attribution owner와 함께 trusted registry에 등록된 family, same-stage 단일 축, bounded before/after, rollback이 모두 일치해야 승인할 수 있다. receipt는 trusted owner, handoff/apply 이후 aware timestamp, exact target 거래일, ingest 미래 아님을 검증하고 새 candidate version 정산보다 기존 exact-date apply receipt를 먼저 반영한다. 동일 초 재결정도 invalidation보다 뒤선 causal timestamp를 가져야 하며, ledger는 runtime env를 직접 변경하거나 미적용 handoff를 자동 이월하지 않는다.
  - 자동화 경계: family-owned guarded apply receipt 파일과 trusted registry를 재검증한 뒤에만 최초 family enrollment를 닫고, 이후 동일 family/stage/axis/bounded-contract 후보만 기존 장후→PREOPEN 체인 자격을 얻는다. 주문·threshold/provider/bot/cap·hard safety·broker guard 직접 변경은 금지한다. 현재 trusted registry와 promotion candidate는 비어 있어 runtime 효과는 없다.

- [ ] `[MachineMicroPolicyCandidateProducer0824] rolling paired-policy candidate producer 구현·acceptance` (`Due: 2026-08-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~18:30`, `Track: ScalpingLogic`)
  - Source: [machine attribution](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py), [candidate intake/approval ledger](/home/ubuntu/KORStockScan/src/engine/automation/machine_microstructure_policy_approval.py), [machine attribution reports](/home/ubuntu/KORStockScan/data/report/machine_microstructure_attribution), [traceability](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: clean baseline 이후 실제 관찰 5거래일·동일 anchor 20건 이상, BBO 95% 이상, depth 90% 이상, invalid row 0, 비용·source quality 반영 5/10/20일 EV 모두 양수, 상대 EV uplift 1% 이상, 20일 net profit 양수, paired p10·held/unresolved 비열화를 모두 검증한 rolling producer만 `policy_promotion_candidates`를 만들 수 있다. floor 미달이면 후보를 합성하지 않고 부족한 day/anchor/coverage를 명시한다.
  - 구현 경계: producer는 source-only candidate만 만들고 runtime family를 자기등록하지 않는다. 후보가 생기면 ledger가 `DESIGN_REQUIRED`로 영속 보존·알림하며, 실제 bounded family/consumer/rollback/receipt 구현과 최초 사용자 승인은 별도 단계로 닫는다.
  - 금지: daily-only EV, simple sum, 비용 미반영 값, 결손 0 보간, 수동관리 제외 여부에 따른 관찰 차별, 후보 생성만으로 runtime env·주문·provider/bot/cap·hard safety를 변경하지 않는다.

- [ ] `[MachineMicrostructureCollectionCanary0818] exact-date 수집 되먹임 첫 장중 acceptance 확인` (`Due: 2026-08-18`, `Slot: INTRADAY`, `TimeWindow: 09:05~15:20`, `Track: RuntimeStability`)
  - Source: [collection target](/home/ubuntu/KORStockScan/data/runtime/scalp_micro_reversion_collection_targets/scalp_micro_reversion_collection_targets_2026-08-18.json), [micro observations](/home/ubuntu/KORStockScan/data/observations/scalp_micro_reversion_forward), [intraday WS freshness](/home/ubuntu/KORStockScan/data/report/intraday_ws_freshness_monitor), [machine attribution](/home/ubuntu/KORStockScan/data/report/machine_microstructure_attribution)
  - 판정 기준: selected item이 기존 WS item budget 안에서 0B/0D를 수신하고 micro partition에 저장되며 `REALTIME_TICK_ARRIVED`·trading target·limit-down observer로 전파되지 않아야 한다. 이전 exact-date set 누적, queue/writer drop·error·storage self-disable·projection breach가 없어야 한다.
  - 다음 액션: `pass_source_only_collection`, `partial_budget_overflow_rotates`, `fail_no_0b_or_0d`, `fail_trading_event_leak`, `fail_storage_guard` 중 하나로 닫는다. bot 재기동은 기존 운영 기동 일정 또는 별도 사용자 승인 범위에서만 수행한다.

- [ ] `[MachineMicrostructurePolicyReadiness0831] 위젯·episode micro-conditioned 정책 승격 가능성 첫 rolling 판정` (`Due: 2026-08-31`, `Slot: POSTCLOSE`, `TimeWindow: 21:20~21:40`, `Track: ScalpingLogic`)
  - Source: [machine attribution](/home/ubuntu/KORStockScan/data/report/machine_microstructure_attribution), [traceability](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [widget runbook](/home/ubuntu/KORStockScan/docs/widget-signal-auto-trading-runbook.md), [episode runbook](/home/ubuntu/KORStockScan/docs/low-price-two-leg-machines.md)
  - 판정 기준: 동일 owner/symbol/session의 관찰 5거래일·policy-eligible unique decision lifecycle 20건, BBO 95% 이상, depth 90% 이상, invalid row 0을 먼저 충족한다. context-matched HELD-only lifecycle은 결손/위험 진단에 남기되 readiness 표본으로 세지 않고, 다른 source-quality 계약 불합격은 fail closed한다. 동일 lifecycle 현 정책 대 단일 micro-conditioned axis의 비용 반영 paired `source_quality_adjusted_ev_pct`가 rolling 5/10/20일 모두 양수, 20일 net profit과 비용 반영 자본시간당 수익 양수, primary EV 상대 개선 1% 이상이며 p10·HELD/unresolved가 악화되지 않아야 한다.
  - 다음 액션: 미달이면 `hold_collection_or_sample`; 충족하면 신규 bounded family·same-stage owner·rollback·post-apply attribution 설계를 먼저 검토한다. 최초 real runtime mapping은 사용자 명시 승인 전까지 만들거나 적용하지 않는다.

- [ ] `[MachineLifecycleTurnoverPolicyResearch0824] 위젯·episode 빠른 회전 목적의 paired cost-aware 정책 연구` (`Due: 2026-08-24`, `Slot: POSTCLOSE`, `TimeWindow: 18:30~20:00`, `Track: ScalpingLogic`)
  - Source: [machine attribution](/home/ubuntu/KORStockScan/data/report/machine_microstructure_attribution), [widget calibration](/home/ubuntu/KORStockScan/data/report/widget_auto_trade_policy_calibration), [episode tuning](/home/ubuntu/KORStockScan/data/report/low_price_two_leg_tuning), [traceability](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: current policy와 단일 speed/turnover 축 대안을 동일 policy-eligible unique lifecycle에서 paired 비교한다. `source_quality_adjusted_ev_pct`, net profit, p10, HELD/right-censored, reconciliation-confirmed duration, target completion within 180 seconds, capital occupancy, cost-aware net return per capital-hour를 함께 보고 gross/no-slippage는 진단으로만 유지한다.
  - 구현 경계: episode 일 1회 attempt·HELD/no forced-exit와 widget open episode·cooldown·daily cap을 현 baseline으로 명시하고, 재진입·TP timeout·target/cooldown/cap 가운데 같은 stage 단일 축만 source-only candidate로 설계한다. 첫 real runtime family에는 rollback·post-apply attribution·사용자 명시 승인이 필요하다.
  - 금지: 속도나 거래횟수만으로 EV·순이익·downside를 대체하거나 기존 주문, target, timeout, cooldown, cap, hard safety, broker/provider/bot을 즉시 변경하지 않는다.

- [ ] `[MachineMicroCollectionReceipt0818] micro source-only 수집 등록·경로 receipt 영속화` (`Due: 2026-08-18`, `Slot: INTRADAY`, `TimeWindow: 09:05~15:20`, `Track: RuntimeStability`)
  - Source: [collection target](/home/ubuntu/KORStockScan/data/runtime/scalp_micro_reversion_collection_targets), [Kiwoom contract](/home/ubuntu/KORStockScan/docs/kiwoom-api-data-contract.md), [Kiwoom WebSocket](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py), [micro observations](/home/ubuntu/KORStockScan/data/observations/scalp_micro_reversion_forward)
  - 판정 기준: exact-date target별 `target accepted`, `REG sent/accepted`, `budget skipped`, `first 0B`, `first 0D`, partition write/error를 symbol·venue·session·target hash와 함께 durable receipt로 남기고 target/report의 선택과 실제 producer 수신을 대사한다.
  - 공식 계약 gate: Kiwoom REST/WebSocket 계약을 변경하기 전에 현 공식 upstream commit, inspected paths, retrieval time, 0B/0D REG/REMOVE·route suffix·한도 계약을 기록하고 불명확한 semantics는 source-quality gap으로 fail closed한다.
  - 금지: receipt 결손을 거래 신호·정책 failure로 간주하거나 stale/broker/account/order/quantity/cooldown/provider/bot/hard-safety guard를 완화하지 않는다.

- [ ] `[MachineMicroPolicyRegistryHardening0824] micro trusted policy registry canonical bound·conflict 계약 강화` (`Due: 2026-08-24`, `Slot: POSTCLOSE`, `TimeWindow: 20:00~20:40`, `Track: RuntimeStability`)
  - Source: [approval ledger](/home/ubuntu/KORStockScan/src/engine/automation/machine_microstructure_policy_approval.py), [traceability](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: trusted registry가 비어 있는 현재 상태를 유지한 채 family별 canonical before/after type·finite value·bound·scope allowlist, exact PREOPEN consumer, trusted apply/attribution receipt owner, rollback, 중앙 same-stage conflict를 machine-readable하게 검증하는 acceptance test를 닫는다.
  - 다음 액션: 모든 계약과 첫 사용자 승인이 닫히기 전에는 candidate 자기선언이나 local family 검증만으로 registry enrollment·runtime mapping을 만들지 않는다.
  - 금지: registry hardening을 threshold/order/provider/bot/cap/hard-safety 변경 또는 자동 최초 승인으로 사용하지 않는다.

- [ ] `[MachineMicroPostcloseOrchestration0824] machine micro 장후 단일 최종 orchestration·last-writer 검증` (`Due: 2026-08-24`, `Slot: POSTCLOSE`, `TimeWindow: 20:40~21:30`, `Track: RuntimeStability`)
  - Source: [postclose wrapper](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [widget expansion service](/home/ubuntu/KORStockScan/deploy/systemd/korstockscan-widget-expansion-recommendation.service), [machine attribution](/home/ubuntu/KORStockScan/data/report/machine_microstructure_attribution), [approval ledger](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval)
  - 판정 기준: owner reports, exact-date canary archive, widget expansion, final attribution, collection target, approval intake가 하나의 dependency/receipt 순서로 정확히 한 번 최종화되고 20:10 1차 산출과 21:15 갱신의 stale overwrite·중복 알림·후행 consumer 누락이 없음을 재실행/부분실패 acceptance로 확인한다.
  - 다음 액션: `single_final_attribution_pass`, `idempotent_retry_pass`, `dependency_missing_fail_closed`, `last_writer_conflict_fix_required` 중 하나로 닫는다.
  - 금지: orchestration 정리를 runtime threshold/order/provider/bot/cap 변경이나 장중 재기동 근거로 사용하지 않는다.

- [ ] `[MachineMicrostructurePostcloseVerify0814] 당일 동적 종목 및 micro producer/consumer gap 최종 확인` (`Due: 2026-08-14`, `Slot: POSTCLOSE`, `TimeWindow: 21:20~21:30`, `Track: RuntimeStability`)
  - Source: [machine microstructure report](/home/ubuntu/KORStockScan/data/report/machine_microstructure_attribution/machine_microstructure_attribution_2026-08-14.json), [widget expansion report](/home/ubuntu/KORStockScan/data/report/widget_collector_expansion_recommendation/widget_collector_expansion_recommendation_2026-08-14.json), [episode expansion report](/home/ubuntu/KORStockScan/data/report/low_price_two_leg_expanded_candidate_research/low_price_two_leg_expanded_candidate_research_2026-08-14.json)
  - 판정 기준: 21:15 final refresh가 위젯 collector-expansion과 episode active/expanded inventory, exact-date canary archive를 모두 소비하고 각 신규 종목을 `matched`, `observed_no_owner_episode` 또는 명시적 micro/source gap 중 하나로 빠짐없이 귀속한다. 다음 거래일 owner report가 정확한 전 거래일 source date의 diagnostic을 `selection_effect=false`로 읽고 policy-eligible unique lifecycle readiness와 context-only HELD를 분리하는지도 확인한다.
  - 금지: gap을 0수익으로 보간하거나 기존 owner EV/policy failure로 해석하지 않고, 이 일일 diagnostic만으로 threshold/policy/runtime/order 변경을 열지 않는다.
  - 다음 액션: `complete_dynamic_inventory_with_matches`, `complete_inventory_with_explicit_gaps`, `owner_source_missing_retry_required`, `micro_contract_invalid_fix_required` 중 하나로 닫는다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
