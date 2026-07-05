# 2026-07-06 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-07-03` postclose -> `2026-07-06`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0706] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-07-06`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-03.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 실행 기록: `applied_guard_passed_env`. `threshold_apply_2026-07-06.json` status=`auto_bounded_live_ready`, apply_mode=`auto_bounded_live`, runtime_change=`true`, generated_at=`2026-07-06T07:35:01+09:00`. `threshold_runtime_env_verify_2026-07-06.json` status=`pass`, passed=`true`, missing_family_count=`0`, findings=`[]`. wrapper log는 `[DONE] threshold-cycle preopen target_date=2026-07-06 finished_at=2026-07-06T07:35:01+0900`.
  - 근거: selected_families는 23개이며 `protect_trailing_smoothing`, `score65_74_recovery_probe`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `scalp_sim_auto_approval`, `lifecycle_bucket_discovery_sim_auto_approval`, `swing_sim_auto_approval`, `entry_cancel_wait_runtime` 등을 포함한다. `approval_requests`와 `approval_contract_gaps`는 0건이다.
  - 봇 env 확인: bot_main.py PID=`8260` 환경에서 `KORSTOCKSCAN_SCALP_PROTECT_TRAILING_SMOOTH_WINDOW_SEC=10`, `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`, `KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED=true`, `KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED=true`를 확인했다.
  - 금지 확인: 전일 EV summary는 report-only warning(`runtime_effect=false`, `decision_authority=threshold_cycle_ev_summary_report_only`, `live_auto_ready_count=0`)으로 분리했고, 장중 threshold/provider/order/bot 수동 변경은 수행하지 않았다.

- [x] `[RisingMissedScoutRuntimePreopen0706] rising_missed_scout_workorder 구현분 다음 장전 runtime 반영 여부 확인` (`Due: 2026-07-06`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-07-03.json), [code_improvement_workorder_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-03.json), [threshold_apply_2026-07-06.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-06.json), [threshold_runtime_env_2026-07-06.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-06.json), [threshold_runtime_env_verify_2026-07-06.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-06.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`4`, forced_scout_with_post_sell_count=`18`, profitable_forced_scout_count=`15`, loss_or_flat_forced_scout_count=`3`, current_missed_count=`5`)과 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.
  - 실행 기록: `implemented_but_runtime_not_selected`. `rising_missed_scout_workorder_2026-07-03.json`의 code_improvement_order_count=`4`, forced_scout_with_post_sell_count=`18`, profitable_forced_scout_count=`15`, loss_or_flat_forced_scout_count=`3`, current_missed_count=`5`를 확인했다. 4개 order(`order_rising_missed_classifier_prior_feedback_bridge`, `order_rising_missed_initial_quality_feedback_loop`, `order_rising_missed_scout_post_sell_bridge`, `order_rising_missed_scout_loss_filter`)는 implementation_status=`implemented`지만 각각 allowed_runtime_apply=`false`, runtime_effect=`false`다.
  - 근거: 당일 apply plan의 `rising_missed_first_touch_calibration`은 status=`loaded`, calibration_state=`hold_sample`, allowed_runtime_apply=`false`, source_quality_blocked=`false`로 로드됐다. 당일 runtime env selected_families 23개에는 별도 `rising_missed_*` runtime family가 포함되지 않았고 verify는 status=`pass`, missing_family_count=`0`으로 닫혔다.
  - 금지 확인: forced scout 손익과 source-only workorder를 근거로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval은 열지 않았다.

