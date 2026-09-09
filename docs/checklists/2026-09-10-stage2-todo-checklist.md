# 2026-09-10 Stage2 To-Do Checklist

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

## 별도 사용자 승인 적용 확인

- [ ] `[WidgetEpisodeApprovedNextDayExecution0910] 9/9 후속 승인 추천의 9/10 정책·기동·자연 소비 확인` (`Due: 2026-09-10`, `Slot: PREOPEN`, `TimeWindow: 08:40~09:00`, `Track: RuntimeStability`)
  - 9/9 23:43 준비 receipt: [승인 successor21행](../audit-reports/2026-09-09-widget-episode-approved-successor-ledger.json)은 canonical72행의 부분집합이다. low-price5추천 검증·기존numeric1변경/기존1재확인/신규3, catalog59·quarantine3·10주×2leg. 신규6timer NEXT9/10(롯데오전09:15/09:19,롯데오후14:15/14:19,TYM오전후반09:55/09:59), 현재거래service3개PID0/inactive.07:32 기존symbol-owner 자동publisher가 새19종목 dated authority를 읽고 이후 각preflight가 당일정책을 생성한다. 위젯080220은9/10정책verified이며3개holdout실패는미선정. 미래정책/PID/자연실현은아직미수용, 현재보유/target변경없음.
  - Source: [9/9 승인 복구 리뷰](../audit-reports/2026-09-09-postclose-authorized-recovery-review.md), [9/9 장후 원본 대사](../audit-reports/2026-09-09-postclose-monitoring-review.md).
  - 승인: 9/9 22:50 재개 시 사용자가 widget/episode 추천 구현 및 내일 실행을 명시 승인했다. source9/9 native ID·실제 변경 축·effective9/10 정책/hash·rollback·기존 timer/loader에 결속된 검증 완료 대상만 적용한다. 승인 이전 source gap/reject/research-watch를 무조건 선정하지 않는다.
  - Acceptance: 승인 ledger 전수 disposition→9/10 exact policy/preflight/설치 trigger→현재 process load receipt→원래 유효 window의 신호/valid-empty·독립 custody/terminal/비용을 단계별 대사한다. 예정 전 기동·현재 주문·기존 target/custody 변경·수량/guard 완화는 승인 범위가 아니다. 자연 receipt 전은 OPEN이며 경제성·future window는 기존 owner와 이력을 보존한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-09-09", "sources": {"automation_chain_trigger_decision": {"sha256": "ed1d6e0023424d0df9e1a5de214e54cd145228131fface1b95977543800a739c"}, "code_improvement_workorder": {"sha256": "7e0d3fca903bcca14f3883b19e172006cb3ee510d12587a28a539047d45df11a"}, "disposition_evidence_0_0": {"sha256": "b014432bf596dd12f15ddee7ffa068be88ce0ac048a113cddd3ed6c5411782c7"}, "disposition_evidence_10_0": {"sha256": "b014432bf596dd12f15ddee7ffa068be88ce0ac048a113cddd3ed6c5411782c7"}, "disposition_evidence_11_0": {"sha256": "b014432bf596dd12f15ddee7ffa068be88ce0ac048a113cddd3ed6c5411782c7"}, "disposition_evidence_1_0": {"sha256": "b014432bf596dd12f15ddee7ffa068be88ce0ac048a113cddd3ed6c5411782c7"}, "disposition_evidence_2_0": {"sha256": "b014432bf596dd12f15ddee7ffa068be88ce0ac048a113cddd3ed6c5411782c7"}, "disposition_evidence_3_0": {"sha256": "b014432bf596dd12f15ddee7ffa068be88ce0ac048a113cddd3ed6c5411782c7"}, "disposition_evidence_4_0": {"sha256": "b014432bf596dd12f15ddee7ffa068be88ce0ac048a113cddd3ed6c5411782c7"}, "disposition_evidence_5_0": {"sha256": "b014432bf596dd12f15ddee7ffa068be88ce0ac048a113cddd3ed6c5411782c7"}, "disposition_evidence_6_0": {"sha256": "b014432bf596dd12f15ddee7ffa068be88ce0ac048a113cddd3ed6c5411782c7"}, "disposition_evidence_7_0": {"sha256": "b014432bf596dd12f15ddee7ffa068be88ce0ac048a113cddd3ed6c5411782c7"}, "disposition_evidence_8_0": {"sha256": "b014432bf596dd12f15ddee7ffa068be88ce0ac048a113cddd3ed6c5411782c7"}, "disposition_evidence_9_0": {"sha256": "b014432bf596dd12f15ddee7ffa068be88ce0ac048a113cddd3ed6c5411782c7"}, "entry_recheck_drought_controller": {"sha256": "89289b471453776668b111fc1b97044d2743fffe97a4888ec22dfe9108f1e7f1"}, "low_price_two_leg_expanded_candidate_research": {"sha256": "362b22217dd46da839ab9eb0795ee37e3e5aa438a1091532ea65ef4a906c16a5"}, "low_price_two_leg_tuning": {"sha256": "3289629411bcc83243aa79b0f26c8de585628ccab6b95b18498537fcb3026fef"}, "machine_entry_timing_tuning": {"sha256": "dcefa4684e0d008a90cbab0e0ef6452988c39b734608ed5620aafd6ee952c413"}, "machine_microstructure_attribution": {"sha256": "b5068924d29491da163a469da05b8634b1528ee5249723012e103d13999e1db5"}, "machine_microstructure_policy_approval": {"sha256": "68039dc37eed3883260e3462acd9b38a21f7d8e904b80feec6f000aeb6330ba6"}, "main_ai_quality_r0_r3": {"sha256": "1dd1fe5dedfbab7c53fd3b712fa0fa9c2ca7ffb832fe41bc45d9aadc9d2e2aa6"}, "postclose_recommendation_dispositions": {"sha256": "0887c3eb594b16fca1693c93bef59da2efd3b1c56805e534e939ae60a847fa54"}, "preopen_apply_plan": {"sha256": "02d63907fb54d420e0cbd9c8870fcd3f48966a6073cac70dd7fdad97e4cc28a2"}, "preopen_pid_verification": {"sha256": "75cbaa6b99b2ff84ee85e5cbdc776e8db99958e50e7fe5a1b10d4735714b06fb"}, "preopen_runtime_manifest": {"sha256": "a5f800eec8a17e3024e771bdb3e25d4238f35c4ea6e0aceac679da4120892129"}, "rising_missed_scout_workorder": {"sha256": "ba7b882d065ef45c28aff754f15784729f134100f25fb667c4dd2f48ffbc4cfe"}, "runtime_apply_gap_audit": {"sha256": "6c1ea2969c1dd149a20f11043c8cc55329a07c3b7beaafdf0576e2d607e2e2d6"}, "samsung_machine_entry_tuning": {"sha256": "132a0bec5de494ee35d1ab8b8072cbf954f58ced6e25085304d65b2213239d3d"}, "threshold_cycle_ev": {"sha256": "4a0d73ae9aab9c91a32fe960e2c08d372d2efcae91aa676da72839bd61f4d526"}, "tuning_performance_control_tower": {"sha256": "20b9ca37e262bc72a5415b4cab7cd0ac379b75f46712267194ab0c0b6a675b11"}, "widget_advisory_calibration": {"sha256": "3cfdbd6ea83ba4450ab2045dd6827982f9195cde98e1ff938d432e80609c501e"}, "widget_auto_trade_policy_calibration": {"sha256": "de0a65a2344665c69977eb295e633403aa5cfe6fdd256116d01cba159e7d8d09"}, "widget_collector_expansion_recommendation": {"sha256": "644bf381dd50ebc1f93d8bbced94d45bd7e7408773983e5866e45eb16b087345"}, "widget_symbol_runtime_policy_apply": {"sha256": "9ed61486a6585b498c50414aa3144fbb1ef6f20f1842a5525a0cd95f5bc8127d"}, "widget_symbol_signal_policy_research": {"sha256": "4e74812acb225e56e1c1e69813aaa249269a446a873422482c708609df2ffd81"}}} -->
