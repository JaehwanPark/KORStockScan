# 2026-06-04 Stage2 To-Do Checklist

## 오늘 목적

- Stage 3 `entry_price_v2` report-only comparison audit를 실행하고 current runtime result와 v2 result를 비교한다.
- 실제 주문가는 기존 current 결과만 사용한다.
- Stage 4 `entry_price` runtime input 전환 여부를 postclose 기준으로만 판정한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## 수동 롤아웃 체크리스트: 진입/보유/청산 AI input v2

- [ ] `[EntryPriceV2ReportOnlyAudit0604] Stage 3 entry_price_v2 report-only comparison audit 결과 확인` (`Due: 2026-06-04`, `Slot: POSTCLOSE`, `TimeWindow: 17:20~17:50`, `Track: AIPrompt`)
  - Source: [pipeline_events_2026-06-04.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-04.jsonl), [threshold_cycle_ev_2026-06-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-04.json), [openai_ws_stability_2026-06-04.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-06-04.md)
  - IN scope: `entry_price` current vs v2 output delta, chase bps, stale submit block, negative EV bucket, parse success, latency, Bedrock failback provenance.
  - OUT scope: runtime authority transfer to v2, threshold/order/quantity guard change, provider route change, bot restart.
  - Acceptance: v2 improves or does not degrade chase/negative-EV category, parse success >=99%, p95 latency degradation <=20%, duplicate-call guard holds, current runtime output remains the only submitted price source.
  - Go/no-go: pass이면 Stage 4 runtime input 전환 후보를 `go_candidate`로 둔다. fail이면 `stage3_report_only_reject_or_rework`로 닫고 v2 runtime enablement를 금지한다.

- [ ] `[EntryPriceV2RuntimeSwitchDecision0604] Stage 4 entry_price runtime input 전환 go/no-go 판정` (`Due: 2026-06-04`, `Slot: POSTCLOSE`, `TimeWindow: 17:50~18:10`, `Track: AIPrompt`)
  - Source: [2026-06-04-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-06-04-stage2-todo-checklist.md), [threshold_cycle_ev_2026-06-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-04.json)
  - IN scope: enabling only `entry_price_v2` runtime input after report-only pass, preserving Qwen3 32B primary -> Nova Lite v2 failback -> defensive fallback.
  - OUT scope: `analyze_target` or `holding_flow` runtime input switch, provider route change, broker/order guard relaxation, threshold mutation.
  - Acceptance: Stage 2 and Stage 3 both pass, rollback flag is documented, audit provenance distinguishes `ai_input_schema=entry_price_v2`, and submit-before-broker revalidation remains active.
  - Go/no-go: pass이면 next PREOPEN bounded env 후보로만 넘긴다. fail이면 `entry_price_v2_runtime_switch_blocked`로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-06-02` postclose -> `2026-06-04`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[SwingPreFinalAutoAndFinalApprovalPreopen0604] 스윙 pre-final auto state 및 final approval artifact 확인` (`Due: 2026-06-04`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-06-02.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-02.json), [threshold_cycle_ev_2026-06-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-02.json)
  - 판정 기준: pre-final은 parsed AI Tier2 auto state가 있어야 하고, final-stage는 사용자 승인 artifact가 있어야 한다.
  - 금지: 스윙 full-live 전환, cap release, provider/bot 변경, hard-safety 완화를 pre-final auto state로 처리하지 않는다.
  - 다음 액션: `pre_final_auto_selected`, `final_approval_artifact_present`, `blocked_by_policy` 중 하나로 닫는다.

- [ ] `[ThresholdEnvAutoApplyPreopen0604] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-06-04`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-02.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[AITransportPreopenConfirm0604] AI transport 유지 설정 및 entry_price/analyze_target provenance 확인` (`Due: 2026-06-04`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-06-02.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-06-02.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 endpoint별 transport를 확인한다. `analyze_target`은 OpenAI Responses WS, `entry_price`는 Bedrock Qwen3 32B primary -> Nova Lite v2 failback provenance를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 다음 액션: entry_price Bedrock provenance 또는 analyze_target WS 표본이 부족하면 장중 표본 재확인 항목과 연결한다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0604] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-06-04`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-02.json)
  - 판정 기준: selected_families=score65_74_recovery_probe, bad_entry_refined_canary, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime, swing_one_share_real_canary_phase0, swing_market_regime_sensitivity가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[AITransportIntradaySample0604] AI transport 장중 표본 및 fallback/fail-closed 재확인` (`Due: 2026-06-04`, `Slot: INTRADAY`, `TimeWindow: 09:20~09:35`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-06-02.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-06-02.md)
  - 판정 기준: `analyze_target` OpenAI WS latency/fallback과 `entry_price` Bedrock transport metadata 누락 여부를 별도 표본으로 확인한다.
  - 금지: entry_price 표본 0건 또는 instrumentation gap을 OpenAI WS runtime 효과 0으로 해석하지 않고, Bedrock provenance 확인을 provider route 변경 근거로 쓰지 않는다.
  - 다음 액션: 표본 부족이면 postclose provenance 보강 workorder로 분리한다.

- [ ] `[SimProbeIntradayCoverage0604] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-06-04`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-06-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-02.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[ThresholdDailyEVReport0604] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-06-04`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-02.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[CodeImprovementWorkorderReview0604] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-06-04`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-06-02.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-02.md), [code_improvement_workorder_2026-06-02.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-02.json)
  - 판정 기준: selected_order_count=134와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0604] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-06-04`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-02.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[RuntimeApplyGapDirectiveReview0604] runtime apply gap Codex 작업지시 표면화 및 구현 여부 확인` (`Due: 2026-06-04`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-06-02.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-02.json), [runtime_apply_gap_audit_2026-06-02.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-02.md), [runtime-apply-gap-audit-user-guide.md](/home/ubuntu/KORStockScan/docs/runtime-apply-gap-audit-user-guide.md)
  - 판정 기준: runtime apply gap audit의 Codex 작업지시 `RESOLVE_SOURCE_DIMENSION_GAP`:lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid(block=source_dimension_gap_contract), `RESOLVE_SOURCE_DIMENSION_GAP`:exit:exit_outcome:outcome_unknown(block=source_dimension_gap_contract), `REVIEW_OBSERVATION_SOURCE_QUALITY_WARNING`:observation_source_quality_audit:warning_summary(block=quiet_gap_visibility_contract)를 구현 필요, 이미 해결, 설계 보류, reject로 분류한다.
  - 금지: 작업지시를 approval artifact나 즉시 runtime env 수정으로 해석하지 않는다. broker/order/provider/cap guard 우회와 장중 threshold mutation은 금지한다.
  - 다음 액션: `implement_now`, `already_implemented`, `defer_design`, `reject`, `needs_new_workorder` 중 하나로 닫고, 구현 시 테스트와 postclose verifier handoff를 같이 확인한다.

- [ ] `[AutomationTriggerDecisionSummary0604] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-06-04`, `Slot: POSTCLOSE`, `TimeWindow: 18:10~18:25`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-06-02.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-06-02.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`13`, skip_count=`1`, source_missing_count=`0`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, scalp_sim_ai_deferred_review, pattern_lab_currentness_audit`, skip_steps_sample=`codebase_performance_workorder`, top_reasons=`upstream_drift_signal:13, fresh_outputs_no_trigger:1, output_missing_or_unreadable:1, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
