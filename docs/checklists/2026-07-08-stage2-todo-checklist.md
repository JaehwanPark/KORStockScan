# 2026-07-08 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-07-07` postclose -> `2026-07-08`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0708] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-07-08`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-07.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-07.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 실행 결과: `applied_guard_passed_env`
  - 근거: [threshold_apply_2026-07-08.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-08.json) status=`auto_bounded_live_ready`, apply_mode=`auto_bounded_live`, runtime_change=`true`, approval_contract_gaps=`[]`, warnings=`[]`; [threshold_runtime_env_2026-07-08.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-08.json) selected_family_count=`23`, env_override_count=`306`; [threshold_runtime_env_verify_2026-07-08.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-08.json) status=`pass`, missing_family_count=`0`, findings=`[]`.
  - 유의: verify의 `pid_env_available=false`라 실행 중 봇 PID 환경 대조는 미확인이다. 장중에는 manual env override 없이 runtime event provenance만 확인한다.

- [x] `[RisingMissedScoutRuntimePreopen0708] rising_missed_scout_workorder 구현분 다음 장전 runtime 반영 여부 확인` (`Due: 2026-07-08`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-07-07.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-07-07.json), [rising_missed_normal_buy_bridge_candidate_discovery_2026-07-07.json](/home/ubuntu/KORStockScan/data/report/rising_missed_normal_buy_bridge_candidate_discovery/rising_missed_normal_buy_bridge_candidate_discovery_2026-07-07.json), [code_improvement_workorder_2026-07-07.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-07.json), [threshold_apply_2026-07-08.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-08.json), [threshold_runtime_env_2026-07-08.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-08.json), [threshold_runtime_env_verify_2026-07-08.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-08.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`4`, forced_scout_with_post_sell_count=`19`, profitable_forced_scout_count=`15`, loss_or_flat_forced_scout_count=`4`, current_missed_count=`0`)과 `rising_missed_normal_buy_bridge_candidate_discovery` 요약(status=`source_missing`, bridge_candidate_count=`0`, code_improvement_order_count=`0`, runtime_env_key=`KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED`)을 함께 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder`/bridge discovery 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.
  - 실행 결과: `runtime_env_reflected_and_verified`
  - 근거: `rising_missed_scout_workorder` summary는 code_improvement_order_count=`4`, forced_scout_with_post_sell_count=`19`, profitable_forced_scout_count=`15`, loss_or_flat_forced_scout_count=`4`, current_missed_count=`0`; `rising_missed_normal_buy_bridge_candidate_discovery` summary는 status=`source_missing`, bridge_candidate_count=`0`, code_improvement_order_count=`0`, runtime_env_key=`KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED`; [threshold_apply_2026-07-08.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-08.json)은 `rising_missed_normal_buy_bridge`를 selected=`true`, decision_reason=`operator_runtime_env_lock_preserved:rising_missed_normal_buy_bridge_operator_override_2026-07-08`로 기록했고 [threshold_runtime_env_2026-07-08.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-08.json)은 `KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED=true`를 포함한다.
  - 유의: code-improvement workorder의 rising_missed 관련 order 5건은 모두 `attach_existing_family`, runtime_effect=`false`, allowed_runtime_apply=`false`이며, forced scout 손익 자체는 runtime threshold/order/provider/cap/bot 변경 근거로 사용하지 않는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0708] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-07-08`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-07.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-07.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, persistent_operator_overrides_2026_06_26가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0708] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-07-08`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-07-07.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-07.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [x] `[IntradaySourceQualityGateCheck0708] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-07-08`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-07-08.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-08.jsonl), [threshold_events_2026-07-08.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-08.jsonl), [observation_source_quality_audit_2026-07-08.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-08.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-07-08 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.
  - 실행 결과: `hard_block_requires_producer_fix`
  - 근거: `observation_source_quality_audit_2026-07-08.json` generated_at=`2026-07-08T14:22:13+09:00`, status=`fail`, hard_blocking_contract_gap_count=`3`, hard_blocking_excluded_row_count=`3`, raw_row_exclusion_applied=`true`, tuning_input_allowed=`false`, blocked_reason=`blocked_contract_gap`, unknown_token_stage_count=`2`, review_warning_count=`2`.
  - 결손 stage: `early_accel_strong_bundle_recheck_evaluated`, `early_accel_strong_bundle_recheck_skipped`, `score65_74_recovery_probe_blocked`; review warning stage: `scalp_entry_action_decision_snapshot`, `real_weak_ai_micro_entry_block`.
  - row exclusion: [manifest.json](/home/ubuntu/KORStockScan/data/source_quality/raw_row_exclusion/2026-07-08_20260708T142200110744+0900/manifest.json). 장중 threshold/order/provider/bot 변경 없이 장후 `PostcloseSourceQualityGateReview0708`와 `CodeImprovementWorkorderReview`에서 producer-fix/workorder handoff를 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [x] `[PostcloseSourceQualityGateReview0708] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-07-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-07-08.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-08.json), [threshold_cycle_ev_2026-07-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-08.json), [code_improvement_workorder_2026-07-08.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-08.json), [threshold_cycle_postclose_verification_2026-07-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-08.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.
  - 실행 결과: `source_quality_gate_pass`. `observation_source_quality_audit_2026-07-08` status=`pass`, event_count=`105913`, hard_blocking_contract_gap_count=`0`, hard_blocking_excluded_row_count=`0`, unknown_token_stage_count=`0`, tuning_input_allowed=`true`.
  - 근거/유의: `threshold_cycle_ev_2026-07-08` source_quality_status=`pass`, source_quality_tuning_input_allowed=`true`; `threshold_cycle_postclose_verification_2026-07-08`는 status=`warning`이지만 source-quality hard block과 raw row exclusion은 pass이고 missing_required_artifacts/missing_downstream_links는 없다. quote_consistency 경고는 별도 source-field follow-up으로 유지하며 장후 runtime/env 변경 근거로 쓰지 않는다.

- [x] `[ThresholdDailyEVReport0708] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-07-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-08.json), [runtime_approval_summary_2026-07-08.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-07-08.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.
  - 실행 결과: daily EV 산출물은 생성됐지만 postclose runtime 반영은 보류. `threshold_cycle_ev_2026-07-08` status=`warning`, source_quality_status=`pass`, real_sample=`119`, sim_sample=`110`, real_sample_ready=`true`, primary_verdict=`real_primary_evidence_present`, live_auto_ready_count=`0`, runtime_effect=`false`.
  - 근거/유의: lifecycle_bucket_discovery selected_count=`1`, sim_auto_positive_ev_count=`2`, sim_auto_approved_count=`0`; swing sim 후보는 계속 관찰 대상이다. 다음 장전 입력은 source-quality pass와 selected runtime family provenance 확인용으로만 사용하고, live-auto ready가 0인 항목은 hold_sample/freeze로 유지한다.

- [x] `[CautionWeakLiquidityBadEntryReview0708] CAUTION weak-liquidity 진입의 bad-entry/post-sell 귀속 확인` (`Due: 2026-07-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-07-08.jsonl.gz](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-08.jsonl.gz), [pipeline_events_2026-07-08_20260708_201006.jsonl.gz](/home/ubuntu/KORStockScan/data/threshold_cycle/snapshots/pipeline_events_2026-07-08_20260708_201006.jsonl.gz), [threshold_cycle_ev_2026-07-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-08.json), [lifecycle_decision_matrix_2026-07-08.json](/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-07-08.json), [code_improvement_workorder_2026-07-08.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-08.json)
  - 판정 기준: 장중 raw 기준 `latency_state=CAUTION`, `entry_price_gap_profile=weak_liquidity_wide_spread`, `liquidity_guard_reason=liquidity_not_available`, `entry_split_order_policy_mode=post_submit_tick_band_seed`로 실제 제출된 record가 post-sell 결과와 join되어 bad-entry, entry-quality, LDM submit/entry bucket, code-improvement workorder 중 하나 이상에 표면화됐는지 확인한다. 08:31 KST 현재 raw 표본은 아이패밀리에스씨(114840, record_id=`15964`, hard stop `-5.39%`)와 잇츠한불(226320, record_id=`15969`, soft stop `-4.32%`) 2건이다.
  - 금지: 이 daily-only 손실 표본만으로 hard stop 완화, broker/order guard 완화, stale quote bypass, provider/bot/cap 변경, intraday threshold mutation, real execution quality approval을 열지 않는다.
  - 다음 액션: `post_sell_joined_and_workorder_visible`, `ldm_bucket_visible_hold_sample`, `source_quality_gap_blocks_join`, `needs_producer_patch_for_liquidity_unknown_join`, `defer_until_postclose_artifact` 중 하나로 닫는다.
  - 실행 결과: `post_sell_joined_and_workorder_visible`. record_id=`15964` 아이패밀리에스씨는 latency_state=`CAUTION`, entry_price_gap_profile=`weak_liquidity_wide_spread`, liquidity_guard_reason=`liquidity_not_available`, entry_split_order_policy_mode=`post_submit_tick_band_seed`, post-sell profit_rate=`-5.39`, exit_rule=`scalp_hard_stop_pct`로 join됐다. record_id=`15969` 잇츠한불도 같은 진입 특성으로 post-sell profit_rate=`-4.32`, exit_rule=`scalp_soft_stop_pct`로 join됐다.
  - 근거/유의: LDM submit 단계에 actual_order_submitted=`true`/broker_order_submitted=`true`로 표면화됐고, `code_improvement_workorder_2026-07-08`에는 bad-entry/liquidity 관련 기존 family handoff가 보인다. daily-only 2건 손실 표본이므로 hard stop, broker guard, provider, bot, cap, threshold는 변경하지 않는다.