<!-- POSTCLOSE_RECOMMENDATION_INTAKE_START -->
## 추천 전수 전달 대사

- source-date: `2026-09-09`; status: `warning`
- native rows SHA256: `1d01fac2e3773938fb4f4961b5f0a187ddcd6c0eb5591f273a79b2a0da398210`
- counts: `{"already_implemented_verified_eligible": 0, "already_implemented_verified_nonrequest": 0, "blocked_external_dependency": 0, "blocked_external_dependency_nonrequest": 0, "blocked_missing_evidence": 11, "blocked_missing_evidence_nonrequest": 3, "deferred": 32, "eligible_actionable_open": 0, "eligible_runtime_effect_false_total": 11, "implement_now_unaccounted_count": 0, "implementation_requested_total": 11, "implemented_pass1": 0, "implemented_pass2": 0, "intake_total": 72, "intake_unaccounted_count": 0, "invalid_or_missing_authority_nonrequest": 0, "invalid_or_missing_authority_total": 0, "nonimplementation_total": 61, "observed_no_patch": 23, "rejected": 3, "user_authority_nonrequest": 0, "user_authority_total": 0}`
- dispositions: `{"blocked_missing_evidence": 14, "deferred": 32, "observed_no_patch": 23, "rejected": 3}`
- 운영 terminal, 구현 fixed-point, PREOPEN 선택, PID 소비, 경제성은 별도 상태다.

