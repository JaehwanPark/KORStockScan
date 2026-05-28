# 2026-05-29 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-05-28` postclose -> `2026-05-29`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0529] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-29`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-28.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 처리 결과(2026-05-29 07:26 KST): `applied_guard_passed_env`.
  - 근거: [threshold_apply_2026-05-29.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-29.json)은 `status=auto_bounded_live_ready`, `apply_mode=auto_bounded_live`, `runtime_change=true`, `approval_requests=[]`, `approval_contract_gaps=[]`로 닫혔다. [threshold_cycle_preopen_2026-05-29.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-05-29.status.json)은 `status=succeeded`다.
  - 다음 액션: 생성된 [threshold_runtime_env_2026-05-29.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-29.env)만 장중 runtime source로 인정하고, 장중 threshold mutation 및 blocked family 수동 override는 하지 않는다.

- [x] `[OpenAIWSPreopenConfirm0529] OpenAI WS 유지 설정 및 entry_price/analyze_target provenance 확인` (`Due: 2026-05-29`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-28.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-28.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 OpenAI route/Responses WS 설정과 `analyze_target`, `entry_price` transport provenance를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 다음 액션: entry_price transport 표본이 부족하면 장중 표본 재확인 항목과 연결한다.
  - 처리 결과(2026-05-29 07:26 KST): `pass_keep_ws_with_entry_price_sample_observed`.
  - 근거: [openai_ws_stability_2026-05-28.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-28.md)는 `decision=keep_ws`, `unique WS calls=4106`, `analyze_target=4101`, `entry_price=5`, `WS fallback=0`, `WS success rate=1.0`, `entry_price canary instrumentation_gap=False`로 닫혔다.
  - 다음 액션: provider transport/provenance는 계속 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.

- [x] `[SwingPreFinalAutoAndFinalApprovalPreopen0529] 스윙 pre-final auto state 및 final approval artifact 확인` (`Due: 2026-05-29`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-28.json), [threshold_cycle_ev_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-28.json)
  - 판정 기준: pre-final은 parsed AI Tier2 auto state가 있어야 하고, final-stage는 사용자 승인 artifact가 있어야 한다.
  - 금지: 스윙 full-live 전환, cap release, provider/bot 변경, hard-safety 완화를 pre-final auto state로 처리하지 않는다.
  - 다음 액션: `pre_final_auto_selected`, `final_approval_artifact_present`, `blocked_by_policy` 중 하나로 닫는다.
  - 처리 결과(2026-05-29 07:26 KST): `blocked_by_policy`.
  - 근거: [swing_runtime_approval_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-28.json)은 `summary.requested=0`, `summary.approved=0`, `summary.blocked=14`, `runtime_change=false`, `approval_requests=[]`이며 주요 block reason은 `severe_downside_guard`다.
  - 다음 액션: 스윙 full-live 전환, cap release, provider/bot 변경, hard-safety 완화는 열지 않고 장후 source report 재판정까지 dry-run/sim-only 경계를 유지한다.

## Runbook 운영 확인

- [x] `[PreopenAutomationHealthCheck20260529] 장전 자동화체인 상태 확인` (`Due: 2026-05-29`, `Slot: PREOPEN`, `TimeWindow: 08:00~09:00`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [threshold_cycle_preopen_2026-05-29.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-05-29.status.json), [threshold_apply_2026-05-29.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-29.json)
  - 판정: `pass`.
  - 근거: 시간창 이후 확인 시 당일 preopen apply 산출물이 누락되어 표준 wrapper를 같은 날짜로 재실행했고, `threshold_cycle_preopen_2026-05-29.status.json`이 `status=succeeded`로 생성됐다. runtime env는 `threshold_runtime_env_2026-05-29.env`로 생성됐으며 approval request/contract gap은 없다.
  - 다음 액션: Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0529] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-29`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-28.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime, entry_wait6579_score66_69_recovery_gate_v1가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0529] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-29`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-28.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[ThresholdDailyEVReport0529] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-05-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-05-28.json), [threshold_cycle_ev_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-28.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[CodeImprovementWorkorderReview0529] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-05-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-28.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-28.md), [code_improvement_workorder_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-28.json)
  - 판정 기준: selected_order_count=97와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0529] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-29`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-28.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[ShadowCanaryCohortReview0529] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-29`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 당일 변경/관찰 결과를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 상태 변동 여부를 닫는다.
  - 금지: shadow 금지, canary-only, baseline 승격 원칙을 코드/문서 상태와 분리하지 않는다.
  - 다음 액션: 변경이 있으면 기준문서와 checklist를 함께 갱신하고 cohort 잠금 필드를 남긴다.

- [ ] `[RuntimeApplyGapDirectiveReview0529] runtime apply gap Codex 작업지시 표면화 및 구현 여부 확인` (`Due: 2026-05-29`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-05-28.json), [runtime_apply_gap_audit_2026-05-28.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-05-28.md), [runtime-apply-gap-audit-user-guide.md](/home/ubuntu/KORStockScan/docs/runtime-apply-gap-audit-user-guide.md)
  - 판정 기준: runtime apply gap audit의 Codex 작업지시 `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`:lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq(block=positive_edge_must_not_default_to_source_only_keep_collecting), `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`:lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid(block=positive_edge_must_not_default_to_source_only_keep_collecting), `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`:lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui(block=positive_edge_must_not_default_to_source_only_keep_collecting), `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`:lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi(block=positive_edge_must_not_default_to_source_only_keep_collecting), `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`:lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq(block=positive_edge_must_not_default_to_source_only_keep_collecting) 외 3건를 구현 필요, 이미 해결, 설계 보류, reject로 분류한다.
  - 금지: 작업지시를 approval artifact나 즉시 runtime env 수정으로 해석하지 않는다. broker/order/provider/cap guard 우회와 장중 threshold mutation은 금지한다.
  - 다음 액션: `implement_now`, `already_implemented`, `defer_design`, `reject`, `needs_new_workorder` 중 하나로 닫고, 구현 시 테스트와 postclose verifier handoff를 같이 확인한다.

- [ ] `[CodebaseImprovementPlanSupplement0529] 오늘 코드베이스 개선 사항을 반영한 리팩터링 작업계획서 보완` (`Due: 2026-05-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [codebase_performance_workorder_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-05-28.json), [src-engine-refactor-inventory.md](/home/ubuntu/KORStockScan/docs/proposals/src-engine-refactor-inventory.md), [lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_decision_matrix.py), [test_lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/tests/test_lifecycle_decision_matrix.py)
  - 판정 기준: 오늘 구현된 lifecycle join gap 해소, bundle EV attribution 보강, 관련 테스트/검증 결과를 `src-engine-refactor-inventory.md`의 safe-slice 계획과 consumer/risk/재개 조건에 반영할지 검토한다.
  - 판정 기준: codebase performance workorder와 code improvement workorder는 입력 근거로만 사용하고, 장후 항목의 목적은 즉시 파일 이동/대규모 리팩터링이 아니라 작업계획서 보완으로 한정한다.
  - 금지: runtime/order/provider/threshold/bot restart 경로 이동, cron/job id 변경, output path/JSON schema/metric semantics 변경, wrapper 제거, direct import bulk rewrite를 수행하지 않는다.
  - 다음 액션: `plan_supplemented`, `already_reflected`, `defer_after_postapply_verification`, `needs_new_workorder` 중 하나로 닫고, 문서 수정 시 parser 검증과 표준 수동 sync 명령 안내를 남긴다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->






## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
