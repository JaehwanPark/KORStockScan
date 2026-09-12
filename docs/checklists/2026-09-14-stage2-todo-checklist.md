# 2026-09-14 Stage2 To-Do Checklist

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
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-09-11", "sources": {"automation_chain_trigger_decision": {"sha256": "534e5f0cee8987996f6eb2247b283a0f090c48549d6156221527927d59ddd2a8"}, "code_improvement_workorder": {"sha256": "6aa56ca87c0f11b2b5c2ea14c1dfbfc16c8eac6a0ba425c4ea9af348bbde4df3"}, "disposition_evidence_0_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_10_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_11_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_12_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_13_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_14_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_15_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_16_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_17_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_18_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_19_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_1_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_20_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_21_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_22_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_23_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_24_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_25_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_26_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_2_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_3_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_4_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_5_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_6_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_7_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_8_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "disposition_evidence_9_0": {"sha256": "23fd4ff6de4ea9f91babecadd82bcd9082a55dbf0549d4a00d90ce9f99086f80"}, "entry_recheck_drought_controller": {"sha256": "866585ebbac1f4290ae3826c066188e2f2d839d055c8e0d17ceef9ce9c359758"}, "low_price_two_leg_expanded_candidate_research": {"sha256": "13f9b81c4c1d1407563b2180f3f4fe00d1f9d03a9fe3facc82552d6b1bc52f0e"}, "low_price_two_leg_tuning": {"sha256": "69387b14898b98d04e585ce244ddfe691e72df4fbe393635be3b2a3553bf01d7"}, "machine_entry_timing_tuning": {"sha256": "6286d273b8e2d5f79dc75e80eb3a02c0c2858c28d9e45a0aa75476fa0222c9b2"}, "machine_microstructure_attribution": {"sha256": "c6abd243f732f8d301e63a5d4ec4a772d4eb96655ae995eb63a10b11c6d1e3b4"}, "machine_microstructure_policy_approval": {"sha256": "3e7667d78ac7405f5ae513913c1aa48ddfbdd19f241ae58cae1d634de44decca"}, "main_ai_quality_r0_r3": {"sha256": "8bd69d677ec7d28f30d1f3f9e68d1b1e8b4602a20d06756d608b2fa61570ac06"}, "postclose_recommendation_dispositions": {"sha256": "c48c8e583f26357cf421f35071f9d368f349298aeca605de321681184d053b22"}, "preopen_apply_plan": {"sha256": "1b494a8f03d75d3a3d1c578b464a8b63c1e6aa39d24c44785fd25c97b7eda5b3"}, "preopen_pid_verification": {"sha256": "2bd07d373530a2f7c234687eaae8b17fe0bfa56a53ec33379b95b75bfc8eaa02"}, "preopen_runtime_manifest": {"sha256": "6e8706a7a407281c66b64618c7c3ebcf146e2bc7c31a8c9d16a621da94663112"}, "rising_missed_scout_workorder": {"sha256": "8b0e21ae255027fd25f79e47e6e4357ec4caaa51dfd0a869749f3aafce0cd6a7"}, "runtime_apply_gap_audit": {"sha256": "0c6e079a333623c4bfed81ad53ae895745b8329490749883c2acf903e8de4a8e"}, "samsung_machine_entry_tuning": {"sha256": "4fea3955cc4a0b3bded0e61d489b22bee298653e6dce0e3a305b6a7dff77f1ab"}, "threshold_cycle_ev": {"sha256": "56a0592dd5f83a970773739d5ce8e8117629d23b2cf4a4f518e5df6d929f95fc"}, "tuning_performance_control_tower": {"sha256": "d7c9ccbb7e908ca0ca09d4eddd550e8184f2d9cc4895b20e4bea49160ea33ca1"}, "widget_advisory_calibration": {"sha256": "34bb01e3fe4a38998b2a601bd105d554021fe075de00a7593eb1e847f4e3dcef"}, "widget_auto_trade_policy_calibration": {"sha256": "30bcc8414e50bd72c06b18473bb21fa85999484175d3003ee62585892233689c"}, "widget_collector_expansion_recommendation": {"sha256": "70c95f5f5a2adb490692593a64e7f07e37c5770a85d4b33bd506d9065b64749b"}, "widget_symbol_runtime_policy_apply": {"sha256": "3d8909a4ad1d2592f071122c210a6eb7df0de1de1705eeb291930e9c2839b5cf"}, "widget_symbol_signal_policy_research": {"sha256": "6d83cba7a3ab40164c36939cc333ccc7e28d711d8aa19da7dadfb58de711dc03"}}} -->
<!-- POSTCLOSE_RECOMMENDATION_INTAKE_START -->
## 추천 전수 전달 대사

