# 2026-09-15 Stage2 To-Do Checklist

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
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-09-14", "sources": {"automation_chain_trigger_decision": {"sha256": "6765a6cf89c116598aa8b57d24e202490727fff12e7ad0572ff0c8d338511f90"}, "code_improvement_workorder": {"sha256": "dcb5635445a85a2377f356113c96c2f9fba02adde3a3da628bdcc80a124e4953"}, "conversion_lane": {"sha256": "2bb74349c97d735a5625203e3ad0385553c92b6171b350136bf86266affb37f9"}, "disposition_evidence_0_0": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_0_1": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_0_2": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_10_0": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_10_1": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_10_2": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_1_0": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_1_1": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_1_2": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_2_0": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_2_1": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_2_2": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_3_0": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_3_1": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_3_2": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_4_0": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_4_1": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_4_2": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_5_0": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_5_1": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_5_2": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_6_0": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_6_1": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_6_2": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_7_0": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_7_1": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_7_2": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_8_0": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_8_1": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_8_2": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_9_0": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_9_1": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "disposition_evidence_9_2": {"sha256": "8b789e62d62f51625946339eb6842c872fa5c7269f71e6f8d14ae7d09701cba7"}, "entry_recheck_drought_controller": {"sha256": "8b14f732352964fc3b6afde6038485d0c184a731d425ad4b7b3fd95b8992aa04"}, "key_lineage_ledger": {"sha256": "4f7ffd02af88da4b3c3abb63cf7bfa23b0789f34aaca91d02a1f9b41664f8023"}, "low_price_two_leg_expanded_candidate_research": {"sha256": "f6cdda9ccfaa084dc11fb408a3e1d642b9065c0333626688c6a0de6649927587"}, "low_price_two_leg_tuning": {"sha256": "1f20ff6672ce69c3231497fba8444f747039fa8d82800b294e12ab2debe247a2"}, "machine_entry_timing_tuning": {"sha256": "6e1ddd254dcc29668c73d7da6fd9880d8cfa5f4741a7c14ac6bd0a90a61bef2d"}, "machine_microstructure_attribution": {"sha256": "1b099d273bdbf0f98879cca5cc06997e7e8399627cf2312ca63f5c0690d204cf"}, "machine_microstructure_policy_approval": {"sha256": "34a0f211897e804d15d5b6d92e3931a6080263badf4cf97d4891071e82ee59f6"}, "main_ai_quality_r0_r3": {"sha256": "1517ea0a1c1858427e3ffb04fd2d556499be99c2778982d6771c97ad96c20b67"}, "postclose_recommendation_dispositions": {"sha256": "4883ae9168b38a4c2339c3ac373df31aea13518ee2722e8a31c86bf302ad1143"}, "preopen_apply_plan": {"sha256": "5611719d8086a04c79909e8ef382938e59fe3484ad94cf034f7fae44c0e21915"}, "preopen_pid_verification": {"sha256": "2d7b9f90c26f47ddfe34f36d09589bce905180774d321ea9de07737dcfe81bef"}, "preopen_runtime_manifest": {"sha256": "04408685ab18c633192ba01d8f222e76f29cb9234e59318f8748d1c7cbaf1b7b"}, "rising_missed_scout_workorder": {"sha256": "f57290dca08e9f20d7b2d84f3a449ce6f494f3de30c626fcc40b066d17ca3748"}, "runtime_apply_gap_audit": {"sha256": "f323f0c1e7a3dc8a57ec0745a855fa4b69211b5e4390d153d7d9c2da98435def"}, "samsung_machine_entry_tuning": {"sha256": "d78152db197c98f068ae337d29a1c62490ca218413e2f92fa7716d9e818d0a89"}, "threshold_cycle_ev": {"sha256": "34585ecfa7b5512d6e8cd7ee45ac76137086dba27d7b897c93fb03c6ad81d36b"}, "tuning_performance_control_tower": {"sha256": "a8b526b607128556bc6e0fcf9342452c95820de6c5ed3a8c3701a09c54de0a52"}, "widget_advisory_calibration": {"sha256": "515ba1ebe9baa5b3ea573ea3278817045eeb056f8c063f1828e304c138ce7d93"}, "widget_auto_trade_policy_calibration": {"sha256": "9b3dbb276a9e508d7e3fda63e461b5634898436fae165fd9d3fce3b22b73f335"}, "widget_collector_expansion_recommendation": {"sha256": "f6a379b8616e5b0bbb055574441a1e1cf8a5155562cc8c91c9eee902c15cf458"}, "widget_symbol_runtime_policy_apply": {"sha256": "453e4b3d8ef176c3316ed3c9e50c9cb72c76795bd6ad40254d438d4c60a9fb82"}, "widget_symbol_signal_policy_research": {"sha256": "1509b72754123dea598a92e857f0377a5e737976355a34ff65e4ffae46c7f717"}}} -->
<!-- POSTCLOSE_RECOMMENDATION_INTAKE_START -->
## 추천 전수 전달 대사