- [x] `[PreopenAutomationHealthCheck20260706] 장전 자동화체인 상태 확인` (`Due: 2026-07-06`, `Slot: PREOPEN`, `TimeWindow: 08:00~09:00`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [threshold_cycle_preopen_2026-07-06.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-07-06.status.json), [threshold_apply_2026-07-06.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-06.json), [threshold_runtime_env_2026-07-06.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-06.json), [threshold_runtime_env_verify_2026-07-06.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-06.json)
  - 판정: `pass`, Tuning Chain Control State=`GREEN`, blocked_stage=`-`.
  - 근거: `threshold_cycle_preopen_2026-07-06.status.json`은 status=`succeeded`, reason=`completed`, exit_code=`0`, runtime_effect=`preopen_runtime_env_apply_only`이며 apply/runtime env/manifest path가 모두 존재한다. `threshold_cycle_preopen_cron.log`에는 `[DONE] threshold-cycle preopen target_date=2026-07-06 finished_at=2026-07-06T07:35:01+0900` marker가 있다. `ensemble_scanner.log`는 `[DONE] final_ensemble_scanner target_date=2026-07-06 finished_at=2026-07-06T07:20:55`이고, `daily_recommendations_v2_diagnostics.json`은 latest_date=`2026-07-03`, selected_count=`2`, fallback_written_to_recommendations=`false`로 직전 영업일 추천 산출물을 유지한다. bot_main.py PID=`8260`은 07:55 KST 기동됐고 당일 runtime env 핵심 키를 로드했다.
  - 다음 액션: 장중 `RuntimeEnvIntradayObserve0706`, `SimProbeIntradayCoverage0706`, `IntradaySourceQualityGateCheck0706`에서 selected family provenance, sim/probe no-real-order 경계, source-quality gate를 이어서 확인한다.
  - 금지 확인: RunbookOps 확인을 broker/order/provider/cap/bot restart 또는 hard-safety 완화 근거로 사용하지 않았다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0706] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-07-06`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-03.json)
  - 판정 기준: selected_families=protect_trailing_smoothing, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, persistent_operator_overrides_2026_06_26가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0706] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-07-06`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-03.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0706] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-07-06`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-07-06.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-06.jsonl), [threshold_events_2026-07-06.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-06.jsonl), [observation_source_quality_audit_2026-07-06.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-06.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-07-06 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0706] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-07-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-07-06.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-06.json), [threshold_cycle_ev_2026-07-06.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-06.json), [code_improvement_workorder_2026-07-06.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-06.json), [threshold_cycle_postclose_verification_2026-07-06.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-06.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[RankChgSignPostcloseClosedMarketConclusion0706] ka00198 rank_chg_sign N/empty 의미 장후 결론 확인` (`Due: 2026-07-06`, `Slot: POSTCLOSE`, `TimeWindow: 20:05~20:15`, `Track: ScalpingLogic`)
  - Source: [ka00198_rank_chg_sign_nxt_operating_pre_krx_2026-07-06_0807_0820_combined_summary.json](/home/ubuntu/KORStockScan/data/runtime/kiwoom_api_samples/ka00198_rank_chg_sign_nxt_operating_pre_krx_2026-07-06_0807_0820_combined_summary.json), [kiwoom-api-data-contract.md](/home/ubuntu/KORStockScan/docs/kiwoom-api-data-contract.md), [kiwoom_utils.py](/home/ubuntu/KORStockScan/src/utils/kiwoom_utils.py)
  - 판정 기준: NXT 포함 거래종료 후 `ka00198(qry_tp=5)`를 30초 간격으로 반복 호출해 `rank_chg_sign`의 `+|-|N|empty` 분포와 signed `RankChange` 방향 불일치율을 확인한다. 오늘 08:07~08:20 KST NXT 운영/KRX 장전 표본은 `N=0`, `empty=216/400`, `+/-` 방향 불일치 0건으로 비교 기준으로 사용한다.
  - 금지: `rank_chg_sign`을 scoring, entry, priority, live authority, threshold mutation, broker/order/provider/bot 변경 근거로 사용하지 않는다. 확정 전후 모두 `RankChangeSignAuthority=raw_unverified_not_decision_input` 경계를 유지한다.
  - 다음 액션: `closed_market_N_reproduced`, `closed_market_empty_only`, `mixed_N_empty_requires_more_sample`, `api_error_retry_required`, `contract_doc_update_required` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0706] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-07-06`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-03.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0706] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-07-06`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-03.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0706] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-07-06`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-07-03.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-03.md), [code_improvement_workorder_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-03.json)
  - 판정 기준: selected_order_count=112와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0706] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-07-06`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-03.json), [runtime_apply_gap_audit_2026-07-03.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-03.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`395`, rollup_required_count=`395`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'exclusion_dimension_candidate': 1, 'parent_conflict_child': 8, 'positive_source_only_keep_collecting': 389}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0706] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-07-06`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-07-03.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-07-03.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`16`, run_count=`16`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, scalp_sim_ai_deferred_review, pattern_lab_currentness_audit`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:14, source_missing_or_unreadable:7, upstream_drift_signal:7, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