- source-date: `2026-09-11`; status: `warning`
- native rows SHA256: `08e0f7a3d82c27487c439e5de34c3be101a5cc7ef62f88d23401740a9c51eeb1`
- counts: `{"already_implemented_verified_eligible": 0, "already_implemented_verified_nonrequest": 0, "blocked_external_dependency": 0, "blocked_external_dependency_nonrequest": 0, "blocked_missing_evidence": 27, "blocked_missing_evidence_nonrequest": 1, "deferred": 21, "eligible_actionable_open": 0, "eligible_runtime_effect_false_total": 27, "implement_now_unaccounted_count": 0, "implementation_requested_total": 27, "implemented_pass1": 0, "implemented_pass2": 0, "intake_total": 79, "intake_unaccounted_count": 0, "invalid_or_missing_authority_nonrequest": 0, "invalid_or_missing_authority_total": 0, "nonimplementation_total": 52, "observed_no_patch": 26, "rejected": 4, "user_authority_nonrequest": 0, "user_authority_total": 0}`
- dispositions: `{"blocked_missing_evidence": 28, "deferred": 21, "observed_no_patch": 26, "rejected": 4}`
- 운영 terminal, 구현 fixed-point, PREOPEN 선택, PID 소비, 경제성은 별도 상태다.

| Owner | Native recommendation dispositions |
| --- | --- |
| low_price_two_leg_expanded_candidate_research | `{"blocked_missing_evidence": 1, "deferred": 4}` |
| machine_microstructure_attribution | `{"observed_no_patch": 1}` |
| main | `{"blocked_missing_evidence": 27, "deferred": 7, "observed_no_patch": 25}` |
| widget_collector_expansion_recommendation | `{"deferred": 10}` |
| widget_symbol_signal_policy_research | `{"rejected": 4}` |
<!-- POSTCLOSE_RECOMMENDATION_INTAKE_END -->

## 자동 생성 체크리스트 (`2026-09-11` postclose -> `2026-09-14`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (07:45~09:00)

