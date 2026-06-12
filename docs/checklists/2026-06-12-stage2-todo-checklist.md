# 2026-06-12 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-06-11` postclose -> `2026-06-12`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0612] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-06-12`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-11.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 처리 결과 (2026-06-12 08:03 KST): 판정=`applied_guard_passed_env`. 근거: [threshold_cycle_preopen_2026-06-12.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-06-12.status.json)은 status=`succeeded`, apply_mode=`auto_bounded_live`, auto_apply=`true`, runtime_effect=`preopen_runtime_env_apply_only`, exit_code=`0`이다. [threshold_apply_2026-06-12.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-12.json)은 status=`auto_bounded_live_ready`, runtime_change=`true`, source_date=`2026-06-11`, generated_at=`2026-06-12T07:35:01+09:00`이다. [threshold_runtime_env_2026-06-12.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-12.json)은 selected_families=`soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime, scalp_sim_auto_approval, lifecycle_bucket_discovery_sim_auto_approval, swing_sim_auto_approval`를 기록하고, [threshold_runtime_env_verify_2026-06-12.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-06-12.json)은 status=`pass`, missing_family_count=`0`이다. 현재 bot PID=`9357` env에서 `KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE=2026-06-12`, `KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED=true`, `KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_ENABLED=true`, `KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED=true`, `KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_ENABLED=true` 로드를 확인했다. 사용자 운영 override로 추가된 `KORSTOCKSCAN_SCALP_SAFE_PROFIT=1.0`, `KORSTOCKSCAN_SCALP_SOFT_STOP_MICRO_GRACE_SEC=60`, `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_MAX_WORSEN_PCT=0.3`도 같은 PID에 로드되어 있다. 다음 액션: 장중에는 selected family provenance와 rollback/safety breach만 관찰하고, 추가 threshold/order/provider/cap/bot 변경은 새 사용자 지시 없이는 열지 않는다.

Runbook 운영 확인 기록: `[PreopenAutomationHealthCheck20260612] 장전 자동화체인 상태 확인` 판정=`pass`, Tuning Chain Control State=`GREEN`, blocked_stage=`-`, impact=`preopen apply/runtime env handoff completed; current bot PID loaded 2026-06-12 runtime env and operator overrides`, next_action=`intraday RuntimeEnvIntradayObserve0612에서 selected family provenance, rollback guard breach, soft-stop/profit override event fields를 확인한다`.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0612] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-06-12`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-11.json)
  - 판정 기준: selected_families=`soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `lifecycle_decision_matrix_runtime`, `scalp_sim_auto_approval`, `lifecycle_bucket_discovery_sim_auto_approval`, `swing_sim_auto_approval`가 runtime env와 runtime event provenance에 찍히는지 확인한다. `lifecycle_bucket_discovery_sim_auto_approval`은 active sim priority/catalog handoff와 natural-match 관찰 상태를 분리해 기록한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, active sim priority handoff present/pending, rollback guard breach 여부를 분리 기록한다.
  - 운영 override 메모 (2026-06-12 07:41 KST): 사용자 지시로 `KORSTOCKSCAN_SCALP_SOFT_STOP_MICRO_GRACE_SEC=60`을 당일 runtime env에 추가하고 `restart.flag` 기반 우아한 재기동을 수행했다. 새 bot PID=`5980` env에서 `KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE=2026-06-12`, `KORSTOCKSCAN_SCALP_SOFT_STOP_MICRO_GRACE_SEC=60`, `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC=20` 로드를 확인했다. hard/protect/emergency stop 우선순위, `SCALP_SOFT_STOP_MICRO_GRACE_EMERGENCY_PCT=-2.0`, `SCALP_HARD_STOP=-2.5`는 변경하지 않았다.
  - 운영 override 보강 (2026-06-12 07:48 KST): 사용자 지시로 real soft-stop whipsaw confirmation의 추가 악화 허용폭을 `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_MAX_WORSEN_PCT=0.1 -> 0.3`으로 확대하고 `restart.flag` 기반 우아한 재기동을 수행했다. 새 bot PID=`7576` env에서 `KORSTOCKSCAN_SCALP_SOFT_STOP_MICRO_GRACE_SEC=60`, `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC=20`, `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_MAX_WORSEN_PCT=0.3` 로드를 확인했다. 적용 범위는 soft stop confirmation 조건이며, emergency `-2.0%`, hard stop `-2.5%`, protect stop 우선순위는 변경하지 않는다.
  - 운영 override 보강 (2026-06-12 07:55 KST): 사용자 지시로 real 일반 SCALPING 익절 감시 시작선을 `KORSTOCKSCAN_SCALP_SAFE_PROFIT=0.5 -> 1.0`으로 높이고 `restart.flag` 기반 우아한 재기동을 수행했다. 새 bot PID=`9357` env에서 `KORSTOCKSCAN_SCALP_SAFE_PROFIT=1.0`, `KORSTOCKSCAN_SCALP_SOFT_STOP_MICRO_GRACE_SEC=60`, `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_MAX_WORSEN_PCT=0.3` 로드를 확인했다. 적용 범위는 `profit_rate >= safe_profit_pct` 이후 AI momentum decay/trailing take profit 감시 시작선이며, trailing weak/strong 되밀림 폭, preset TP/protect 경로, 손절선은 변경하지 않는다.

