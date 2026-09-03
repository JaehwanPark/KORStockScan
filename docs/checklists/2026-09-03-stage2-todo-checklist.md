# 2026-09-03 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-09-02` postclose -> `2026-09-03`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (07:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0903] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-09-03`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-02.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0903] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-09-03`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-09-02.json), [code_improvement_workorder_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-02.json), [threshold_apply_2026-09-03.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-09-03.json), [threshold_runtime_env_2026-09-03.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-03.json), [threshold_runtime_env_verify_2026-09-03.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-03.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`2`, forced_scout_with_post_sell_count=`0`, post_sell_join_coverage_pct=`0`, outcome_coverage_state=`no_closed_outcome`, profitable_forced_scout_count=`0`, loss_or_flat_forced_scout_count=`0`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0903] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-09-03`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-02.json)
  - 전일 postclose candidate_selected_families=entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime, post_probe_winner_recovery, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0903] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-09-03`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-02.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0903] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-09-03`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-09-03.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-09-03.jsonl), [threshold_events_2026-09-03.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-09-03.jsonl), [observation_source_quality_audit_2026-09-03.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-03.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-09-03 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (16:25~21:55)

- [ ] `[ScannerOpportunityExecutableMeasurementAcceptance0903] 외부 상승·반등 기회와 전환점 executable BBO 계측 보완 acceptance` (`Due: 2026-09-03`, `Slot: POSTCLOSE`, `TimeWindow: 19:45~20:00`, `Track: ScalpingLogic`)
  - Source: [market_opportunity_census.py](/home/ubuntu/KORStockScan/src/engine/monitoring/market_opportunity_census.py), [entry_turn_point_replay.py](/home/ubuntu/KORStockScan/src/engine/monitoring/entry_turn_point_replay.py), [market_opportunity_census_2026-09-03.json](/home/ubuntu/KORStockScan/data/report/market_opportunity_census/market_opportunity_census_2026-09-03.json), [rising_missed_intraday_feedback_2026-09-03.json](/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-09-03.json)
  - 공식 Kiwoom reference gate: upstream commit `234560d213acd8871ae344b5481aecd2f30287fa`, inspected paths `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`, `kiwoom/core`, `kiwoom/realtime`, `postman/kiwoom-openapi.postman_collection.json`, retrieval `2026-09-03T10:54:06+09:00`. `POST /api/dostk/mrkcond`, `api-id=ka10004`, body `stk_cd`와 최우선 매도·매수 호가/잔량 `sel_fpr_bid|sel_fpr_req|buy_fpr_bid|buy_fpr_req`를 확인했으며, NXT `_NX`는 local exact-route contract로 별도 검증한다.
  - 판정 기준: report schema v3가 official-master `liquid_common/top20/forward_exact` 분모와 scanner funnel을 유지하면서, 외부 census 자체의 `liquid_common/top20` exact-route ka10004 BBO와 promoted WS/prune BBO 보조 경로의 가격·최우선 잔량·receipt time·schedule lag·venue/session·source-only authority를 검증하고 1/3/5/10/20/30/60분 bounded-path 결과와 비용차감 EV를 venue+session별 floor로 fail-closed하는지 확인한다. direct external BBO는 0.25초 간격, run당 40건 cap을 지키고 각 요청 전에 durable target-date ledger에서 KST date당 4,800건 cap을 예약해야 한다. invalid/mismatched/exhausted ledger는 Kiwoom 호출 전 차단하며 최초 ledger는 이미 persisted된 pre-ledger attempt를 초기값으로 이관한다. 전환점 replay는 persisted canonical JSON과 당일 legacy repr bundle을 모두 복원하고 quote reference epoch와 event emission time을 분리해야 한다.
  - 현재 process 반영 경계: 기존 legacy bundle consumer repair는 즉시 재해석할 수 있다. 신규 external-census BBO는 review 이후 다음 5분 one-shot부터, `market_data_effective_quote_reference_epoch`와 promoted WS/prune 최우선 잔량 producer field는 fresh main PID부터 자연 표본 acceptance가 가능하다. 이 항목은 bot 재기동 권한을 만들지 않는다.
  - 금지: ka10027 현재가를 executable BBO로 대체하거나, bounded observer EV를 전수 외부 모집단으로 외삽하거나, source-only 결과로 scanner slot/cooldown/threshold·provider/bot·주문/수량·broker/hard-safety를 변경하지 않는다.
  - 다음 액션: `legacy_consumer_repair_verified`, `fresh_pid_producer_receipt_verified`, `collecting_after_structural_repair`, `source_quality_or_floor_blocked`를 분리하고 exact-BBO coverage>=95%, resolved>=20, right-censored<=20의 venue+session별 상태와 `full_external_population_ev_extrapolation_allowed=false`를 기록한다.

- [ ] `[ThresholdDailyEVReport0903] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-09-03`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-09-02.json), [threshold_cycle_ev_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-02.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0903] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-09-03`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-02.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[MainAIQualitySourceGapMainAIQualityMaterializedCompanionBindingRepair0903] main AI materialized companion exact-hash 결속 복구 확인` (`Due: 2026-09-03`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-02.json)
  - 판정 기준: workorder `main-ai-gap-e1c4f11e9a8acb21057ede9d`의 owner=`MainAIQualityMaterializedCompanionBindingRepair`, reason_codes=`execution_report_materialized_companion_binding_mismatch_count=1, execution_report_materialized_companion_binding_mismatch_dates=2026-08-24`를 source-only producer 보완으로 닫는다. reason_codes에 명시된 source date별 execution report와 materialized request/response companion의 exact hash를 재검증하고, 불변 원천에 결속할 수 없는 historical row는 합성 없이 제외한다.
  - 완료 조건: each affected execution report binds the exact materialized request and response companion hashes for its own source date; unchanged immutable historical rows remain excluded and no runtime or order authority changes
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[MainAIQualitySourceGapRuntimeExecutionReceiptCustodyRepair0903] RuntimeExecutionReceiptCustodyRepair main lifecycle source gap 복구 확인` (`Due: 2026-09-03`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-02.json)
  - 판정 기준: workorder `main-ai-gap-6734b630c81bdcf86afcf240`의 owner=`RuntimeExecutionReceiptCustodyRepair`, reason_codes=`lifecycle_exact_join_missing_count=7, lifecycle_exact_join_missing_dates=2026-08-18`를 source-only producer 보완으로 닫는다. 공식 raw execution envelope의 order/execution identity를 합성 없이 검증하고 결손 lifecycle만 제외한 뒤 paired producer를 재검증한다.
  - 완료 조건: official raw execution envelope/order/execution identity is complete for each repair-required lifecycle or the affected row remains explicitly excluded; custody and order authority remain unchanged
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[CodeImprovementWorkorderReview0903] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-09-03`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-09-02.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-09-02.md), [code_improvement_workorder_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-02.json)
  - 판정 기준: selected_order_count=49와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0903] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-09-03`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-09-02.json), [runtime_apply_gap_audit_2026-09-02.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-09-02.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`372`, rollup_required_count=`372`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 371}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[MachineLifecycleTurnoverObjectiveFollowup0903] 위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인` (`Due: 2026-09-03`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_policy_approval_postclose_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_2026-09-02.json), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 판정 기준: 승인 후보 수와 무관하게 `followup_required=true`인 미완료 목적 항목 `machine_lifecycle_turnover_policy_research_v1`(status=`EVIDENCE_ACCUMULATING`, next_action=`repair_excluded_source_report_contracts_and_rerun`)의 상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.
  - 상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, `EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. `CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.
  - 권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[AutomationTriggerDecisionSummary0903] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-09-03`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-09-02.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-09-02.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`9`, skip_count=`0`, source_missing_count=`4`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:8, disabled_by_runtime_policy:5, source_missing_or_unreadable:4, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

- [ ] `[PostcloseSourceQualityGateReview0903] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-09-03`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-09-03.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-03.json), [threshold_cycle_ev_2026-09-03.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-03.json), [code_improvement_workorder_2026-09-03.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-03.json), [threshold_cycle_postclose_verification_2026-09-03.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-09-03.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 구조 보완 후속

- [ ] `[OneShareThresholdOpportunityEfficiencyAcceptance0903] one-share threshold opportunity 의미·coverage·증분 실행 검증` (`Due: 2026-09-03`, `Slot: POSTCLOSE`, `TimeWindow: 21:05~21:25`, `Track: ScalpingLogic`)
  - Source: [one_share_threshold_opportunity.py](/home/ubuntu/KORStockScan/src/engine/monitoring/one_share_threshold_opportunity.py), [one_share_threshold_opportunity_2026-09-03.json](/home/ubuntu/KORStockScan/data/report/one_share_threshold_opportunity/one_share_threshold_opportunity_2026-09-03.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: 고정 taxonomy `configured_threshold_group_count=5`, forced event보다 늦지 않은 실제 first-blocker 전수 `primary_blocker_evaluation_count`, EV/floor 통과 source-only existing-family `threshold_opportunity_count`를 분리한다. 양(+) EV는 `route=existing_family`이며 별도 계측·join root-cause gap 없이 `implement_now`가 되면 실패다. terminal sell→post-sell record+stock join coverage와 pending/right-censored submit을 확인하고, 같은 record ID의 복수 forced primary event, propagated forced event stock 충돌, 상충하는 post-sell outcome, stock 누락·불일치 또는 관련 malformed JSON은 `source_identity_conflict|source_coverage_gap`으로 격리되어 last-row-wins·valid-empty가 없어야 한다. source processing은 변경 partition만 forced-ID discovery 1회와 해당 ID targeted scan 최대 1회로 제한하고 이전 partition cache hit, scanned/reused·estimated I/O bytes, elapsed를 남겨야 한다. cache payload에 전체 record taxonomy가 들어가면 실패다.
  - 완료 조건: 동일 source 2회 targeted validation에서 두 번째 실행의 cache hit와 `source_bytes_scanned=0`이 확인되고 현재 코드로 재계산한 actionable·AI contract digest 및 후보별 parsed review census가 모두 불변이면 `new_provider_call=false`; 신규 terminal sell source가 있으면 entry date와 무관하게 exact record join되고 terminal receipt 뒤 post-sell 누락만 terminal-lineage gap으로 남는다.
  - 금지: 고정 다섯 group을 신규 후보 5개로 보고하거나, cache hit만으로 EV 유효성을 주장하거나, 이 source-only 보완으로 threshold·provider route·bot·주문·수량/cap·broker/hard-safety를 변경하지 않는다.

- [ ] `[ScannerPruneBBOBoundedObserverAcceptance0903] scanner prune bounded observer 신규 PID·자연 표본 확인` (`Due: 2026-09-03`, `Slot: INTRADAY`, `TimeWindow: 09:10~09:30`, `Track: RuntimeStability`)
  - Source: [pruned_candidate_bbo_collector.py](/home/ubuntu/KORStockScan/src/engine/monitoring/pruned_candidate_bbo_collector.py), [intraday_ws_freshness_monitor.py](/home/ubuntu/KORStockScan/src/engine/monitoring/intraday_ws_freshness_monitor.py), [intraday_ws_freshness_monitor_2026-09-03.json](/home/ubuntu/KORStockScan/data/report/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_2026-09-03.json)
  - 판정 기준: 신규 기동 PID가 active episode 8·pending sample 80의 bounded source-only collector를 로드했고, prune receipt 중 명시적으로 선택된 episode만 coverage/resolved/right-censor/EV 분모에 들어가며 full prune census는 별도 보존되는지 확인한다.
  - 완료 조건: natural prune에서 `new_episode_scheduled|existing_episode_reused`와 exact-route capture 또는 명시적 source-quality gap receipt가 나타나고 `full_funnel_population_ev_extrapolation_allowed=false`가 유지된다.
  - 금지: 표본 확보를 위한 bot 재기동, scanner slot/cooldown·threshold·provider·주문·수량·cap·hard-safety 변경과 bounded 표본 EV의 full population 외삽을 하지 않는다.

- [ ] `[PostcloseTerminalAwareFinalizationAcceptance0903] 장후 terminal-aware cleanup·final detector 설치/실행 확인` (`Due: 2026-09-03`, `Slot: POSTCLOSE`, `TimeWindow: 21:55~23:50`, `Track: RuntimeStability`)
  - Source: [run_postclose_finalization.sh](/home/ubuntu/KORStockScan/deploy/run_postclose_finalization.sh), [postclose_finalization_cron.log](/home/ubuntu/KORStockScan/logs/postclose_finalization_cron.log), [error_detection_2026-09-03.json](/home/ubuntu/KORStockScan/data/report/error_detection/error_detection_2026-09-03.json)
  - 판정 기준: main postclose artifact/log, controller artifact/wrapper와 replay follower, tuning monitoring artifact/log, dashboard archive가 같은 target date로 terminal인 뒤 cleanup→final detector 순서가 실행되고 finalization `[DONE]`이 남는지 확인한다.
  - 실패 처리: predecessor fail/timeout 또는 23:20 KST hard deadline이면 cleanup을 건너뛰고 최대 600초의 detector와 finalization `[FAIL]`을 남겨 원본을 보존한다. 정상 경로도 cleanup/detector를 각각 최대 600초로 제한해 자정 전 20분 고정 여유를 보존하며, 고정 21:55 진행 중 detector snapshot을 final 판정으로 사용하지 않는다.
  - 권한 경계: storage/health automation 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, broker/hard safety 변경 권한이 없다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