- [ ] `[MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0914] micro observer 저장공간·연속수집 source gap 복구 확인` (`Due: 2026-09-14`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:45`, `Track: RuntimeStability`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-11.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-11.json)
  - 판정 기준: workorder `main-ai-gap-8652a97fc58e4e15cfbdae6d`의 owner=`MicroReversionForwardCollectorContinuity`, reason_codes=`row_exclusion_required, past_market_row_missing=0`를 source-only producer 보완으로 닫는다. 장전 free bytes가 writer low-disk watermark를 충분히 상회하는지 확인하고, 부족하면 실주문과 무관한 closed-date verified compression만 실행한 뒤 observer canary를 재검증한다.
  - 완료 조건: exact-date canary remains pass or row-exclusion-only through close; later clean windows continue collecting; provider replay remains held until queue-loss scope has an exact exclusion receipt or the next clean date
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[ThresholdEnvAutoApplyPreopen0914] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-09-14`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-11.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0914] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-09-14`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-09-11.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-09-11.json), [code_improvement_workorder_2026-09-11.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-11.json), [threshold_apply_2026-09-14.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-09-14.json), [threshold_runtime_env_2026-09-14.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-14.json), [threshold_runtime_env_verify_2026-09-14.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-14.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`5`, forced_scout_with_post_sell_count=`13`, post_sell_join_coverage_pct=`3.367876`, outcome_coverage_state=`partial`, profitable_forced_scout_count=`10`, loss_or_flat_forced_scout_count=`3`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0914] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-09-14`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-11.json)
  - 전일 postclose candidate_selected_families=score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, post_probe_winner_recovery, entry_opportunity_recheck_runtime, holding_decision_context_v1, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0914] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-09-14`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-09-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-11.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0914] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-09-14`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-09-14.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-09-14.jsonl), [threshold_events_2026-09-14.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-09-14.jsonl), [observation_source_quality_audit_2026-09-14.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-14.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-09-14 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

- [ ] `[KrxAftermarketSorCanary0914] 통합 KRX/NXT 애프터마켓 SOR canary·source·reconciliation 자연 소비 확인` (`Due: 2026-09-14`, `Slot: INTRADAY`, `TimeWindow: 15:25~20:05`, `Track: RuntimeStability`)
  - Source: [canary approval](/home/ubuntu/KORStockScan/data/runtime/krx_aftermarket_sor_canary_approval/krx_aftermarket_sor_canary_approval_2026-09-14.json), [runtime release selection](/home/ubuntu/KORStockScan/data/runtime/runtime_release_selection.json), [unified runtime deployment](/home/ubuntu/KORStockScan/data/runtime/unified_runtime_deployment.json), [deployment receipt](/home/ubuntu/KORStockScan/docs/audit-reports/2026-09-12-krx-aftermarket-sor-deployment.md)
  - 판정 기준: 07:35 PREOPEN과 07:55 main PID가 현재 selector의 release `/home/ubuntu/KORStockScan-runtime-releases/tuning-net-ev-floor-20260914` / `1aec12d37357d5f3cf6f44c83f668514fe557f82` 또는 이 항목을 승계한 최신 검토 release를 소비하고, 15:30~16:00 transition은 신규 submit 0, 16:00~19:40은 실제 자격이 확인된 기존 guard 통과 종목에만 main initial BUY one-share·route SOR·type `0|00|6`(`3=>6`) canary가 허용되는지 확인한다. 2026-09-14 이후 15:15 terminal SELL은 0건이어야 한다. 19:40 이후 신규 BUY 0을 유지하고, 19:45 이후에는 신선한 실행가능 매도호가 기준 비용 차감 수익률이 `> 0`인 경우만 terminal SELL 후보로 선택하며 `<= 0`이면 terminal 신호 없이 기존 holding·익절·손절·보호·AI 로직을 계속한다. unsupported type broker submit 0을 대사한다. canary의 broker receipt·route/type·source-quality·central sizing policy가 모두 유효하면 다음 PREOPEN에만 hash-bound successor policy가 발행되며, 없거나 invalid면 one-share canary/기존 guard를 유지한다.
  - 완료 조건: exact approval/root/commit/session-contract hash 소비 receipt, SOR requested route와 KRX|NXT|UNKNOWN actual venue 분리, partial/cancel/restart 수량 보존, 통합 source cron/collector coverage, 15:15 terminal signal 0, 19:45 positive-net SELL exact receipt 또는 valid nonpositive-net HOLD 판정, 20:05 이후 장후 consumer의 신규 cohort source-only/blocked 처리를 확인한다. 정상 HOLD는 같은 거래일·종료 직전60초 이내 판정이고 open BUY/SELL·close-reconciliation blocker가 없어야 한다. nonpositive-net HOLD는 다른 holding/hard-safety SELL을 차단하지 않아야 하며, 실주문이 없으면 기회 부재와 차단 사유를 보존하고 성공을 합성하지 않는다.
  - rollback: owner=`main operator`; 즉시 조건은 actual venue 오귀속, unsupported submit, 경계 중복/고아 주문, owner/custody/quantity 불일치, 미승인 dual BUY, UNKNOWN의 기존 NXT EV 편입이다. 신규 dual entry만 OFF하고 기존 주문·보유·미체결 reconciliation/SELL은 유지한다.

## 장후 체크리스트 (16:25~21:55)

- [ ] `[ThresholdDailyEVReport0914] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-09-14`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-09-11.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-09-11.json), [threshold_cycle_ev_2026-09-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-11.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0914] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-09-14`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-11.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[MainAIQualitySourceGapMainAIAllocatorSubmittedTraceCustodyRepair0914] main AI allocator submitted trace source 결속 복구 확인` (`Due: 2026-09-14`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-11.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-11.json)
  - 판정 기준: workorder `main-ai-gap-e08c3479beab7e76e067d51b`의 owner=`MainAIAllocatorSubmittedTraceCustodyRepair`, reason_codes=`missing_expected_submitted_trace=10`를 source-only producer 보완으로 닫는다. submitted trace와 immutable receipt의 exact join 또는 source-quality 제외를 확인한다. non-submitted는 not-applicable이며 실제 custody 원장·주문을 수정할 권한은 없다.
  - 완료 조건: each submitted allocator trace joins one exact immutable receipt or is explicitly source-quality excluded; non-submitted stages remain not-applicable and are not promoted to missing evidence
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[CodeImprovementWorkorderReview0914] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-09-14`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-09-11.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-09-11.md), [code_improvement_workorder_2026-09-11.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-11.json)
  - 판정 기준: selected_order_count=40와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[MachineLifecycleTurnoverObjectiveFollowup0914] 위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인` (`Due: 2026-09-14`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_policy_approval_postclose_2026-09-11.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_2026-09-11.json), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 판정 기준: 승인 후보 수와 무관하게 `followup_required=true`인 미완료 목적 항목 `machine_lifecycle_turnover_policy_research_v1`(status=`EVIDENCE_ACCUMULATING`, next_action=`repair_excluded_source_report_contracts_and_rerun`)의 상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.
  - 상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, `EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. `CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.
  - 권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[AutomationTriggerDecisionSummary0914] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-09-14`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-09-11.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-09-11.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`6`, skip_count=`0`, source_missing_count=`6`, force_override_count=`0`, run_steps_sample=`pattern_lab_currentness_audit, pattern_lab_ai_review, observation_source_quality_audit, pattern_lab_propagation_audit, runtime_apply_gap_audit`, skip_steps_sample=`-`, top_reasons=`disabled_by_runtime_policy:8, source_missing_or_unreadable:6, output_missing_or_unreadable:5, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

- [ ] `[PostcloseSourceQualityGateReview0914] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-09-14`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-09-14.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-14.json), [threshold_cycle_ev_2026-09-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-14.json), [code_improvement_workorder_2026-09-14.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-14.json), [threshold_cycle_postclose_verification_2026-09-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-09-14.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
