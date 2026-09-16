# 2026-09-16 Stage2 To-Do Checklist

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
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-09-15", "sources": {"automation_chain_trigger_decision": {"sha256": "c12eeb6a9b31fb8a99f8210cb6a24b205edb91b70dfa5db02832d42c9e5374f1"}, "code_improvement_workorder": {"sha256": "fca59b4b8c66995770c70f4821a872511a527428584e712bd41bf183be47a2fc"}, "conversion_lane": {"sha256": "aabe1a1779f6e5eba95feae094e4638c889ba68cc14f0521132b5dfa09f46ae5"}, "disposition_evidence_0_0": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_10_0": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_10_1": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_10_2": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_11_0": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_11_1": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_11_2": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_1_0": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_1_1": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_1_2": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_2_0": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_2_1": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_2_2": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_3_0": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_3_1": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_3_2": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_4_0": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_4_1": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_4_2": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_5_0": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_5_1": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_5_2": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_6_0": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_6_1": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_6_2": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_7_0": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_7_1": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_7_2": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_8_0": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_8_1": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_8_2": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_9_0": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_9_1": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "disposition_evidence_9_2": {"sha256": "964da8375c4842b1cfd3cceb26f7ad46fe6fd7b2108177ec9ec975946408ed92"}, "entry_recheck_drought_controller": {"sha256": "4742523203406fd03d847b660316c71cc093e215493eccd2daa5faad8170fb3e"}, "key_lineage_ledger": {"sha256": "090777e2e1f34023d2a3abff7c1b387526ddf3578fe070df1427735dd9e24871"}, "low_price_two_leg_expanded_candidate_research": {"sha256": "312094c85ff15a13e55b2f21075d1aeddbce01ebc490cc891214383b63a8c8d9"}, "low_price_two_leg_tuning": {"sha256": "782d201af9a8a9fdbb0ee2fb4fca1a5a6ee61026a73a2dc7d3cae05eea5b590b"}, "machine_entry_timing_tuning": {"sha256": "e97e5d6cd2818b36922697c77829d4102625dec537e7b50f53524a9a4b010349"}, "machine_microstructure_attribution": {"sha256": "fd84b0328f09ed125ce16aa8f31ea5dc38eced1f03e977b5f462de99e93213b9"}, "machine_microstructure_policy_approval": {"sha256": "c67c660571f9675361b4c7f7b7aaafa75a5e1aee780a3ae2fcb9be2237b86328"}, "main_ai_quality_r0_r3": {"sha256": "2c2e352932795617efefafe6355eba6f51a47eef715682a51c82640dc3bfad84"}, "postclose_recommendation_dispositions": {"sha256": "e15c574419b07ba3432caab96a3b1c08369cbd227711f3bbebcd664659640429"}, "preopen_apply_plan": {"sha256": "37603738838ccbe75bb872d84c28bd05d2a2384b6f01878c7edb06bccfe87642"}, "preopen_pid_verification": {"sha256": "b18737b2b6fd80dc04dae3707e29fa00d50d776431adae427bc60e74a04b2d69"}, "preopen_runtime_manifest": {"sha256": "a8f9b8d9f42cb2ff37b188968dfd79e8cb638df5db78ccc040dfe26d717fd01c"}, "rising_missed_scout_workorder": {"sha256": "31112aabe2d9a6efd6da387b332eff663cfd230af6f8f8c1a254c1680ad6d662"}, "runtime_apply_gap_audit": {"sha256": "5fb407135248eaf99ebb514eddc7f07ddc97b7bbadbe33e7a406319daa387443"}, "samsung_machine_entry_tuning": {"sha256": "7d5c3c75c636fbe251a0290788851cfef6a4659f03625e2dcabd914a9d33119e"}, "threshold_cycle_ev": {"sha256": "407bd887469d6bb1c07ef72ba64dbbcf45745be6a9114a45124e376cac93d33c"}, "tuning_performance_control_tower": {"sha256": "bbbc4d3670c0313ed851bd88f130d7d1e9e0ca5ff3ec1b91b1c645f1a1979c53"}, "widget_advisory_calibration": {"sha256": "dad2c12f8aa807d0d1a9af1139e48c0c69d0dd2cc75c8f0579ad072cd03fa95f"}, "widget_auto_trade_policy_calibration": {"sha256": "1bfb1d1192400e3070c439b53a62b03ef20788ba645c45280fc4c86635325ad4"}, "widget_collector_expansion_recommendation": {"sha256": "c12805964789512228c48ed2c4dcdf527e40e658ab0d3e0c678e62bad012dde8"}, "widget_symbol_runtime_policy_apply": {"sha256": "f84f1d8ce0b87a7e920ae5bb8c9a15f99066660f28f9481dbc08e90f3cad473e"}, "widget_symbol_signal_policy_research": {"sha256": "2ee51bc1f330c2efd87bd2a7ef1f390160c7450bd8317dcbb8f3fe6768a6d806"}}} -->
<!-- POSTCLOSE_RECOMMENDATION_INTAKE_START -->
## 추천 전수 전달 대사

