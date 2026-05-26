# 2026-05-27 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-05-26` postclose -> `2026-05-27`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0527] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-27`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-26.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[OpenAIWSPreopenConfirm0527] OpenAI WS 유지 설정 및 entry_price/analyze_target provenance 확인` (`Due: 2026-05-27`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-26.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-26.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 OpenAI route/Responses WS 설정과 `analyze_target`, `entry_price` transport provenance를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 다음 액션: entry_price transport 표본이 부족하면 장중 표본 재확인 항목과 연결한다.

- [ ] `[SwingPreFinalAutoAndFinalApprovalPreopen0527] 스윙 pre-final auto state 및 final approval artifact 확인` (`Due: 2026-05-27`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-05-26.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-26.json), [threshold_cycle_ev_2026-05-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-26.json)
  - 판정 기준: pre-final은 parsed AI Tier2 auto state가 있어야 하고, final-stage는 사용자 승인 artifact가 있어야 한다.
  - 금지: 스윙 full-live 전환, cap release, provider/bot 변경, hard-safety 완화를 pre-final auto state로 처리하지 않는다.
  - 다음 액션: `pre_final_auto_selected`, `final_approval_artifact_present`, `blocked_by_policy` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0527] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-27`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-26.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime, swing_one_share_real_canary_phase0, swing_gatekeeper_reject_cooldown, entry_wait6579_score66_69_recovery_gate_v1가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0527] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-27`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-26.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[ThresholdDailyEVReport0527] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-05-27`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-05-26.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-05-26.json), [threshold_cycle_ev_2026-05-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-26.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[CodeImprovementWorkorderReview0527] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-05-27`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-26.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-26.md), [code_improvement_workorder_2026-05-26.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-26.json)
  - 판정 기준: selected_order_count=64와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0527] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-27`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-26.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-26.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[RuntimeApplyGapDirectiveReview0527] runtime apply gap Codex 작업지시 표면화 및 구현 여부 확인` (`Due: 2026-05-27`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-05-26.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-05-26.json), [runtime_apply_gap_audit_2026-05-26.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-05-26.md), [runtime-apply-gap-audit-user-guide.md](/home/ubuntu/KORStockScan/docs/runtime-apply-gap-audit-user-guide.md)
  - 판정 기준: runtime apply gap audit의 Codex 작업지시 `IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET`:entry_wait6579_score66_69_recovery_gate_v1:2026-05-26(block=env_mapping_contract), `IMPLEMENT_SCALE_IN_POLICY_CONTRACT`:scale_in_bucket_runtime_policy_v1:2026-05-26(block=runtime_bridge_contract)를 구현 필요, 이미 해결, 설계 보류, reject로 분류한다.
  - 금지: 작업지시를 approval artifact나 즉시 runtime env 수정으로 해석하지 않는다. broker/order/provider/cap guard 우회와 장중 threshold mutation은 금지한다.
  - 다음 액션: `implement_now`, `already_implemented`, `defer_design`, `reject`, `needs_new_workorder` 중 하나로 닫고, 구현 시 테스트와 postclose verifier handoff를 같이 확인한다.

- [ ] `[ShadowCanaryCohortReview0527] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-27`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 당일 변경/관찰 결과를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 상태 변동 여부를 닫는다.
  - 금지: shadow 금지, canary-only, baseline 승격 원칙을 코드/문서 상태와 분리하지 않는다.
  - 다음 액션: 변경이 있으면 기준문서와 checklist를 함께 갱신하고 cohort 잠금 필드를 남긴다.

- [ ] `[EngineRefactorMonitoringSamplerSlice0527] src.engine Phase 2 Slice 2 monitoring sampler safe slice 구현 여부 확인` (`Due: 2026-05-27`, `Slot: POSTCLOSE`, `TimeWindow: 18:55~19:10`, `Track: Plan`)
  - Source: [src-engine-refactor-inventory.md](/home/ubuntu/KORStockScan/docs/proposals/src-engine-refactor-inventory.md), [system_metric_sampler.py](/home/ubuntu/KORStockScan/src/engine/system_metric_sampler.py)
  - 판정 기준: 05-26 POSTCLOSE에서 선정한 `monitoring_sampler_slice_selected`를 기준으로 `src.engine.system_metric_sampler -> src.engine.monitoring.system_metric_sampler` safe slice를 진행할지 결정한다. 구현 시 new canonical path, old root wrapper, old/new import smoke, old/new CLI smoke, targeted monitoring tests, parser, `git diff --check`를 한 slice에서 닫는다.
  - 금지: runtime/order/provider/threshold/bot restart 경로 이동, cron/job id 의미 변경, output path/JSON schema/metric semantics 변경, wrapper 제거, `src/trading` 또는 `src/utils` 전체 이동, direct import bulk rewrite를 금지한다.
  - 다음 액션: `implement_monitoring_sampler_slice`, `defer_after_consumer_inventory`, `blocked_by_runtime_path`, `wrapper_keep_required`, `tests_or_smoke_failed` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->





## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