- [ ] `[SimProbeIntradayCoverage0612] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-06-12`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-06-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-11.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다. `scalp_sim_auto_approval`/`lifecycle_bucket_discovery_sim_auto_approval` 표본은 policy/catalog 적용, active priority match, source-quality split, natural no-match를 구분한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, active priority match/open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0612] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-06-12`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-06-12.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-12.jsonl), [threshold_events_2026-06-12.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-06-12.jsonl), [observation_source_quality_audit_2026-06-12.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-12.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-06-12 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[PostcloseSourceQualityGateReview0612] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-06-12`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-06-12.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-12.json), [threshold_cycle_ev_2026-06-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-12.json), [code_improvement_workorder_2026-06-12.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-12.json), [threshold_cycle_postclose_verification_2026-06-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-12.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다. ADM/LDM 입력 source-quality는 `scalp_entry_adm:unknown_bucket_source_quality_gap`, `score_bucket/source_score_missing`, `risk_context_source_missing`, `price_context_source_missing`, LDM `source_dimension_gap_count`, `policy_key_gap_classification_counts`, `lifecycle_flow_incomplete_stage_contract_count`를 함께 기록한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `adm_source_field_gap_workorder_required`, `ldm_source_dimension_gap_workorder_required`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0612] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-06-12`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-06-11.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-06-11.json), [threshold_cycle_ev_2026-06-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-11.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다. `primary_verdict`, `lifecycle_sim_auto_approved_count`, `lifecycle_live_auto_apply_ready_count`, `real_conversion_queue_count`, `positive_ev_sample_floor_blocked_count`, `active_sim_priority_preopen_handoff_pending`, `runtime_observed_count`, `natural_match_0_count`를 함께 기록한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목, sim-only 유지 항목, sample_floor/lineage/source-quality blocker, hold_sample/freeze 항목을 분리한다.

- [ ] `[DynamicEntryPricePostSellJoinVerify0612] dynamic_entry_price_resolver sim post-sell join 및 missed_upside/EV metric 해소 확인` (`Due: 2026-06-12`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~16:55`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-06-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-12.json), [sim_post_sell_evaluations_2026-06-12.jsonl](/home/ubuntu/KORStockScan/data/post_sell/sim_post_sell_evaluations_2026-06-12.jsonl), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py)
  - 판정 기준: `dynamic_entry_price_resolver`의 `candidate_metrics.sim.post_sell_joined_count>0`, `candidate_metrics_missing.sim`에서 `missed_upside`/`source_quality_adjusted_ev_pct` 제거, `source_quality_adjusted_ev_pct`와 `missed_upside` provenance가 `sim_post_sell_evaluations` join으로 표시되는지 확인한다.
  - 금지: `candidate_metrics_diagnostic_missing.real`을 sim 튜닝 readiness blocker로 취급하지 않는다. sim post-sell join 검증 전에는 가격 resolver 추천값을 real runtime authority, broker execution 품질, live-auto promotion 근거로 사용하지 않는다.
  - 다음 액션: `sim_post_sell_join_metric_resolved`, `sim_post_sell_join_pending`, `sim_post_sell_artifact_missing`, `sim_metric_still_missing_fix_producer`, `diagnostic_real_missing_only` 중 하나로 닫는다.