- [x] `[HumanInterventionSummary0708] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-07-08`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-07-08.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-07-08.json), [threshold_cycle_ev_2026-07-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-08.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.
  - 실행 결과: 사용자 즉시 승인/개입 대상 없음. `runtime_approval_summary_2026-07-08` runtime_mutation_allowed=`false`, panic_approval_requested=`0`, swing_requested=`0`, swing_approved=`0`.
  - 근거/유의: `panic_entry_freeze_guard`는 hold_sample 및 approval contract missing, `panic_buy_runner_tp_canary`는 freeze 및 source-quality blocker/approval contract missing 상태다. 둘 다 observe/report-only로 유지하며 env 파일 직접 수정, provider/bot/cap/order guard 변경, 수동 승인 생성은 하지 않는다.

- [x] `[CodeImprovementWorkorderReview0708] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-07-08`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-07-08.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-08.md), [code_improvement_workorder_2026-07-08.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-08.json)
  - 판정 기준: selected_order_count와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.
  - 실행 결과: `keep_visible_by_design` 및 `already_implemented` 혼합으로 종료. `code_improvement_workorder_2026-07-08` source_order_count=`147`, selected_order_count=`106`, selected_implement_now_route_count=`0`, selected_unimplemented_runtime_effect_false_count=`0`, repeat_unresolved_escalation_count=`0`, repeat_unresolved_structural_blocker_count=`0`.
  - 근거/유의: selected route는 existing_family 중심이며 runtime_effect=false handoff가 유지된다. 오늘 장후 체크리스트 실행만으로 추가 repo 구현은 열지 않는다.