- source-date: `2026-09-14`; status: `warning`
- native rows SHA256: `27ae1ac1496e3a83865a39c7ea162dbf9a98a33bfbf17ffcedf74a9052fdf508`
- counts: `{"already_implemented_verified_eligible": 11, "already_implemented_verified_nonrequest": 0, "blocked_external_dependency": 0, "blocked_external_dependency_nonrequest": 0, "blocked_missing_evidence": 3, "blocked_missing_evidence_nonrequest": 1, "deferred": 23, "eligible_actionable_open": 0, "eligible_runtime_effect_false_total": 14, "implement_now_unaccounted_count": 0, "implementation_requested_total": 14, "implemented_pass1": 0, "implemented_pass2": 0, "intake_total": 73, "intake_unaccounted_count": 0, "invalid_or_missing_authority_nonrequest": 0, "invalid_or_missing_authority_total": 0, "nonimplementation_total": 59, "observed_no_patch": 31, "rejected": 4, "user_authority_nonrequest": 0, "user_authority_total": 0}`
- dispositions: `{"already_implemented_verified": 11, "blocked_missing_evidence": 4, "deferred": 23, "observed_no_patch": 31, "rejected": 4}`
- 운영 terminal, 구현 fixed-point, PREOPEN 선택, PID 소비, 경제성은 별도 상태다.

| Owner | Native recommendation dispositions |
| --- | --- |
| low_price_two_leg_expanded_candidate_research | `{"blocked_missing_evidence": 1, "deferred": 4}` |
| machine_microstructure_attribution | `{"observed_no_patch": 1}` |
| main | `{"already_implemented_verified": 11, "blocked_missing_evidence": 3, "deferred": 13, "observed_no_patch": 30}` |
| widget_collector_expansion_recommendation | `{"deferred": 6}` |
| widget_symbol_signal_policy_research | `{"rejected": 4}` |
<!-- POSTCLOSE_RECOMMENDATION_INTAKE_END -->

## 자동 생성 체크리스트 (`2026-09-14` postclose -> `2026-09-15`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (07:45~09:00)

