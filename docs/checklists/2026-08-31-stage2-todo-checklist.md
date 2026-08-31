# 2026-08-31 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-08-28` postclose -> `2026-08-31`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0831] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-08-31`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-28.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0831] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-08-31`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-08-28.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-08-28.json), [code_improvement_workorder_2026-08-28.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-28.json), [threshold_apply_2026-08-31.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-31.json), [threshold_runtime_env_2026-08-31.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-31.json), [threshold_runtime_env_verify_2026-08-31.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-08-31.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`3`, forced_scout_with_post_sell_count=`5`, post_sell_join_coverage_pct=`1.068376`, outcome_coverage_state=`partial`, profitable_forced_scout_count=`4`, loss_or_flat_forced_scout_count=`1`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[WidgetEpisodeMarketWeaknessEntryFreeze0831] 사용자 승인 시장별 약세 latch 신규 BUY veto·미체결 BUY 취소 가동·귀속 확인` (`Due: 2026-08-31`, `Slot: INTRADAY`, `TimeWindow: 09:05~15:20`, `Track: RuntimeStability`)
  - Source: [market_weakness_entry_guard.py](/home/ubuntu/KORStockScan/src/engine/risk/market_weakness_entry_guard.py), [market_weakness_observer_state.json](/home/ubuntu/KORStockScan/tmp/market_weakness_observer_state.json), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: `WIDGET_EPISODE_MARKET_WEAKNESS_ENTRY_FREEZE_OPEN_BUY_CANCEL_V2`가 current-session `active|release_pending` latch와 canonical verified listing market이 일치하는 위젯·에피소드 신규·추가 BUY를 차단하고, 해제 후 동일 유효 신호·attempt를 재평가한다. 이미 접수된 BUY는 당일 exact owner 주문번호와 broker reconciliation의 현재 미체결 잔량이 확인된 경우에만 해당 잔량을 취소하며, block/cancel event에 observation ID·market·policy/operator·원주문·부분체결/잔량 provenance가 남는지 확인한다.
  - 금지: source/market scope 불명확 상태의 주문 취소, 수동·메인봇·다른 owner 주문, 매도·target 주문, 체결수량·보유, 수량 resize·가격, provider·broker guard 변경. observer/notifier source-only authority를 live authority로 직접 승격하지 않는다.
  - rollback: `KORSTOCKSCAN_WIDGET_EPISODE_MARKET_WEAKNESS_ENTRY_GUARD_ENABLED=0`; rollback 전 owner별 미체결·inventory를 대사하고 적용 process provenance를 남긴다.
  - 다음 액션: `active_market_entry_block_observed`, `active_market_exact_buy_remainder_cancel_observed`, `cancel_blocked_reconciliation_not_fresh`, `latch_inactive_no_block`, `no_natural_entry_or_open_buy_sample`, `source_or_market_mapping_blocked`, `rollback_required` 중 하나로 닫고 장후 machine weakness response attribution으로 신호 정합성을 누적한다.

- [ ] `[RuntimeEnvIntradayObserve0831] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-08-31`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-28.json)
  - 전일 postclose candidate_selected_families=entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, post_probe_winner_recovery, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0831] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-08-31`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-08-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-28.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0831] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-08-31`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-31.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-31.jsonl), [threshold_events_2026-08-31.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-31.jsonl), [observation_source_quality_audit_2026-08-31.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-31.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-08-31 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[MarketWeaknessHysteresisClosedLoop0831] 약세 차단신호 executable-BBO 반사실·OOS review·다음-session exact 정책 handoff 확인` (`Due: 2026-08-31`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:30`, `Track: RuntimeStability`)
  - Source: [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py), [machine_market_weakness_response.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_market_weakness_response.py), [market_weakness_hysteresis_tuning.py](/home/ubuntu/KORStockScan/src/engine/automation/market_weakness_hysteresis_tuning.py)
  - 판정 기준: 차단된 위젯·에피소드 신호가 content-hashed owner/scope/symbol/session/signal anchor로 보존되고 1·3·5·10·20·30분 fresh depth-backed executable BBO, 비용 차감 수익, MFE/MAE, target/adverse first-hit 및 오경보·누락경보로 분류되는지 확인한다. 10거래일·50신호·위젯/에피소드 각 10신호·KOSPI/KOSDAQ 각 10신호·latest 3거래일 OOS와 현 정책 실제 관측 3거래일을 요구하며, 전체 EV/p10/오분류 guard뿐 아니라 두 owner와 두 listing market 각각의 holdout/full EV 비열화 금지와 오분류 비증가가 모두 닫힌 경우에만 현재 정책에서 한 축 ±1인 exact next-session policy를 허용한다.
  - 권한 경계: 당일 hot mutation, 60초 spacing·breadth 정의, main bot, 가격·수량·target·holding/exit·broker guard 변경은 금지한다. 표본/review 미달은 현재 정책 carry-forward, exact policy/source hash 불일치는 2/3 baseline fallback으로 닫는다.
  - 다음 액션: 다음 장 OPEN에서 observation의 policy hash와 notifier state activation/release 값, 차단/해제 자연 표본 및 기존 owner 비훼손을 post-apply attribution으로 확인한다.

