# 2026-06-29 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-06-26` postclose -> `2026-06-29`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0629] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-06-29`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-26.json), [threshold_apply_2026-06-29.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-29.json), [threshold_runtime_env_2026-06-29.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-29.env), [threshold_runtime_env_2026-06-29.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-29.json), [quote_consistency_normalization_2026-06-29.json](/home/ubuntu/KORStockScan/data/threshold_cycle/operator_runtime_env_locks/quote_consistency_normalization_2026-06-29.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env/verify 결과를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다. `selected_families`와 `runtime_env_overrides`가 일치하고, 가격정규화 포함 전체 runtime family가 env 파일에 누락 없이 export 되었는지 확인한다.
  - 가격정규화 필수 확인: `quote_consistency_normalization`이 selected=true이고 `KORSTOCKSCAN_QUOTE_CONSISTENCY_RUNTIME_ENABLED=true`, `MAX_WS_AGE_MS=700`, `MAX_REST_AGE_MS=1500`, `OK_GAP_BPS=30`, `WARN_GAP_BPS=80`, `EMERGENCY_REST_TIMEOUT_MS=400`, `BLOCK_ENTRY_ON_DIVERGENCE=true`가 runtime env/manifest 양쪽에 존재해야 한다. protective/hard/emergency sell 차단 금지와 hard safety 우선순위가 operator lock scope/forbidden_uses에 남아 있어야 한다.
  - 전체 runtime 필수 확인: `runtime_env_handoff_verification.passed=true`, `missing_family_count=0`, `findings=[]`인지 확인하고, 기존 operator runtime override와 신규 가격정규화 env가 서로 덮어쓰거나 누락되지 않았는지 확인한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다. 가격정규화 점검을 provider route, broker guard, hard/protect/emergency stop 완화, bot restart 승인으로 해석하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `applied_guard_passed_env_quote_consistency_verified`, `blocked_no_env`, `partial_apply_with_blocked_families`, `quote_consistency_env_missing`, `runtime_env_verify_failed`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0629] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-06-29`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-26.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, lifecycle_decision_matrix_runtime, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, weak_context_late_entry_guard_runtime가 runtime event provenance에 찍히는지 확인한다. 가격정규화 runtime rows는 `quote_consistency_state`, `canonical_mark_price`, `executable_buy_price`, `executable_sell_price`, `ws_rest_gap_bps`, `price_source`, `normalization_runtime_effect=true`가 누락 없이 기록되는지 함께 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0629] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-06-29`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-06-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-26.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0629] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-06-29`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-06-29.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-29.jsonl), [threshold_events_2026-06-29.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-06-29.jsonl), [observation_source_quality_audit_2026-06-29.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-29.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-06-29 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (21:40~23:05)

- [ ] `[PostcloseSourceQualityGateReview0629] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-06-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-06-29.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-29.json), [threshold_cycle_ev_2026-06-29.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-29.json), [code_improvement_workorder_2026-06-29.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-29.json), [threshold_cycle_postclose_verification_2026-06-29.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-29.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0629] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-06-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-26.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0629] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-06-29`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-26.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0629] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-06-29`, `Slot: POSTCLOSE`, `TimeWindow: 22:05~22:20`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-06-26.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-26.md), [code_improvement_workorder_2026-06-26.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-26.json)
  - 판정 기준: selected_order_count=113와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[RuntimeApplyGapDirectiveReview0629] runtime apply gap Codex 작업지시 표면화 및 구현 여부 확인` (`Due: 2026-06-29`, `Slot: POSTCLOSE`, `TimeWindow: 22:35~22:50`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-06-26.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-26.json), [runtime_apply_gap_audit_2026-06-26.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-26.md), [runtime-apply-gap-audit-user-guide.md](/home/ubuntu/KORStockScan/docs/runtime-apply-gap-audit-user-guide.md)
  - 판정 기준: runtime apply gap audit의 Codex 작업지시 `RESOLVE_SOURCE_DIMENSION_GAP`:scale_in:ai_score_band:score_unknown(block=source_dimension_gap_contract)를 구현 필요, 이미 해결, 설계 보류, reject로 분류한다.
  - 금지: 작업지시를 approval artifact나 즉시 runtime env 수정으로 해석하지 않는다. broker/order/provider/cap guard 우회와 장중 threshold mutation은 금지한다.
  - 다음 액션: `implement_now`, `already_implemented`, `defer_design`, `reject`, `needs_new_workorder` 중 하나로 닫고, 구현 시 테스트와 postclose verifier handoff를 같이 확인한다.

- [ ] `[AutomationTriggerDecisionSummary0629] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-06-29`, `Slot: POSTCLOSE`, `TimeWindow: 22:50~23:05`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-06-26.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-06-26.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`16`, run_count=`15`, skip_count=`1`, source_missing_count=`0`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`scalp_sim_ai_deferred_review`, top_reasons=`upstream_drift_signal:14, upstream_artifact_newer:9, fresh_outputs_no_trigger:1, output_missing_or_unreadable:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 수동 보강 체크리스트