- source-date: `2026-09-15`; status: `warning`
- native rows SHA256: `07d914bf5582335ed76a192f63c57002a3dd4fd28edaf2550a0d5c339d0cd280`
- counts: `{"already_implemented_verified_eligible": 11, "already_implemented_verified_nonrequest": 0, "blocked_external_dependency": 0, "blocked_external_dependency_nonrequest": 0, "blocked_missing_evidence": 9, "blocked_missing_evidence_nonrequest": 1, "deferred": 24, "eligible_actionable_open": 0, "eligible_runtime_effect_false_total": 20, "implement_now_unaccounted_count": 0, "implementation_requested_total": 20, "implemented_pass1": 0, "implemented_pass2": 0, "intake_total": 75, "intake_unaccounted_count": 0, "invalid_or_missing_authority_nonrequest": 0, "invalid_or_missing_authority_total": 0, "nonimplementation_total": 55, "observed_no_patch": 26, "rejected": 4, "user_authority_nonrequest": 0, "user_authority_total": 0}`
- dispositions: `{"already_implemented_verified": 11, "blocked_missing_evidence": 10, "deferred": 24, "observed_no_patch": 26, "rejected": 4}`
- 운영 terminal, 구현 fixed-point, PREOPEN 선택, PID 소비, 경제성은 별도 상태다.

| Owner | Native recommendation dispositions |
| --- | --- |
| low_price_two_leg_expanded_candidate_research | `{"blocked_missing_evidence": 1, "deferred": 4}` |
| machine_microstructure_attribution | `{"observed_no_patch": 1}` |
| main | `{"already_implemented_verified": 11, "blocked_missing_evidence": 9, "deferred": 13, "observed_no_patch": 25}` |
| widget_collector_expansion_recommendation | `{"deferred": 7}` |
| widget_symbol_signal_policy_research | `{"rejected": 4}` |
<!-- POSTCLOSE_RECOMMENDATION_INTAKE_END -->