- [ ] `[MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0915] micro observer 저장공간·연속수집 source gap 복구 확인` (`Due: 2026-09-15`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:45`, `Track: RuntimeStability`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-14.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-14.json)
  - 판정 기준: workorder `main-ai-gap-6a4233860a318e9ec55e89e1`의 owner=`MicroReversionForwardCollectorContinuity`, reason_codes=`row_exclusion_required, past_market_row_missing=0`를 source-only producer 보완으로 닫는다. 장전 free bytes가 writer low-disk watermark를 충분히 상회하는지 확인하고, 부족하면 실주문과 무관한 closed-date verified compression만 실행한 뒤 observer canary를 재검증한다.
  - 완료 조건: exact-date canary remains pass or row-exclusion-only through close; later clean windows continue collecting; provider replay remains held until queue-loss scope has an exact exclusion receipt or the next clean date
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[ThresholdEnvAutoApplyPreopen0915] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-09-15`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-14.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0915] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-09-15`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-09-14.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-09-14.json), [code_improvement_workorder_2026-09-14.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-14.json), [threshold_apply_2026-09-15.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-09-15.json), [threshold_runtime_env_2026-09-15.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-15.json), [threshold_runtime_env_verify_2026-09-15.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-15.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`2`, forced_scout_with_post_sell_count=`0`, post_sell_join_coverage_pct=`0`, outcome_coverage_state=`no_closed_outcome`, profitable_forced_scout_count=`0`, loss_or_flat_forced_scout_count=`0`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0915] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-09-15`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-14.json)
  - 전일 postclose candidate_selected_families=entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, post_probe_winner_recovery, position_sizing_dynamic_formula, holding_decision_context_v1, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 위젯 release 결속: `widget_startup_runtime_receipt_v2`의 process identity·`release_root`와 `korstockscan-widget-signal-auto-trader.service`의 현재 MainPID·WorkingDirectory를 대사한다. 07:58~08:05는 bounded wait이며 이후 missing/legacy receipt 또는 root 불일치는 `unit_process_release_mismatch`로 실패한다. unit 설정만 최신인 상태를 실제 PID 소비로 인정하지 않는다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0915] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-09-15`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-09-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-14.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0915] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-09-15`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-09-15.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-09-15.jsonl), [threshold_events_2026-09-15.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-09-15.jsonl), [observation_source_quality_audit_2026-09-15.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-15.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-09-15 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (16:25~21:55)

- [ ] `[ThresholdDailyEVReport0915] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-09-15`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-09-14.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-09-14.json), [threshold_cycle_ev_2026-09-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-14.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[EntryAxesClosedLoopPostclose0915] 최초 진입 가격·수량+multi-leg 장후 폐루프 및 다음 장전 정책 발행 확인` (`Due: 2026-09-15`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~21:55`, `Track: ScalpingLogic`)
  - Source: [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [entry_split_order_plan.py](/home/ubuntu/KORStockScan/src/engine/scalping/entry_split_order_plan.py), [threshold_cycle_ev_2026-09-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-15.json)
  - 판정 기준: 기계 가격 후보와 초기진입 전용 수량·multi-leg 동일-attempt 4-arm을 비용 차감 terminal 기준으로 평가한다. 조건 통과 시 `mechanistic_entry_price_policy`와 `entry_execution_sizing_policy`가 다음 KRX 거래일 날짜로 원자 발행되고, 미달이면 기존 기본 정책을 유지한 채 직접 blocker와 남은 표본을 기록해야 한다.
  - owner 경계: AI 가격 후보와 provider/model 선택을 금지하고, AVG_DOWN/PYRAMID action·price·execution-sizing 표본을 최초 진입 정책 승격 분모에 합치지 않는다. 결측 arm·비용·terminal은 0으로 보간하지 않는다.
  - 완료 조건: 장후 producer terminal, 정책 생성 또는 정당한 hold, artifact file/hash/source date/active date, `runtime_effect=false`인 PREOPEN handoff가 모두 설명된다. 장후 정책 발행을 다음날 PID 소비나 비용 후 실효성 완료로 표시하지 않는다.

- [ ] `[EntryAxesClosedLoopPreopen0916] 최초 진입 axis bundle·dated 정책 PREOPEN 및 PID 소비 확인` (`Due: 2026-09-16`, `Slot: PREOPEN`, `TimeWindow: 07:35~08:00`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [entry_execution_sizing_plan.py](/home/ubuntu/KORStockScan/src/engine/scalping/entry_execution_sizing_plan.py), [run_runtime_release.sh](/home/ubuntu/KORStockScan/deploy/run_runtime_release.sh)
  - 판정 기준: 7개 axis의 env key owner 중복이 0이고, B6은 policy 선택 없이 file/hash/date/consumer identity만 결속해야 한다. 생성된 dated 가격·통합 sizing 정책이 있으면 PREOPEN audit와 PID env가 동일해야 하며, 후보 미생성은 baseline 기동을 막지 않는다.
  - 완료 조건: 선택 release/commit, PREOPEN manifest·env·verify, 실제 main PID root/commit/env, 기계 가격 receipt와 atomic quantity+leg plan을 분리 확인한다. 필수 hash/date 불일치는 fail-closed하되 사용자 env 복사나 수동 정책 합성으로 우회하지 않는다.

- [ ] `[HumanInterventionSummary0915] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-09-15`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-14.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[MainAIQualitySourceGapMainAIMicroExactEconomicIntersectionRepair0915] main AI micro exact 경제성 교집합 source gap 복구 확인` (`Due: 2026-09-15`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-14.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-14.json)
  - 판정 기준: workorder `main-ai-gap-d4aa9884ba4bead0cc0d2c07`의 owner=`MainAIMicroExactEconomicIntersectionRepair`, reason_codes=`paired_decision_quality_eligible=2, net_economic_eligible=0, current_exact_source_eligible=0`를 source-only producer 보완으로 닫는다. 동일 primary trace의 paired/mature/sidecar/net-economic 교집합과 bridge/source-bundle parent census를 대사한다. 비용·원천 결손을 0 또는 대체 parent로 보간하지 않는다.
  - 완료 조건: bridge current exact trace census equals the source-bundle eligible parent census; a parent is materialized only when the same primary trace is paired, mature, sidecar-valid, and net-economic eligible
  - 구현 receipt (08:10 KST): actual lifecycle의 `entry|entry_ai|entry_decision`과 submit/fill trace 유일 교집합을 우선하도록 수리했고, micro bridge는 symbol·venue/session·route/epoch·decision timestamp·source bundle과 fixed-price 1초 창을 검증한다. 비용은 comparison/executable/broker 층으로 분리하고 결손을 보간하지 않는다. 테스트 검증은 완료하되 오늘 자연 `path_evaluable`·same-trace·비용 후 EV는 18:00 이후 이 owner에서 별도 확인한다.
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[MainAIQualitySourceGapRuntimeExecutionReceiptCustodyRepair0915] RuntimeExecutionReceiptCustodyRepair main lifecycle source gap 복구 확인` (`Due: 2026-09-15`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-14.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-14.json)
  - 판정 기준: workorder `main-ai-gap-bdadf6a9e6e61758b5624f9c`의 owner=`RuntimeExecutionReceiptCustodyRepair`, reason_codes=`pipeline_lifecycle_instrumentation_gap_count=2, real_submitted_lifecycle_count=3, broker_execution_unique_count=1`를 source-only producer 보완으로 닫는다. 공식 raw execution envelope의 order/execution identity를 합성 없이 검증하고 결손 lifecycle만 제외한 뒤 paired producer를 재검증한다.
  - 완료 조건: official raw execution envelope/order/execution identity is complete for each repair-required lifecycle or the affected row remains explicitly excluded; custody and order authority remain unchanged
  - 구현 receipt (08:10 KST): 동일 trace가 entry decision과 submit/fill에 함께 나타나는 실제 lifecycle을 한 번만 선택하는 계약과 선택 근거 census를 추가했다. order/execution identity·시세 경로·broker 비용의 오늘 자연 결속 여부는 아직 미도래이며, 결손이면 기존 exclusion reason을 유지한다.
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[CodeImprovementWorkorderReview0915] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-09-15`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-09-14.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-09-14.md), [code_improvement_workorder_2026-09-14.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-14.json)
  - 판정 기준: selected_order_count=31와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[MachineLifecycleTurnoverObjectiveFollowup0915] 위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인` (`Due: 2026-09-15`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_policy_approval_postclose_2026-09-14.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_2026-09-14.json), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 판정 기준: 승인 후보 수와 무관하게 `followup_required=true`인 미완료 목적 항목 `machine_lifecycle_turnover_policy_research_v1`(status=`EVIDENCE_ACCUMULATING`, next_action=`repair_excluded_source_report_contracts_and_rerun`)의 상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.
  - 상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, `EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. `CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.
  - 권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.
  - 구현 receipt (08:10 KST): widget signal 연구·low-price expanded 연구는 source/policy/cost fingerprint, machine attribution은 선언 source path의 size/mtime 세대와 producer code hash가 동일할 때만 exact-date heavy 계산을 재사용한다. source 변경 시 full recompute fixture를 통과했으며 오늘 21:15 자연 unit 시간·valid-empty/carry는 별도 확인한다.
  - 복구 receipt (23:26 KST): 겹치는 attribution window의 raw/normalized source object 공유 수리 뒤에도 512MiB 설치 상한에서 swap pressure가 재현되어, repository unit의 분석 전용 `MemoryMax`를 2GiB로 조정했다. host available memory·단일 service PID를 확인한 후 설치하고 동일 target-date terminal·peak를 재검증한다. 매매 process·정책·threshold·provider·broker 권한은 변경하지 않는다.

- [ ] `[AutomationTriggerDecisionSummary0915] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-09-15`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-09-14.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-09-14.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`6`, skip_count=`0`, source_missing_count=`5`, force_override_count=`0`, run_steps_sample=`pattern_lab_currentness_audit, pattern_lab_ai_review, observation_source_quality_audit, pattern_lab_propagation_audit, runtime_apply_gap_audit`, skip_steps_sample=`-`, top_reasons=`disabled_by_runtime_policy:8, output_missing_or_unreadable:5, source_missing_or_unreadable:5, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 구현 receipt (08:10 KST): main은 EV 2회·workorder 1회·core checklist/verifier만 소유하고, 늦은 source를 포함하는 tower→checklist→strict는 finalization summary-handoff로 단일화했다. 오늘 자연 wrapper와 finalization의 실제 실행 횟수·최신 source hash는 예정 시각 이후 검증한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 최종 generation: final runtime summary 뒤의 source-only trigger snapshot refresh가 checklist/strict verifier보다 먼저 있고, 초기 snapshot의 `source_missing`이 최종 상태로 남지 않는지 확인한다. refresh는 producer 실행·runtime apply·정책 변경 권한이 없으며 실패 시 prior snapshot과 strict verifier의 stale-link 판정을 분리해 기록한다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

- [ ] `[PostcloseSourceQualityGateReview0915] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-09-15`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-09-15.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-15.json), [threshold_cycle_ev_2026-09-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-15.json), [code_improvement_workorder_2026-09-15.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-15.json), [threshold_cycle_postclose_verification_2026-09-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-09-15.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