- [x] `[PreSubmitGuardApprovalReadiness0629] overbought/liquidity report-only 축 승인 후보 승격 가능 여부 확인` (`Due: 2026-06-29`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: ScalpingLogic`)
  - Source: [threshold_apply_2026-06-29.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-29.json), [threshold_cycle_ev_2026-06-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-26.json), [runtime_approval_summary_2026-06-26.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-06-26.json), [runtime_apply_bridge_2026-06-26.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-06-26.json), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [threshold_cycle_ev_report.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_ev_report.py)
  - 판정 기준: `overbought_pullback_guard_p1`와 `liquidity_pre_submit_guard_p1`의 `sample_floor_status=ready`, source-quality pass, forbidden-use contract, same-stage owner conflict, missed_winner/avoided_loser trade-off, `avg_close_10m_pct`, `avg_mae_10m_pct`, `avg_mfe_10m_pct`를 확인한다. 현재 자동화 조건상 `human_approval_required=true`라도 `calibration_state=approval_required`가 아니면 approval request가 생성되지 않으므로, `hold` 유지가 맞는지 또는 approval artifact 후보로 승격해야 하는지를 evidence로 닫는다.
  - 금지: 이 항목을 PREOPEN runtime env 직접 수정, approval artifact 승인 대체, broker/order/provider/cap/bot 변경, hard-safety 완화, 또는 장중 threshold mutation 근거로 사용하지 않는다. 승인 후보로 승격하더라도 다음 PREOPEN 적용은 별도 approval artifact와 runtime apply bridge 검증을 통과해야 한다.
  - 다음 액션: `approval_candidate_ready`, `approval_contract_missing`, `blocked_by_forbidden_use`, `same_stage_conflict`, `hold_more_evidence`, `reject_no_edge` 중 하나로 닫고, `approval_candidate_ready`이면 approval_id, 대상 env key, rollback guard, 다음 PREOPEN verify 항목을 남긴다.
  - 처리 결과 (`2026-06-27 KST`): 판정=`same_stage_conflict` + `approval_contract_missing`. 근거: [threshold_apply_2026-06-29.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-29.json)에서 `overbought_pullback_guard_p1`은 `sample_count=1449/20`, `source_sample_count=215`, `sample_floor_status=ready`, `missed_winner_rate=81.2111`, `avoided_loser_rate=15.4756`, `avg_close_10m_pct=11.0906`로 표본과 missed-upside evidence는 충분하지만 `calibration_state=hold`, `allowed_runtime_apply=false`, `recommended_values.enabled=false`, `approval_requests=[]`라 approval artifact 후보로 닫히지 않았다. 같은 2026-06-29 PREOPEN에는 `weak_pullback_entry_block_runtime`이 이미 `KORSTOCKSCAN_SCALP_REAL_WEAK_PULLBACK_ENTRY_BLOCK_ENABLED=true`로 선택되어 overbought/pullback submit 전 차단 계층과 attribution이 겹친다. `liquidity_pre_submit_guard_p1`도 `sample_count=2061/20`, `source_sample_count=464`, `sample_floor_status=ready`, `missed_winner_rate=72.7776`, `avoided_loser_rate=25.3288`, `avg_close_10m_pct=2.2833`이나 `calibration_state=hold`, `allowed_runtime_apply=false`, `recommended_values.enabled=false`, `approval_requests=[]`이며, 같은 PREOPEN에 `pre_submit_liquidity_relief_runtime`이 `KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_ENABLED=true`로 선택되어 liquidity submit 차단 완화 계층과 충돌한다. 따라서 두 p1 family는 지금 approval 후보로 승격하지 않고 기존 pre-submit safety/risk-context 관측으로 유지한다.
  - 후속 조건: 2026-06-29 장후에는 `weak_pullback_entry_block_runtime`과 `pre_submit_liquidity_relief_runtime`의 post-apply attribution을 먼저 확인한다. 그 뒤에도 missed_winner가 높고 selected runtime이 효과를 설명하지 못하면, p1 자체의 구체 `recommended_values`, approval_id, rollback guard, same-stage owner 해소 조건을 포함한 별도 approval artifact 후보로 다시 표면화한다.


## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