- [ ] `[PostcloseSourceQualityGateReview0831] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-08-31`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-08-31.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-31.json), [threshold_cycle_ev_2026-08-31.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-31.json), [code_improvement_workorder_2026-08-31.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-31.json), [threshold_cycle_postclose_verification_2026-08-31.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-31.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0831] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-08-31`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-08-28.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-08-28.json), [threshold_cycle_ev_2026-08-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-28.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0831] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-08-31`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-28.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[MainAIQualitySourceGapRuntimeExecutionReceiptCustodyRepair0831] RuntimeExecutionReceiptCustodyRepair main lifecycle source gap 복구 확인` (`Due: 2026-08-31`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-08-28.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-08-28.json)
  - 판정 기준: workorder `main-ai-gap-49c42abe1df61995628a5b96`의 owner=`RuntimeExecutionReceiptCustodyRepair`, reason_codes=`real_submitted_lifecycle_count=7, broker_execution_unique_count=10, execution_report_materialized_companion_binding_mismatch_count=1, lifecycle_exact_join_missing_count=7`를 source-only producer 보완으로 닫는다. 공식 raw execution envelope의 order/execution identity를 합성 없이 검증하고 결손 lifecycle만 제외한 뒤 paired producer를 재검증한다.
  - 완료 조건: official raw execution envelope/order/execution identity is complete for at least one reconciled lifecycle; materialized execution companions bind to their exact request census; custody and order authority remain unchanged
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[CodeImprovementWorkorderReview0831] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-08-31`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-08-28.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-08-28.md), [code_improvement_workorder_2026-08-28.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-28.json)
  - 판정 기준: selected_order_count=49와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0831] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-08-31`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-08-28.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-28.json), [runtime_apply_gap_audit_2026-08-28.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-28.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`339`, rollup_required_count=`339`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 338}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[MachineLifecycleTurnoverObjectiveFollowup0831] 위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인` (`Due: 2026-08-31`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_policy_approval_postclose_2026-08-28.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_2026-08-28.json), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 판정 기준: 승인 후보 수와 무관하게 `followup_required=true`인 미완료 목적 항목 `machine_lifecycle_turnover_policy_research_v1`(status=`EVIDENCE_ACCUMULATING`, next_action=`repair_excluded_source_report_contracts_and_rerun`)의 상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.
  - 상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, `EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. `CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.
  - 권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[AutomationTriggerDecisionSummary0831] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-08-31`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-08-28.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-08-28.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`9`, skip_count=`0`, source_missing_count=`4`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:8, disabled_by_runtime_policy:5, upstream_drift_signal:5, source_missing_or_unreadable:4, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 수동 운영 후속

- [ ] `[ScannerSubmitDroughtClosedLoop0901] scanner 탐색→runtime handoff→heavy evaluation 폐루프 자연표본 검증` (`Due: 2026-09-01`, `Slot: INTRADAY`, `TimeWindow: 09:05~15:20,16:00~19:20`, `Track: ScalpingLogic`)
  - Source: [intraday_ws_freshness_monitor.py](/home/ubuntu/KORStockScan/src/engine/monitoring/intraday_ws_freshness_monitor.py), [market_opportunity_census.py](/home/ubuntu/KORStockScan/src/engine/monitoring/market_opportunity_census.py), [run_market_opportunity_census_intraday.sh](/home/ubuntu/KORStockScan/deploy/run_market_opportunity_census_intraday.sh), [install_market_opportunity_census_cron.sh](/home/ubuntu/KORStockScan/deploy/install_market_opportunity_census_cron.sh), [install_stage2_ops_cron.sh](/home/ubuntu/KORStockScan/deploy/install_stage2_ops_cron.sh), [installed_trigger.json](/home/ubuntu/KORStockScan/data/runtime/market_opportunity_census/installed_trigger.json), [scalping_scanner.py](/home/ubuntu/KORStockScan/src/scanners/scalping_scanner.py), [kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py), [market_opportunity_census_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/market_opportunity_census/market_opportunity_census_2026-09-01.json), [intraday_ws_freshness_monitor_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_2026-09-01.json), [buy_funnel_sentinel_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-09-01.json), [holding_exit_sentinel_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/holding_exit_sentinel/holding_exit_sentinel_2026-09-01.json), [code_improvement_workorder_2026-09-01.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-01.json)
  - 판정 기준: 현재 runtime 반영 후 manual-control 제외 종목의 scanner promotion·WS REG·zero-fill WATCHING 잔존이 각각 0인지 확인한다. 성공 attach의 `scanner_runtime_handoff_promotion_id/epoch/runtime_instance_id/provenance_version` coverage 100%, scan generation conservation delta 0, pipeline/threshold mirror dedup, `eligible_for_heavy_entry_eval` 대비 heavy 미도달의 exact final outcome 귀속을 확인한다.
  - source-quality/경제성: `eligible_no_heavy`, `heavy_then_stale_queue_evict`, `non_gainer_not_rising_repeat`를 KRX/PREMARKET_KRX_LIKE/NXT별 exact executable BBO와 비용 계약에 결합한다. BBO·effective date·source hash 결손은 0수익으로 보간하지 않고 `source_quality_blocked` workorder로 유지한다.
  - 외부 포착률 분모: 공식 보통주 master effective date/hash, 설치 trigger와 capture cadence, stable opportunity episode ID/TTL/reset, bounded scanner detection SLA를 고정한다. capture 이후 same code·venue·session·episode의 `forward_exact`만 causal recall로 사용하고, named primary metric과 실제 output field·분모·분자 및 broad-population 최초 미도달 상태 보존식을 대조한다. 단일/얇은 capture나 same-day retrospective는 `early_evidence|hold_sample`이며 scanner recall 정상 근거가 아니다.
  - 자동 환류: intraday monitor의 unresolved directive가 같은 날짜 `build_code_improvement_workorder`에 자동 소비되고 source fingerprint·acceptance test를 보존하는지 확인한다. 다음 자연표본에서 gap이 0이면 workorder를 해소하고, 남으면 원인별 workorder를 유지한다.
  - 사전 구현/설치 확인: trigger receipt v2가 현재 crontab exact 5개 line과 wrapper SHA/executable을 검증하고, 실제 capture가 같은 session 내 venue/panel별 3회·연속 gap 360초 이하인지 확인한다. 각 신규 capture의 sanitized request contract+normalized response rows SHA가 검증되고, legacy 무해시 row는 소급 합성 없이 `capture_source_hash_missing`으로 차단돼야 한다. `install_stage2_ops_cron.sh`가 BUY/HOLD sentinel의 KRX·NXT trigger를 중복 없이 소유하고, 16시 이후 NXT append event가 두 sentinel report의 최신 source offset·completion time에 반영되는지 확인한다. ranked source/candidate→WATCHING admission→runtime attach→trusted AI→entry authority→submit safety→submit의 기존 event lineage field가 report에 나타나야 하며, executable BBO outcome 결손은 그대로 blocker다.
  - 권한 경계: 이 항목은 source-quality·instrumentation·report·test 폐루프 전용이다. 장중 threshold, provider/bot, 실주문·취소, 가격·수량·cap, broker/account/order/cooldown, stale/hard/protect/emergency guard를 자동 변경하지 않는다.

- [ ] `[LowPriceTwoLegProfileRevision0831] 8월 28일 추천 7건 exact-date profile 적용·기동 검증` (`Due: 2026-08-31`, `Slot: PREOPEN`, `TimeWindow: 08:45~10:20`, `Track: ScalpingLogic`)
  - Source: [low_price_two_leg_expanded_profile_evidence_2026-08-28.json](/home/ubuntu/KORStockScan/data/config/low_price_two_leg_expanded_profile_evidence_2026-08-28.json), [profiles.py](/home/ubuntu/KORStockScan/src/trading/low_price_two_leg/profiles.py), [low_price_two_leg_policy_2026-08-31.json](/home/ubuntu/KORStockScan/data/threshold_cycle/low_price_two_leg/applied/low_price_two_leg_policy_2026-08-31.json)
  - 판정 기준: 기존 5개 profile 갱신과 팬오션 morning/late-morning 2개 신규 profile을 합친 48개 inventory, evidence hash, exact-date applied policy와 preflight authority가 일치하고 설치된 timer가 해당 instance를 각각 09:34/10:04에 기동하는지 확인한다.
  - 권한 경계: 기존 주문·HELD custody는 제출 당시 세대 정책으로 유지한다. 승인 evidence에 고정된 target 외의 수량·target·stop·provider/bot·broker/account/order/quantity/cooldown guard를 변경하거나 다른 owner 보유수량을 흡수하지 않는다.
  - 완료 조건: applied policy validation pass, 7개 evidence binding pass, 팬오션 manual_operator exclusion 유지, preflight/live unit revision 일치, 중복 신규주문 0건. 서비스 설치 또는 기동 전에는 `implemented_not_runtime_reflected`, 자연 표본이 없으면 `runtime_reflected_no_natural_sample`로 분리한다.

- [ ] `[LogRotationWriterOwnershipRepair0831] writer-owned active log rotation 계약 보완 및 terminal 재검증` (`Due: 2026-08-31`, `Slot: POSTCLOSE`, `TimeWindow: 21:00~21:15`, `Track: RuntimeStability`)
  - Shortage ID: `operations|log_rotation_cleanup|writer_owned_active_logs|postclose|log_rotation_v1|daily|active_log_identity`
  - Source: [log_rotation_cleanup_cron.log](/home/ubuntu/KORStockScan/logs/log_rotation_cleanup_cron.log), [error_detection_2026-08-28.json](/home/ubuntu/KORStockScan/data/report/error_detection/error_detection_2026-08-28.json), [run_logs_rotation_cleanup_cron.sh](/home/ubuntu/KORStockScan/deploy/run_logs_rotation_cleanup_cron.sh), [run_owned_log_rotation.sh](/home/ubuntu/KORStockScan/deploy/run_owned_log_rotation.sh), [log_writer_rollover_receipts](/home/ubuntu/KORStockScan/data/report/log_writer_rollover_receipts)
  - 판정 근거: `2026-08-28` cleanup은 active log 8개를 writer-active로 보존하고 rotation을 defer했으며, writer-defer 7개가 연속 6회로 escalation되어 `[FAIL]`로 종료됐다. 21:55 final detector도 `cron_completion=fail`을 유지했다.
  - 보완 범위: installed crontab의 대상 writer가 `run_with_owned_log.sh`를 사용하고, owner-integrated pre-open rollover의 lock/open-inode/stable hash/no-clobber gzip/receipt 계약과 state reset 조건을 검증한다. 현재 writer가 쓰는 파일을 rename/unlink하거나 미검증 원본을 삭제하지 않는다.
  - 완료 조건: oversize source가 있으면 `rotated_verified` receipt의 owner/path/size/source SHA-256/archive SHA-256과 decoded gzip hash가 일치한다. open writer는 0 mutation `deferred_writer_active` 뒤 다음 closed invocation에서 finite하게 회복한다. 동일 계약의 21:00 scheduled run이 `[DONE]`, `writer_defer_escalated=0`, `writer_defer_state_failures=0`, 원본 손상 0건으로 닫히고 21:55 final detector의 `cron_completion=pass`가 확인된다. oversize 자연 표본이 없으면 `installed_no_oversize_sample`로 receipt acceptance만 OPEN 유지한다.
  - 권한 경계: 이 항목은 log lifecycle/process-liveness 보완 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
