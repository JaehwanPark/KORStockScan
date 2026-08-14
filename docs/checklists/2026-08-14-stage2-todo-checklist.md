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
  - Source: [risky_micro_episode policy](/home/ubuntu/KORStockScan/src/engine/scalping/risky_micro_episode/policy.py), [rising_missed_intraday_feedback.py](/home/ubuntu/KORStockScan/src/engine/monitoring/rising_missed_intraday_feedback.py), [pipeline_events_2026-08-14.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-14.jsonl)
  - 판정 기준: promotion EV에는 `source_only_candidate`와 현재 policy version의 canonical `bid_plus_one_ttl_3s` profile만 1회 포함한다. `recheck_required`는 별도 진단 cohort로 유지하고, 같은 후보의 bid+1 TTL 3/5/10초와 candidate spread 15bp 이하 제한적 ask TTL 3초를 source-only paired counterfactual로 비교한다. clean baseline 이후 rolling resolved opportunity 30건·10 symbols·3 trade dates와 fresh executable ask-touch fill 뒤 target/adverse/timeout으로 종결된 filled-terminal 10건·3 trade dates를 모두 충족한 경우에만 `source_quality_adjusted_ev_pct` review 후보를 만든다.
  - 진행: report-only adapter와 rolling gate 구현·타깃 테스트·당일 실데이터 임시 재생은 완료했다. 전체 리뷰에서 cross-venue/global watermark가 exact-path 미체결을 확정할 수 있던 결함을 제거해 동일 종목·venue·session fresh-BBO watermark만 TTL 성숙을 소유하도록 보완했다. rolling row에 candidate status·policy version·entry profile을 보존하고 tick context·quote freshness·BBO 결손을 canonical instrumentation gap으로 계측한다. 11:40 KST 기존 v1 산출물은 481 observations 중 tick context missing 131·quote stale/age missing 41·BBO missing 16이며, v2 정식 산출물 재생성 전에는 promotion 표본으로 승계하지 않는다. 장중 계속 갱신되는 원본의 POSTCLOSE 최종 성숙·정식 산출물 재생성 전까지 체크는 OPEN으로 유지한다.
  - 금지: candidate count, `recheck_required`, 복수 entry profile 중복가중, mark-price MFE, daily-only win rate만으로 broker 주문, 취소, 자동매도, 수량/cap, hard safety, provider/bot 또는 PREOPEN live 승격을 열지 않는다. 3거래일 및 두 sample floor 충족 후에도 별도 PREOPEN policy·명시 승인 없이는 `real_order_promotion_allowed=false`를 유지한다. 기존 `position_sizing_dynamic_formula -> probe-first` 수량 owner와 episode/widget order ledger를 변경하거나 공유하지 않는다.
  - 다음 액션: `outcome_join_ready_positive_ev`, `outcome_join_ready_non_positive_ev`, `fill_feasibility_unresolved`, `source_quality_blocked`, `sample_floor_pending` 중 하나로 닫는다.

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





## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