## 자동 생성 체크리스트 (`2026-09-15` postclose -> `2026-09-16`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (07:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0916] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-09-16`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-15.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0916] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-09-16`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-09-15.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-09-15.json), [code_improvement_workorder_2026-09-15.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-15.json), [threshold_apply_2026-09-16.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-09-16.json), [threshold_runtime_env_2026-09-16.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-16.json), [threshold_runtime_env_verify_2026-09-16.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-16.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`2`, forced_scout_with_post_sell_count=`0`, post_sell_join_coverage_pct=`0`, outcome_coverage_state=`no_closed_outcome`, profitable_forced_scout_count=`0`, loss_or_flat_forced_scout_count=`0`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0916] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-09-16`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-15.json)
  - 전일 postclose candidate_selected_families=entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, post_probe_winner_recovery, entry_opportunity_recheck_runtime, holding_decision_context_v1, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0916] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-09-16`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-09-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-15.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0916] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-09-16`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-09-16.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-09-16.jsonl), [threshold_events_2026-09-16.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-09-16.jsonl), [observation_source_quality_audit_2026-09-16.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-16.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 08:27 보완: 새 `scalp_entry_action_decision_snapshot` 16행에서 계산되지 않은 `buy_pressure_10t=50.0`, `curr_vs_micro_vwap_bp=0.0`, `curr_vs_ma5_bp=0.0` 기본값과 현재 exact snapshot의 과거 WATCHING feature fallback을 재현했다. producer는 미평가 값을 `not_evaluated`로 기록하고 current exact provenance가 있으면 과거 feature를 재사용하지 않도록 수리했으며, audit는 `provider_called=false`, 실제 주문 없음, `unavailable_fail_closed`가 모두 명시된 행만 정상 미평가로 분류한다. 실제 제출 행과 stale/freshness guard에는 이 예외를 적용하지 않는다.
  - 14:13 SOURCE_INVALID 구조 보완: commit `7046a532`는 preflight 평가 순서상 primary blocker·원인군·전체 blocker/missing source를 producer/trace/pipeline에 보존하고, promotion 최초/최신 분모와 배타 집계를 `machine_primary_entry_funnel_v2`에 추가했다. SOURCE_INVALID는 provider 호출 없이 `ai_confirmed_terminal_no_budget`로 닫힌다. immutable release를 PID `3600571`로 기동했고 cwd/commit PID receipt와 runtime-env 검증은 통과했다. 재기동 이후 자연 machine 평가 표본은 아직 없어 새 분해/terminal pair 자연 확인은 이 OPEN 항목의 잔여 acceptance다. 기존 3,594 evaluations 중 SOURCE_INVALID 532건은 원인 필드 배포 전 표본이라 `unclassified`로 유지하며 소급 추정하지 않는다.
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-09-16 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.
  - 16:12 추가 review owner: [postclose release review](../audit-reports/2026-09-16-postclose-release-review.md)는 verifier 동시 발행의 최초 실패 포인터 경합·attempt 충돌과 receipt의 관측 data route를 session preference로 덮어쓰는 결함을 보완한다. 사용자 승인 범위는 review/fix·커밋/푸시·common release 배포·graceful main 재기동이며 독립 machine pin·주문·env/threshold/provider/quantity/custody/hard safety 변경은 아니다. 구현/테스트·selector·새 PID·오늘 장후 strict chain·다음 자연 audit 재발 0은 각각 별도 acceptance로 유지한다. 어제 최초 22:14 fail contract는 덮어써져 복원 불가이므로 release 전환 자체를 직접 원인으로 단정하지 않는다.

## 장후 체크리스트 (16:25~21:55)

- [ ] `[ThresholdDailyEVReport0916] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-09-16`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-09-15.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-09-15.json), [threshold_cycle_ev_2026-09-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-15.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0916] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-09-16`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-15.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[MainAIQualitySourceGapMainAIMicroExactEconomicIntersectionRepair0916] main AI micro exact 경제성 교집합 source gap 복구 확인` (`Due: 2026-09-16`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-15.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-15.json)
  - 판정 기준: workorder `main-ai-gap-8325bf094291fdf698670007`의 owner=`MainAIMicroExactEconomicIntersectionRepair`, reason_codes=`paired_decision_quality_eligible=9, net_economic_eligible=1, current_exact_source_eligible=0`를 source-only producer 보완으로 닫는다. 동일 primary trace의 paired/mature/sidecar/net-economic 교집합과 bridge/source-bundle parent census를 대사한다. 비용·원천 결손을 0 또는 대체 parent로 보간하지 않는다.
  - 완료 조건: bridge current exact trace census equals the source-bundle eligible parent census; a parent is materialized only when the same primary trace is paired, mature, sidecar-valid, and net-economic eligible
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[MainAIQualitySourceGapRuntimeExecutionReceiptCustodyRepair0916] RuntimeExecutionReceiptCustodyRepair main lifecycle source gap 복구 확인` (`Due: 2026-09-16`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-15.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-15.json)
  - 판정 기준: workorder `main-ai-gap-14027f556095f7732fda1abc`의 owner=`RuntimeExecutionReceiptCustodyRepair`, reason_codes=`pipeline_lifecycle_instrumentation_gap_count=1, real_submitted_lifecycle_count=2, broker_execution_unique_count=2`를 source-only producer 보완으로 닫는다. 공식 raw execution envelope의 order/execution identity를 합성 없이 검증하고 결손 lifecycle만 제외한 뒤 paired producer를 재검증한다.
  - 완료 조건: official raw execution envelope/order/execution identity is complete for each repair-required lifecycle or the affected row remains explicitly excluded; custody and order authority remain unchanged
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[CodeImprovementWorkorderReview0916] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-09-16`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-09-15.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-09-15.md), [code_improvement_workorder_2026-09-15.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-15.json)
  - 판정 기준: selected_order_count=32와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[MachineLifecycleTurnoverObjectiveFollowup0916] 위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인` (`Due: 2026-09-16`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_policy_approval_postclose_2026-09-15.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_2026-09-15.json), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 판정 기준: 승인 후보 수와 무관하게 `followup_required=true`인 미완료 목적 항목 `machine_lifecycle_turnover_policy_research_v1`(status=`EVIDENCE_ACCUMULATING`, next_action=`repair_excluded_source_report_contracts_and_rerun`)의 상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.
  - 상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, `EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. `CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.
  - 권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[AutomationTriggerDecisionSummary0916] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-09-16`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-09-15.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-09-15.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`4`, skip_count=`2`, source_missing_count=`3`, force_override_count=`0`, run_steps_sample=`observation_source_quality_audit, pattern_lab_propagation_audit, runtime_apply_gap_audit, workorder_branch`, skip_steps_sample=`pattern_lab_currentness_audit, pattern_lab_ai_review`, top_reasons=`disabled_by_runtime_policy:8, source_missing_or_unreadable:3, fresh_outputs_no_trigger:2, upstream_artifact_newer:2`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