| Owner | Native recommendation dispositions |
| --- | --- |
| low_price_two_leg_expanded_candidate_research | `{"blocked_missing_evidence": 2, "deferred": 7}` |
| machine_microstructure_attribution | `{"observed_no_patch": 1}` |
| main | `{"blocked_missing_evidence": 11, "deferred": 18, "observed_no_patch": 22}` |
| widget_collector_expansion_recommendation | `{"deferred": 7}` |
| widget_symbol_signal_policy_research | `{"blocked_missing_evidence": 1, "rejected": 3}` |
<!-- POSTCLOSE_RECOMMENDATION_INTAKE_END -->

## 자동 생성 체크리스트 (`2026-09-09` postclose -> `2026-09-10`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (07:45~09:00)

- [ ] `[MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0910] micro observer 저장공간·연속수집 source gap 복구 확인` (`Due: 2026-09-10`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:45`, `Track: RuntimeStability`)
  - 00:36 source9/9 복구 handoff: [복구·재발 방지 리뷰](../audit-reports/2026-09-10-postclose-0909-recovery-review.md)의 closed entry window18개/eligible0은 과거 격리다. 오늘 PREOPEN actual process/epoch/0B·0D exact route receipt, 장중 원 신호 전후 -30~+6초 창, through-close canary를 새 source로 확인한다. SOR를 NXT로 대용하거나 과거 unverified epoch를 승인하지 않는다. 원천이 없으면 첫 source/route gap과 권한 범위를 남기고 반복 replay로 성공 처리하지 않는다. 현재 not_yet_due; 수리 코드 PASS와 자연 수집·비용 후 EV는 별도다.
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-09.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-09.json)
  - 판정 기준: workorder `main-ai-gap-a7c7bc7b22a14cd93c8c30e9`의 owner=`MicroReversionForwardCollectorContinuity`, reason_codes=`row_exclusion_required, past_market_row_missing=33`를 source-only producer 보완으로 닫는다. 장전 free bytes가 writer low-disk watermark를 충분히 상회하는지 확인하고, 부족하면 실주문과 무관한 closed-date verified compression만 실행한 뒤 observer canary를 재검증한다.
  - 완료 조건: exact-date canary remains pass or row-exclusion-only through close; later clean windows continue collecting; provider replay remains held until queue-loss scope has an exact exclusion receipt or the next clean date
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[ThresholdEnvAutoApplyPreopen0910] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-09-10`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - 07:46:53 사용자 승인 결함 복구: [recheck evidence 수리](../audit-reports/2026-09-10-recheck-preopen-evidence-repair.md). hash-bound null 제거 결함 수리/484 tests PASS 뒤 오늘 PREOPEN producer만 재생성, handoff PASS. recheck는 정상 OFF 정책 채택(9/7 schema5 이력 부족 유지), 활성18개 불변. 07:55 예정 PID/WS 소비와 기존 장중 acceptance는 별도이며 OPEN 유지.
  - source9/9 자정 복구의 다음 consumer: 기존 `EntryRecheckNaturalAttribution0907`의 exact source/scope 및 current controller→자동 PREOPEN 선택→PID receipt를 대사한다. 운영 RED 복구는 accepted submit0이나 비용 미대사를 해소한 것이 아니다. 기존 승인 family/guard만 소비하고 수동 env·추가 경제성 veto를 만들지 않는다.
  - Source: [threshold_cycle_ev_2026-09-09.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-09.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0910] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-09-10`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-09-09.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-09-09.json), [code_improvement_workorder_2026-09-09.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-09.json), [threshold_apply_2026-09-10.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-09-10.json), [threshold_runtime_env_2026-09-10.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-10.json), [threshold_runtime_env_verify_2026-09-10.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-10.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`2`, forced_scout_with_post_sell_count=`0`, post_sell_join_coverage_pct=`0`, outcome_coverage_state=`no_closed_outcome`, profitable_forced_scout_count=`0`, loss_or_flat_forced_scout_count=`0`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0910] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-09-10`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - 동시호가 후속: [장중 §4.2.1](../intraday-monitoring-task-instructions.md#421-동시호가nxt-휴장-구간의-수신-기대)에 따라08:50~09:00 무수신(확인된 NXT-only09:00:30까지)을 장애로 세지 않았는지 #89 다음 자연 output의 `expected_market_quiet`/원 age/route/as-of로 대사한다.09:00 KRX·09:00:30 NXT 재개 후 현재 수신/기존 SLA와09:05~09:20 소비를 별도 확인한다. 원천/연결/저장 오류는 유지하며 이번 코드 검증을 기존 PID reload 완료로 표시하지 않는다. 실행 중 WS 변경은 별도 승인 전 재기동하지 않는다.
  - Source: [threshold_cycle_ev_2026-09-09.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-09.json)
  - 전일 postclose candidate_selected_families=score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, post_probe_winner_recovery, entry_opportunity_recheck_runtime, holding_decision_context_v1, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0910] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-09-10`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-09-09.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-09.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0910] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-09-10`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-09-10.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-09-10.jsonl), [threshold_events_2026-09-10.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-09-10.jsonl), [observation_source_quality_audit_2026-09-10.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-10.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-09-10 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (16:25~21:55)

- [ ] `[ThresholdDailyEVReport0910] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-09-10`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-09-09.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-09-09.json), [threshold_cycle_ev_2026-09-09.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-09.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0910] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-09-10`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-09.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-09.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[MainAIQualitySourceGapMainAIMicroExactEconomicIntersectionRepair0910] main AI micro exact 경제성 교집합 source gap 복구 확인` (`Due: 2026-09-10`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-09.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-09.json)
  - 판정 기준: workorder `main-ai-gap-b3edbf4b953cb345d37c90d7`의 owner=`MainAIMicroExactEconomicIntersectionRepair`, reason_codes=`paired_decision_quality_eligible=24, net_economic_eligible=0, current_exact_source_eligible=0`를 source-only producer 보완으로 닫는다. 동일 primary trace의 paired/mature/sidecar/net-economic 교집합과 bridge/source-bundle parent census를 대사한다. 비용·원천 결손을 0 또는 대체 parent로 보간하지 않는다.
  - 완료 조건: bridge current exact trace census equals the source-bundle eligible parent census; a parent is materialized only when the same primary trace is paired, mature, sidecar-valid, and net-economic eligible
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[CodeImprovementWorkorderReview0910] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-09-10`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-09-09.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-09-09.md), [code_improvement_workorder_2026-09-09.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-09.json)
  - 판정 기준: selected_order_count=33와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[MachineLifecycleTurnoverObjectiveFollowup0910] 위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인` (`Due: 2026-09-10`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_policy_approval_postclose_2026-09-09.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_2026-09-09.json), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 판정 기준: 승인 후보 수와 무관하게 `followup_required=true`인 미완료 목적 항목 `machine_lifecycle_turnover_policy_research_v1`(status=`EVIDENCE_ACCUMULATING`, next_action=`repair_excluded_source_report_contracts_and_rerun`)의 상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.
  - 상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, `EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. `CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.
  - 권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[AutomationTriggerDecisionSummary0910] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-09-10`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - 재발 방지 자연 확인: source9/9 자정 복구에서 storage CLI의 lazy dependency 안내가 JSON stdout을 오염시킨 결함을 stderr 분리로 보완했다(전체711 tests PASS). 오늘 정상 예약 finalization의 storage receipt strict JSON/schema/hash→cleanup→7개 detector terminal을 확인한다. 과거 source9/9의 explicit 복구/부분 generic receipt 재사용을 오늘 자연 실행 성공으로 재라벨링하지 않는다. [복구 기록](../audit-reports/2026-09-10-postclose-0909-recovery-review.md).
  - Source: [automation_chain_trigger_decision_2026-09-09.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-09-09.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`6`, skip_count=`0`, source_missing_count=`5`, force_override_count=`0`, run_steps_sample=`pattern_lab_currentness_audit, pattern_lab_ai_review, observation_source_quality_audit, pattern_lab_propagation_audit, runtime_apply_gap_audit`, skip_steps_sample=`-`, top_reasons=`disabled_by_runtime_policy:8, output_missing_or_unreadable:5, source_missing_or_unreadable:5, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

- [ ] `[PostcloseSourceQualityGateReview0910] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-09-10`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-09-10.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-10.json), [threshold_cycle_ev_2026-09-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-10.json), [code_improvement_workorder_2026-09-10.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-10.json), [threshold_cycle_postclose_verification_2026-09-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-09-10.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