- [ ] `[CodeImprovementWorkorderReview0612] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-06-12`, `Slot: POSTCLOSE`, `TimeWindow: 16:55~17:10`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-06-11.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-11.md), [code_improvement_workorder_2026-06-11.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-11.json)
  - 판정 기준: selected_order_count=115와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다. 장후 ADM source-field gap, LDM source-dimension gap, active sim priority handoff gap, runtime apply gap directive가 workorder에 생성/해소/보류 중 어디에 속하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented, next_checklist_recheck_required 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0612] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-06-12`, `Slot: POSTCLOSE`, `TimeWindow: 17:10~17:25`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-11.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[RuntimeApplyGapDirectiveReview0612] runtime apply gap Codex 작업지시 표면화 및 구현 여부 확인` (`Due: 2026-06-12`, `Slot: POSTCLOSE`, `TimeWindow: 17:25~17:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-06-11.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-11.json), [runtime_apply_gap_audit_2026-06-11.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-11.md), [runtime-apply-gap-audit-user-guide.md](/home/ubuntu/KORStockScan/docs/runtime-apply-gap-audit-user-guide.md)
  - 판정 기준: runtime apply gap audit의 Codex 작업지시 `IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET`:scale_in_bucket_runtime_policy_v1:2026-06-11(block=env_mapping_contract)를 구현 필요, 이미 해결, 설계 보류, reject로 분류한다. `active_sim_priority_preopen_handoff_pending`, `key_lineage_blocker_count`, `conversion_lane_positive_ev_sample_floor_blocked_count`가 06-12 postclose verifier/control tower에서 해소됐는지도 함께 확인한다.
  - 금지: 작업지시를 approval artifact나 즉시 runtime env 수정으로 해석하지 않는다. broker/order/provider/cap guard 우회와 장중 threshold mutation은 금지한다.
  - 다음 액션: `implement_now`, `already_implemented`, `defer_design`, `reject`, `needs_new_workorder` 중 하나로 닫고, 구현 시 테스트와 postclose verifier handoff를 같이 확인한다.

- [ ] `[AutomationTriggerDecisionSummary0612] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-06-12`, `Slot: POSTCLOSE`, `TimeWindow: 18:10~18:25`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-06-11.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-06-11.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`15`, run_count=`13`, skip_count=`2`, source_missing_count=`0`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`scalp_sim_ai_deferred_review, codebase_performance_workorder`, top_reasons=`upstream_drift_signal:13, fresh_outputs_no_trigger:2, output_missing_or_unreadable:2, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

- [ ] `[Tier1WatchingScoreReportOnlyPreopen0615] Tier 1 WATCHING score smoothing report-only PREOPEN 전환 및 PID env 확인` (`Due: 2026-06-15`, `Slot: PREOPEN`, `TimeWindow: 08:45~09:00`, `Track: ScalpingLogic`)
  - Source: [watching_score_smoothing.py](/home/ubuntu/KORStockScan/src/engine/scalping/watching_score_smoothing.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: 코드/회귀 검증 완료 후에만 다음 PREOPEN runtime env에 `KORSTOCKSCAN_AI_WATCHING_SCORE_SMOOTHING_MODE=report_only`를 명시하고 graceful restart 후 PID env 및 첫 3개 `ai_confirmed` event의 `ai_score==ai_score_raw`, `ai_score_smoothing_applied=false`, projected provenance를 확인한다.
  - 금지: 장중 mode 변경, `applied` 직접 전환, 정규 ADM/LDM/threshold-cycle report schema·산식 변경, projected score의 주문 권한 사용을 금지한다.
  - 다음 액션: `report_only_loaded_contract_pass`, `pid_env_missing`, `event_contract_mismatch`, `keep_off_due_regression` 중 하나로 닫는다.

- [ ] `[Tier1WatchingScoreAppliedGateReview0617] Tier 1 WATCHING score smoothing 3-session applied 전환조건 판정` (`Due: 2026-06-17`, `Slot: POSTCLOSE`, `TimeWindow: 17:25~17:40`, `Track: ScalpingLogic`)
  - Source: [watching_score_smoothing.py](/home/ubuntu/KORStockScan/src/engine/scalping/watching_score_smoothing.py), `data/report/ai_watching_score_smoothing_diagnostic/ai_watching_score_smoothing_diagnostic_2026-06-17.json`
  - 판정 기준: 3개 정상 세션, 유효응답 300건, 종목 20개, 3회 이상 sequence 50개, contention/stale/dispersion/flip/delay/EV/missed-upside/source-quality guard를 모두 확인하고 artifact `transition_guard.eligible=true`일 때만 다음 PREOPEN `applied` 후보로 분류한다.
  - 금지: diagnostic artifact를 threshold-cycle/ADM/LDM/preopen-auto-apply 입력으로 등록하거나, 조건 일부 누락 상태에서 applied로 전환하지 않는다.
  - 다음 액션: `eligible_next_preopen_applied_review`, `continue_report_only`, `rollback_off`, `diagnostic_join_fix_required` 중 하나로 닫는다.

- [x] `[EntryCancelWaitStandaloneRuntime0612] 매수취소 대기시간 독립 튜닝축 구현 및 다음 PREOPEN handoff 준비` (`Due: 2026-06-12`, `Slot: INTRADAY`, `TimeWindow: 09:30~15:20`, `Track: ScalpingLogic`)
  - Source: [entry_cancel_wait_attribution.py](/home/ubuntu/KORStockScan/src/engine/scalping/entry_cancel_wait_attribution.py), [entry_cancel_wait_runtime.py](/home/ubuntu/KORStockScan/src/engine/scalping/entry_cancel_wait_runtime.py), [entry_cancel_wait_tuning.py](/home/ubuntu/KORStockScan/src/engine/automation/entry_cancel_wait_tuning.py), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py)
  - 판정: `implemented_next_preopen_activation_ready`. 근거: legacy AI `entry_timeout_sec_override`의 실주문 직접 권한을 제거하고 report/selected/actual timeout 계약을 정렬했다. profile threshold는 `60/120/600/1200`, 일일 step은 일반/돌파 `±30초`, 눌림/예약 `±10%`이며 stale/passive만 30초 guard를 허용한다. Counterfactual producer와 deterministic EV 전용 report를 추가하고 ADM/LDM/lifecycle/general EV/runtime bridge 입력에서 제외했다.
  - 다음 액션: `2026-06-15 PREOPEN` runtime env에서 family selected, enabled=true, profile 4개 threshold, runtime handoff verification을 확인한다. 이후 hold/warning/missing report는 직전 ON/value 유지이며 explicit operator OFF 외 자동 비활성화 금지다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->


## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