- [ ] `[PostcloseSourceQualityGateReview0916] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-09-16`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-09-16.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-16.json), [threshold_cycle_ev_2026-09-16.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-16.json), [code_improvement_workorder_2026-09-16.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-16.json), [threshold_cycle_postclose_verification_2026-09-16.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-09-16.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 사용자 지시 구현

- [x] `[WidgetResearchWatchAutoPromotionRepair0916] exact-date 정책 release 경로 및 research-watch 자동 승격 연결 보완` (`Due: 2026-09-16`, `Slot: INTRADAY`, `TimeWindow: 12:00~15:30`, `Track: ScalpingLogic`)
  - Source: [widget_auto_trade policy loader](/home/ubuntu/KORStockScan/src/trading/widget_auto_trade/policy.py), [widget symbol signal-policy research](/home/ubuntu/KORStockScan/src/engine/monitoring/widget_symbol_signal_policy_research.py), [widget symbol runtime policy](/home/ubuntu/KORStockScan/src/engine/monitoring/widget_symbol_runtime_policy.py), [widget research-watch config](/home/ubuntu/KORStockScan/data/config/widget_research_watch_symbols.json)
  - 판정 기준: immutable release의 shared-data symlink에서 exact-date standard policy가 canonical path identity로 로드되고, hash-validated 13-symbol research-watch catalog가 completed KRX 1-minute calibration/holdout 분석에 포함되며, 통과 symbol이 exact-date policy, dynamic advisory contract, trader catalog까지 연결된다.
  - 완료 조건: targeted tests와 compile/diff/parser 검증 통과, scoped commit/push, immutable release 배포, widget runtime collector와 signal auto trader의 새 PID/selected-release 확인. 후보 생성과 runtime 적용, 자연 signal/order, 비용차감 경제성은 별도 상태로 기록한다.
  - 권한 경계: 10주 수량, source/execution-quality, 양 calibration half, independent holdout, 비용차감 EV/downside, own-filled custody, manual exclusion, global BUY pause, broker/hard-safety guard를 유지한다. 종목 수 인위적 상한은 두지 않으며 테스트 주문은 제출하지 않는다.
  - 완료 증거 (12:24 KST): commit `2968584e0aa13b4376de62779f353e1c825a95a5`를 `origin/main`에 push하고 immutable release `/home/ubuntu/KORStockScan-runtime-releases/widget-watch-promotion-20260916-2968584e`를 공통 선택 및 영향 서비스에 배포했다. `korstockscan-widget-symbol-runtime-collector.service` PID `3462863`, `korstockscan-widget-signal-auto-trader.service` PID `3462877`이 해당 release에서 `active/running`이며 재시작 횟수는 0이다. 배포 receipt는 `data/runtime/widget_research_watch_promotion_deployment.json`이다.
  - 검증 증거: workspace widget targeted `180 passed`, immutable release widget targeted `180 passed`, machine passing-candidate 구조 판별 `4 passed`, Black/Ruff/compile/diff/parser PASS. trader state의 실행 세션은 `005930/NXT_PREMARKET`으로 복구되었고 08:35 cutoff 이후라 신규 주문은 없으며 KRX 3-symbol safety veto는 유지된다.
  - 자연 증거 경계: 기존 2026-09-15 research report는 연결 전 v3/고정 4-symbol 산출물이므로 현재 research-watch 실행정책은 0개다. 오늘 장후 자연 v4 17-symbol 분석·통과 후보 생성, 이후 자연 signal/order와 비용차감 경제성은 아직 `waiting`이며 이 구현·배포 완료와 동일시하지 않는다.

- [x] `[EpisodeWidgetUnboundedAutoExpansion0916] 위젯·episode 무승인 자동 확장과 장기 미성과 제거 배포` (`Due: 2026-09-16`, `Slot: INTRADAY`, `TimeWindow: 12:30~16:20`, `Track: ScalpingLogic`)
  - Source: [machine_candidate_lifecycle.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_candidate_lifecycle.py), [low_price_two_leg_auto_expansion_policy.py](/home/ubuntu/KORStockScan/src/engine/automation/low_price_two_leg_auto_expansion_policy.py), [auto_expansion_service.py](/home/ubuntu/KORStockScan/src/trading/low_price_two_leg/auto_expansion_service.py), [widget_symbol_runtime_policy.py](/home/ubuntu/KORStockScan/src/engine/monitoring/widget_symbol_runtime_policy.py)
  - 판정 기준: 위젯은 completed daily recommendation 신규 종목을 설정 파일 밖에서 자동 등록하고 모든 통과 종목을 상한 없이 다음 거래일 정책으로 승격한다. Episode는 통과한 new-symbol/time-extension을 exact-date 정책과 동적 서비스로 자동 승격한다. 최소 40개 유효 거래일과 성숙 표본의 full/holdout 비용차감 EV가 모두 비양수인 후보만 신규 진입/연구 universe에서 제거한다.
  - 완료 조건: code review·targeted test·compile/bash/parser/diff 검증, commit/push, immutable release 및 영향 서비스 배포, exact-date policy/owner-policy 소비 경로와 PID 또는 예정 timer receipt를 확인한다.
  - 권한 경계: 보유·미체결 청산 custody, owner registry, 수량, global BUY pause, liquidity/market-weakness, source/execution-quality, broker/hard-safety guard를 유지한다. 자연 signal/order 및 비용차감 실현 경제성은 배포와 분리한다.
  - 완료 증거 (13:20 KST): 구현 commit `fa8e76acf725cb65746f8e67b00af533ceed17e6`, systemd startup 보완 commit `e0e04afe`를 `origin/main`에 push했다. immutable release `/home/ubuntu/KORStockScan-runtime-releases/unbounded-auto-expansion-20260916-fa8e76ac`는 workspace/release affected suite 각 `586 passed`를 통과했고 main PID `3534064`, widget runtime collector PID `3534575`, widget trader PID `3534578`, episode auto-expansion PID `3536363`이 해당 release를 소비한다. 자동확장 timer는 active/waiting이며 다음 예정은 `2026-09-17 08:56 KST`, 서비스 재시작 횟수는 0이다.
  - 정책 증거: `2026-09-15` hash-bound 자연 연구 결과에서 `auto_034020_midday`, `auto_111770_late_morning` 두 profile이 cardinality cap 없이 `2026-09-16` exact-date 정책으로 승격됐다. 두 symbol의 기존 exact-date owner policy에는 이미 `episode` 권한과 broker/registry zero-conflict 검증이 있어 서비스가 정책을 로드했고, 13:20 현재 각각 `READY`/`NO_TRADE`, signal·order 0이다. 장중 owner auto-apply 재실행은 standing window 및 main-process quiescence guard로 두 차례 fail-closed 되었고 기존 정책/env는 변경되지 않았다.
  - 자연 증거 경계: 현재 widget exact-date 자동승격은 0종목이다. 오늘 장후 새 분석 universe는 established 4 + research-watch 13 + completed-daily 자동발견 2 = 19종목이며, 이 중 기준을 통과한 전 종목이 다음 거래일 정책으로 승격된다. 자연 signal/order/fill과 비용차감 경제성은 아직 `waiting`이다.

- [ ] `[SellNoCallNaturalAcceptance0916] 통합 애프터마켓 FAST_EXIT 주문형·미호출 복구 자연 확인` (`Due: 2026-09-16`, `Slot: INTRADAY`, `TimeWindow: 16:40~20:10`, `Track: ScalpingLogic`)
  - Source: [수리·복구 계약](../audit-reports/2026-09-16-sell-no-call-aftermarket-repair.md), `data/runtime/runtime_release_selection.json`, exact record `45050` 및 원 pending generation `3b66289a035c4c39966e34882f08947c`.
  - 판정 기준: 정규장 최유리 IOC `16` 유지, 애프터마켓 청산 최유리 `6` 적용; 실제 미호출 차단만 process-local proof와 영속 terminal/CAS 계약으로 HOLDING 복구한다. 실제 접수 불확실 주문의 reconciliation은 유지한다.
  - 완료 조건: scoped commit/push·immutable release/PID 소비, 해당 orphan journal 종료·DB 상태 일치 및 새 missing-original-order 반복 0. 후속 자연 주문/체결/terminal·비용차감 경제성은 별도 판정한다.
  - 권한 경계: 사용자 구현·배포·기동 승인 범위의 한 generation 복구만 수행한다. 수량/threshold/provider/owner/독립 unit pin/quote·broker·account·cooldown·hard-safety 변경, 수동 주문 및 일괄 DB/journal 해제는 금지한다.

- [ ] `[WidgetPostcloseEvaluationPinAcceptance0916] 위젯 장후 평가 최신 release 소비 및 최종 handoff 자연 확인` (`Due: 2026-09-16`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~23:20`, `Track: RuntimeStability`)
  - Source: [pin 보완·rollback 계약](../audit-reports/2026-09-16-widget-evaluation-release-pin-repair.md), `korstockscan-samsung-widget-evaluation.service`, `data/runtime/widget_evaluation_release_pin_repair_2026-09-16.json`.
  - 판정 기준: 20:10 자연 평가가 `sell-no-call-aftermarket-20260916-0b712b54`에서 실행되고 exact-date calibration/research/runtime-policy 산출물을 생성한다. 이후 final sources → tower → checklist → strict verifier `--require-summary-handoff` → controller/finalization 정합성을 확인한다.
  - 권한 경계: 이번 사용자 보완 지시는 위젯 평가 oneshot pin과 systemd reload만 허용한다. 메인·매매·collector·episode·machine 서비스 재기동, 수동 report/provider/order 호출, timer·threshold·quantity·owner·hard-safety 변경은 하지 않는다. 설치 검증은 자연 완료·자동승격·경제성으로 대체하지 않는다.
  - 배포 증거 (17:00 KST): 위젯 평가 unit의 effective WorkingDirectory/PYTHONPATH/ExecStart가 `0b712b54`로 일치하며 inactive, timer는 20:10 active다. workspace/release 각 `252 passed`, compile/bash/parser/diff PASS, scoped review finding 0. 기존 drop-in backup·SHA를 receipt에 보존했고 메인 PID `3779784`, widget collector/trader PID `3654913`/`3654984` 및 machine-final-refresh route는 유지했다. 자연 실행은 `not_yet_due`다.

- [ ] `[IntegratedAftermarketRouteRepair0916] 통합 애프터마켓 runtime AL 원천 등록·정상 source 자연 확인` (`Due: 2026-09-16`, `Slot: INTRADAY`, `TimeWindow: 18:40~20:10`, `Track: RuntimeStability`)
  - Source: [원인·공식 API 검증·수리·rollback 계약](../audit-reports/2026-09-16-integrated-aftermarket-runtime-route-repair.md), `data/runtime/integrated_aftermarket_runtime_route_repair_2026-09-16.json`, `data/runtime/kiwoom_ws_snapshot/latest.json`.
  - 판정 기준: scoped review/validation 후 commit/push·clean managed release·사용자 승인 graceful main restart를 확인한다. 새 PID에서 actual AL REG 및 fresh exact AL 0B/0D → source-valid consumer 연결을 확인하며, 과거 196행과 새 generation을 분리한다.
  - 권한 경계: 이번 사용자 지시는 기존 WS source owner의 수리·배포·main 기동만 허용한다. plain KRX receipt 재분류, actual venue 추정, guard/quantity/provider/threshold/owner 변경, 수동 주문·report 재생성, 별도 service/timer/cron/정책 family 추가는 하지 않는다. 독립 unit pin은 유지한다.
  - 현재 증거: workspace 최종 `1480 passed` (route/source 403 + full sniper 1077), compile/Black/bash/parser/diff PASS, scoped review finding 0. release·PID·자연 표본은 별도 진행 중이다. AL 미수신·노후·충돌은 계속 fail-closed이며 매매·경제성은 별도 판정한다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
