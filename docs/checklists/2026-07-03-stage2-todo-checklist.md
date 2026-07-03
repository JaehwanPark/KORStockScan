# 2026-07-03 Stage2 To-Do Checklist

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
- 운영 메모: 사용자 요청으로 System Error Detector 임시 OFF를 해제하고 cron wrapper와 bot daemon 기본값을 재개한다. 이 변경은 report-only 운영 감시 재개이며 threshold/env/provider/order/bot restart 권한을 만들지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-07-02` postclose -> `2026-07-03`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0703] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-07-03`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-02.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 실행 결과: `applied_guard_passed_env`.
  - 근거: `threshold_apply_2026-07-03.json` status=`auto_bounded_live_ready`, apply_mode=`auto_bounded_live`, runtime_change=`true`, source_phase_auto_apply_blocked=`false`, approval_contract_gaps=`0`, approval_requests=`0`, warnings=`0`.
  - runtime env 확인: `threshold_runtime_env_2026-07-03.json` generated_at=`2026-07-03T07:35:02+09:00`, selected_family_count=`23`, env_overrides_count=`309`.
  - verify 확인: `threshold_runtime_env_verify_2026-07-03.json` status=`pass`, passed=`true`, missing_family_count=`0`, findings_count=`0`.

- [x] `[RisingMissedScoutRuntimePreopen0703] rising_missed_scout_workorder 구현분 다음 장전 runtime 반영 여부 확인` (`Due: 2026-07-03`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-07-02.json), [code_improvement_workorder_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-02.json), [threshold_apply_2026-07-03.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-03.json), [threshold_runtime_env_2026-07-03.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-03.json), [threshold_runtime_env_verify_2026-07-03.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-03.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`5`, forced_scout_with_post_sell_count=`14`, profitable_forced_scout_count=`11`, loss_or_flat_forced_scout_count=`3`, current_missed_count=`3`)과 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.
  - 실행 결과: `source_only_no_runtime_authority`.
  - 근거: `rising_missed_scout_workorder_2026-07-02.json` allowed_runtime_apply=`false`, runtime_effect=`false`, decision_authority=`source_only_operational_workorder`; code_improvement_order_count=`5`이며 5개 order는 모두 status=`implemented`.
  - 표본 요약: forced_scout_with_post_sell_count=`14`, profitable_forced_scout_count=`11`, loss_or_flat_forced_scout_count=`3`, current_missed_count=`3`.
  - runtime 반영 확인: 당일 selected_families에는 `entry_opportunity_recheck_runtime`, `early_accel_recheck_runtime`, `scalping_scanner_real_source_guard_runtime` 등 기존/별도 runtime family가 포함됐지만, rising missed scout workorder 자체는 runtime_effect=`false`/allowed_runtime_apply=`false`인 source-only 산출물이므로 별도 runtime authority로 인정하지 않는다. verify는 status=`pass`, missing_family_count=`0`.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RuntimeEnvIntradayObserve0703] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-07-03`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-02.json)
  - 판정 기준: selected_families=score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, lifecycle_decision_matrix_runtime, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, weak_context_late_entry_guard_runtime, persistent_operator_overrides_2026_06_26가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.
  - 실행 결과: `provenance_partial_present_no_rollback_breach`.
  - 실행 시각: `2026-07-03T10:55:22+09:00`.
  - runtime env 확인: `threshold_runtime_env_2026-07-03.json` selected_family_count=`23`, `threshold_runtime_env_verify_2026-07-03.json` status=`pass`, passed=`true`, missing_family_count=`0`.
  - event provenance 확인: `threshold_events_2026-07-03.jsonl`/`pipeline_events_2026-07-03.jsonl`에서 문자열 또는 family provenance가 확인된 selected family는 `score65_74_recovery_probe`, `quote_consistency_normalization`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `scalp_sim_auto_approval`, `entry_cancel_wait_runtime`, `sell_side_open_time_block_runtime`이다.
  - missing/미관측 확인: 나머지 selected family는 10:55 KST 현재 이벤트 natural match 또는 동일 문자열 provenance가 확인되지 않았다. 이는 장중 threshold mutation 사유가 아니며 장후 post-apply attribution/verifier에서 재확인한다.
  - rollback guard 확인: sim/source authority guard flag 위반 없음, 장중 threshold/env/provider/order/bot 변경 없음.

- [x] `[SimProbeIntradayCoverage0703] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-07-03`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-02.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.
  - 실행 결과: `sim_probe_authority_preserved_source_quality_split`.
  - 실행 시각: `2026-07-03T10:55:22+09:00`.
  - 표본 확인: sim/probe 추정 이벤트 count=`1416`, open-stage 추정=`1396`, closed-stage 추정=`20`.
  - 권한 분리 확인: `actual_order_submitted` 위반=`0`, `broker_order_forbidden` 위반=`0`, sim/source authority guard flag 위반=`0`.
  - active state 확인: active priority seed match count=`137`, active_seed_id=`rising_missed_prior_e65574639530054b`.
  - 주의: 일부 sim/source 이벤트의 `decision_authority`가 `sim_observation_only`가 아닌 source 전용 권한으로 기록된 count=`24`가 있으나 real order/provider/bot/cap/threshold 권한 위반은 확인되지 않았다. 장후 verifier에서 source-only 분리 상태를 재확인한다.

- [x] `[IntradaySourceQualityGateCheck0703] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-07-03`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-07-03.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-03.jsonl), [threshold_events_2026-07-03.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-03.jsonl), [observation_source_quality_audit_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-03.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-07-03 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.
  - 실행 결과: `defective_rows_excluded`.
  - 실행 시각: `2026-07-03T14:20:37+09:00`.
  - 감사 결과: status=`pass`, event_count=`75534`, hard_blocking_contract_gap_count=`0`, hard_blocking_excluded_row_count=`0`, tuning_input_allowed=`true`, raw_row_exclusion_applied=`true`, unknown_token_stage_count=`0`, review_warning_count=`0`, reviewed_unknown_token_stage_count=`8`.
  - raw row exclusion 확인: excluded_row_count=`89`, stage_counts=`{'scalp_entry_action_decision_snapshot': 89}`, manifest=`data/source_quality/raw_row_exclusion/2026-07-03_20260703T142019383320+0900/manifest.json`.
  - 제외 사유 확인: `required_field_missing=89`, `provenance_missing=89`, `not_evaluated_context=89`, `insufficient_history=34`, `source_quality_blocker=24`, `unknown_token=14`.
  - 다음 확인: hard block은 없지만 raw exclusion이 존재하므로 장후 `PostcloseSourceQualityGateReview0703`에서 EV 소비 전 결손 row/window 제외 반영을 재확인한다. broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.

- [x] `[IntradayAutomationHealthCheck20260703] Runbook 장중 자동화체인 상태 확인` (`Due: 2026-07-03`, `Slot: INTRADAY`, `TimeWindow: 09:05~15:30`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [run_buy_funnel_sentinel_cron.log](/home/ubuntu/KORStockScan/logs/run_buy_funnel_sentinel_cron.log), [run_holding_exit_sentinel_cron.log](/home/ubuntu/KORStockScan/logs/run_holding_exit_sentinel_cron.log), [run_panic_sell_defense_cron.log](/home/ubuntu/KORStockScan/logs/run_panic_sell_defense_cron.log), [run_panic_buying_cron.log](/home/ubuntu/KORStockScan/logs/run_panic_buying_cron.log), [system_metric_sampler_cron.log](/home/ubuntu/KORStockScan/logs/system_metric_sampler_cron.log), [bd_fbuy_accum_pre_intraday_cron.log](/home/ubuntu/KORStockScan/logs/bd_fbuy_accum_pre_intraday_cron.log)
  - 실행 결과: `runbook_intraday_health_warning_report_only`.
  - 실행 시각: `2026-07-03T10:58:01+09:00`.
  - artifact append 확인: `pipeline_events_2026-07-03.jsonl` mtime=`10:58`, `threshold_events_2026-07-03.jsonl` mtime=`10:58`.
  - cron marker 확인: BUY Funnel Sentinel latest classification=`NORMAL`; Holding/Exit Sentinel latest classification=`HOLD_DEFER_DANGER`, secondary=`AI_HOLDING_OPS,SOFT_STOP_WHIPSAW`; Panic Sell state=`NORMAL`; Panic Buying state=`NORMAL`; System Metric Sampler latest `[DONE]`; BD_FBUY_ACCUM_PRE latest `[DONE]`, db_pass_count=`1`.
  - 권한 확인: sentinel/panic/BD_FBUY 결과는 report/source-only이며 threshold/env/provider/order/bot 변경 없음.

## 장후 체크리스트 (20:05~21:55)

- [x] `[PostcloseSourceQualityGateReview0703] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-07-03`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-03.json), [threshold_cycle_ev_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-03.json), [code_improvement_workorder_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-03.json), [threshold_cycle_postclose_verification_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-03.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.
  - 실행 결과: `source_quality_gate_pass`.
  - 실행 시각: `2026-07-03T21:05:00+09:00`.
  - postclose 감사 결과: `observation_source_quality_audit_2026-07-03.json` status=`pass`, generated_at=`2026-07-03T20:53:09+09:00`, event_count=`122764`, hard_blocking_contract_gap_count=`0`, hard_blocking_excluded_row_count=`0`, tuning_input_allowed=`true`, raw_row_exclusion_applied=`false`, unknown_token_stage_count=`0`, review_warning_count=`0`, reviewed_unknown_token_stage_count=`10`.
  - EV 소비 확인: `threshold_cycle_ev_2026-07-03.json` status=`warning`, source_quality_status=`warning`, source_quality_tuning_input_allowed=`true`, warning_count=`13`, live_auto_ready_count=`0`.
  - workorder handoff 확인: `code_improvement_workorder_2026-07-03.json` observation_source_quality_source_order_count=`0`, selected_implement_now_route_count=`0`, selected_unimplemented_runtime_effect_false_count=`0`.
  - verifier 확인: `threshold_cycle_postclose_verification_2026-07-03.json` status=`warning`; hard source-quality block이 아니라 handoff warning 중심으로 유지된다.

- [x] `[ThresholdDailyEVReport0703] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-07-03`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-03.json), [tuning_performance_control_tower_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-07-03.json), [runtime_approval_summary_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-07-03.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.
  - 실행 결과: `sim_progress_no_live_bucket`.
  - 실행 시각: `2026-07-03T21:05:00+09:00`.
  - daily EV 확인: `threshold_cycle_ev_2026-07-03.json` status=`warning`, source_quality_tuning_input_allowed=`true`, warning_count=`13`, live_auto_ready_count=`0`.
  - control tower 확인: lifecycle_sim_auto_approved_count=`2`, swing_sim_auto_approved_count=`36`, lifecycle_live_auto_apply_ready_count=`0`, bridge_live_auto_apply_ready_count=`0`, real_conversion_queue_count=`0`, positive_ev_real_conversion_queue_count=`0`.
  - 다음 장전 적용 입력: sim-auto/active-priority 관찰은 유지하지만 real/live-auto 전환 큐는 없음. `positive_ev_not_due_until_next_preopen_count=145`, key_lineage_blocker_count=`136`, sample_floor blocker가 top conversion blocker다.
  - runtime approval 확인: scalping_selected_auto_bounded_live=`2`, panic_approval_requested=`0`, entry_submit_drought_handoff_selected=`false`.

- [x] `[HumanInterventionSummary0703] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-07-03`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-03.json), [runtime_approval_summary_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-07-03.json), [tuning_performance_control_tower_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-07-03.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.
  - 실행 결과: `observe_only_no_user_approval_required`.
  - 실행 시각: `2026-07-03T21:05:00+09:00`.
  - approval 분류: panic_approval_requested=`0`, real_conversion_queue_count=`0`, positive_ev_real_conversion_queue_count=`0`, lifecycle_live_auto_apply_ready_count=`0`, bridge_live_auto_apply_ready_count=`0`.
  - Codex 구현 필요 분류: code-improvement workorder 기준 selected_implement_now_route_count=`0`, selected_unimplemented_runtime_effect_false_count=`0`; 신규 구현 지시 대상 없음.
  - 관찰만 분류: lifecycle_sim_auto_approved_count=`2`, swing_sim_auto_approved_count=`36`, key_lineage_blocker_count=`136`, positive_ev_not_due_until_next_preopen_count=`145`.
  - 수동 동기화: checklist 문서 수정 후 parser 검증을 AI가 실행하고, Project/Calendar 동기화는 문서 하단 표준 명령으로 사용자가 수동 실행한다.

- [x] `[CodeImprovementWorkorderReview0703] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-07-03`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-07-03.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-03.md), [code_improvement_workorder_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-03.json)
  - 판정 기준: selected_order_count=`109`와 `implement_now`, `attach_existing_family`, `defer_evidence`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.
  - 실행 결과: `terminal_non_implement_longstanding`.
  - 실행 시각: `2026-07-03T21:05:00+09:00`.
  - 최신 workorder 확인: source_order_count=`155`, selected_order_count=`109`, non_selected_order_count=`46`, selected_decision_counts=`{'attach_existing_family': 107, 'defer_evidence': 2}`.
  - 구현 큐 확인: selected_implement_now_route_count=`0`, selected_unimplemented_runtime_effect_false_count=`0`, artifact_regeneration_required_count=`0`, needs_followup_workorder_count=`0`.
  - 장기 항목 재판정: selected_terminal_non_implement_runtime_effect_false_count=`9`, selected_terminal_non_implement_longstanding_count=`9`, repeat_unresolved_escalation_count=`0`, repeat_unresolved_structural_blocker_count=`0`.
  - root-cause 확인: root_cause_closed_count=`79`, implementation_done_count=`1`, handoff_closed_root_cause_open_count=`20`. 남은 open은 conversion_lane key-lineage 관찰 문제이며 다음 PREOPEN/runtime/postclose 연속성 또는 natural_match_0로 닫는다.

- [x] `[LifecycleQuietGapReview0703] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-07-03`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-03.json), [runtime_apply_gap_audit_2026-07-03.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-03.md), [tuning_performance_control_tower_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-07-03.json)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`395`, quiet_gap_rollup_count=`395`, quiet_gap_codex_directive_count=`0`, codex_directive_count=`0`, source_dimension_gap_count=`74`, critical_failure_count=`0`, ai_review_status=`parsed`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.
  - 실행 결과: `rollup_only`.
  - 실행 시각: `2026-07-03T21:05:00+09:00`.
  - runtime apply gap 확인: status=`pass`, quiet_gap_count=`395`, quiet_gap_rollup_count=`395`, quiet_gap_codex_directive_count=`0`, codex_directive_count=`0`, source_dimension_gap_count=`74`, critical_failure_count=`0`, ai_review_status=`parsed`.
  - control tower 확인: runtime_apply_gap_audit_status=`pass`, runtime_apply_gap_audit_quiet_gap_count=`395`, runtime_apply_gap_audit_quiet_gap_codex_directive_count=`0`, source_artifact_warning_count=`0`.
  - 처리 확인: quiet gap은 rollup/관찰 전용이며 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.

- [x] `[AutomationTriggerDecisionSummary0703] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-07-03`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-07-03.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [threshold_cycle_postclose_cron.log](/home/ubuntu/KORStockScan/logs/threshold_cycle_postclose_cron.log)
  - 판정 기준: trigger decision summary의 total_steps=`16`, run_count=`16`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, scalp_sim_ai_deferred_review, pattern_lab_currentness_audit`, skip_steps_sample=`-`를 확인하고 wrapper 로그의 `[DONE] threshold-cycle postclose ...` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.
  - 실행 결과: `trigger_contract_pass`.
  - 실행 시각: `2026-07-03T21:05:00+09:00`.
  - trigger decision 확인: generated_at=`2026-07-03T20:15:57.548418+09:00`, total_steps=`16`, run_count=`16`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`, runtime_effect=`false`, allowed_runtime_apply=`false`.
  - wrapper marker 확인: `threshold_cycle_postclose_cron.log`의 최종 `[DONE] threshold-cycle postclose target_date=2026-07-03 ... finished_at=2026-07-03T20:43:43+0900` 확인. skip_count=`0`이므로 오늘 target-date의 trigger_decision skip marker는 기대값이 아니다.

- [x] `[RankChgSignLiveSampleValidation0703] ka00198 rank_chg_sign NXT/시간외 반복 샘플 검증 및 의사결정 입력 승격 여부 판단` (`Due: 2026-07-03`, `Slot: INTRADAY`, `TimeWindow: 17:10~19:50`, `Track: ScalpingLogic`)
  - Source: [kiwoom-api-data-contract.md](/home/ubuntu/KORStockScan/docs/kiwoom-api-data-contract.md), [kiwoom_utils.py](/home/ubuntu/KORStockScan/src/utils/kiwoom_utils.py), [scalping_scanner.py](/home/ubuntu/KORStockScan/src/scanners/scalping_scanner.py)
  - 판정 기준: NXT/시간외 거래 중 `ka00198(qry_tp=5)`를 5~10분 간격으로 반복 호출해 `rank_chg`, `rank_chg_sign`, `bigd_rank`, `base_comp_chgr`, `prev_base_chgr` 샘플을 누적하고, `rank_chg_sign` 비어있음/`+`/`-` 분포와 `rank_chg` 부호 불일치율을 확인한다. 최소 표본은 non-empty sign `>=30` 또는 호출 횟수 `>=20` 중 먼저 충족한 쪽으로 본다.
  - 금지: 반복 샘플 검증 전에는 `rank_chg_sign`을 scoring, entry, priority, live authority, threshold/env/provider/order/bot 변경 근거로 사용하지 않는다. 검증 중에도 raw provenance 외 authority를 열지 않는다.
  - 다음 액션: `raw_contract_confirmed_promote_candidate`, `keep_raw_unverified`, `field_missing_or_sparse`, `mismatch_requires_parser_guard`, `api_call_failed_retry_next_regular_session` 중 하나로 닫는다.
  - 실행 결과: `keep_raw_unverified`.
  - 실행 시각: `2026-07-03T21:05:00+09:00`.
  - 확인 결과: 오늘 read-only 샘플 근거는 [kiwoom-api-data-contract.md](/home/ubuntu/KORStockScan/docs/kiwoom-api-data-contract.md)에 반영되어 있으며, `rank_chg_sign`은 empty/`+`/`-`가 관찰됐고 non-empty sign은 해당 샘플의 `rank_chg` 부호와 일치했다.
  - 반복 표본 판정: data/log 경로에서 별도 반복 샘플 artifact 또는 `ka00198` rank sample 파일은 확인되지 않았다. 최소 표본(non-empty sign `>=30` 또는 호출 횟수 `>=20`) 충족 근거가 없으므로 scoring/entry/priority/live authority 입력 승격은 보류한다.
  - 코드/계약 확인: `get_realtime_item_rank_ka00198`는 `RankChangeSignAuthority='raw_unverified_not_decision_input'`를 부여한다. 현 상태에서는 raw provenance 보존만 허용한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-07-03 15:45:54`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-07-03.md`
- `Trade Review`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