- [x] `[LifecycleQuietGapReview0708] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-07-08`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-07-08.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-08.json), [runtime_apply_gap_audit_2026-07-08.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-08.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count, rollup_required_count, sim_live_connected_quiet_gap_count, observation_source_quality_warning_count, quiet_gap_type_counts를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.
  - 실행 결과: `rollup_only` 및 `defer_until_more_sample`. `runtime_apply_gap_audit_2026-07-08` status=`pass`, candidate_count=`702`, critical_failure_count=`0`, quiet_gap_count=`419`, quiet_gap_rollup_count=`419`, codex_directive_count=`0`, retry_queue_count=`0`.
  - 근거/유의: low AI-review coverage와 source-dimension gap은 source-only rollup/coverage 보강 대상으로 남고, actionable unknown gap과 Codex directive는 없다. quiet gap은 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.

- [x] `[AutomationTriggerDecisionSummary0708] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-07-08`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-07-08.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-07-08.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [threshold_cycle_postclose_cron.log](/home/ubuntu/KORStockScan/logs/threshold_cycle_postclose_cron.log)
  - 판정 기준: trigger decision summary의 total_steps, run_count, skip_count, source_missing_count, force_override_count, run_steps_sample, skip_steps_sample, top_reasons를 확인하고 wrapper 로그의 start/done/skip marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.
  - 실행 결과: `trigger_contract_pass`. `automation_chain_trigger_decision_2026-07-08` total_steps=`16`, run_count=`16`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`.
  - 근거/유의: wrapper log에 `2026-07-08T20:10:01+0900` start marker와 `2026-07-08T20:47:00+0900` done marker가 있고, 오늘 skip marker 대조 대상은 없다. all-run은 output/upstream/source missing 이유에 의한 정상 run 판단이며 PREOPEN apply나 runtime/env 변경 근거로 쓰지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-07-08 15:46:40`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-07-08.md`
- `Trade Review`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
