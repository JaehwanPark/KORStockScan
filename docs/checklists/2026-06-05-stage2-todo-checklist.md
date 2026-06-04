# 2026-06-05 Stage2 To-Do Checklist

## 오늘 목적

- Stage 4 `entry_price_v2` runtime input 전환 결과를 post-apply attribution으로 확인한다.
- Stage 5 `holding_flow_v2`와 `entry_screen_v2`는 순차 후보로만 판정하고 동시 runtime enablement를 금지한다.
- 다음 영업일로 넘길 항목은 go/no-go, blocker, rollback guard, artifact source를 명시한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## 수동 롤아웃 체크리스트: 진입/보유/청산 AI input v2

- [ ] `[EntryPriceV2PostApplyAttribution0605] Stage 4 entry_price_v2 runtime input post-apply attribution 확인` (`Due: 2026-06-05`, `Slot: POSTCLOSE`, `TimeWindow: 17:20~17:45`, `Track: AIPrompt`)
  - Source: [threshold_cycle_ev_2026-06-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-05.json), [runtime_approval_summary_2026-06-05.md](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-06-05.md), [pipeline_events_2026-06-05.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-05.jsonl)
  - IN scope: entry_price v2 input provenance, parse/fallback rate, latency, chase bps, stale submit block, negative EV category, duplicate refresh count.
  - OUT scope: provider route change, threshold/order/quantity guard change, holding/analyze runtime input switch, bot restart.
  - Acceptance: no duplicate-call regression, Bedrock failback chain remains Qwen3 32B -> Nova Lite v2 -> defensive fallback, p95 latency and parse rate stay within Stage 4 acceptance, post-apply attribution artifact can separate input effect from threshold/order guard effect.
  - Go/no-go: pass이면 Stage 5 후보 검토로 진행한다. fail이면 rollback flag를 next PREOPEN 후보로 남기고 `entry_price_v2_rollback_candidate`로 닫는다.

- [ ] `[HoldingFlowV2SequentialDecision0605] Stage 5 holding_flow_v2 순차 rollout 후보 판정` (`Due: 2026-06-05`, `Slot: POSTCLOSE`, `TimeWindow: 17:45~18:05`, `Track: AIPrompt`)
  - Source: [threshold_cycle_ev_2026-06-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-05.json), [pipeline_events_2026-06-05.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-05.jsonl), [test_holding_flow_override.py](/home/ubuntu/KORStockScan/src/tests/test_holding_flow_override.py)
  - IN scope: holding_flow current vs v2 replay/report-only candidate, HOLD/TRIM early review state-change policy, hard/protect/emergency/order/account/cooldown/quantity guard precedence.
  - OUT scope: simultaneous `analyze_target` v2 runtime switch, forced exit rule change, score cutoff change, provider route change.
  - Acceptance: hard guard precedence is unchanged, parse success >=99%, stale/parse failure remains fail-closed, HOLD/TRIM early review triggers at most one bounded review per state-change window.
  - Go/no-go: pass이면 next trading day checklist에 report-only Stage 5 execution item을 create/keep한다. fail이면 `holding_flow_v2_rework_required`로 닫는다.

- [ ] `[EntryScreenV2SequentialDecision0605] Stage 5 entry_screen_v2 순차 rollout 후보 판정` (`Due: 2026-06-05`, `Slot: POSTCLOSE`, `TimeWindow: 18:05~18:20`, `Track: AIPrompt`)
  - Source: [threshold_cycle_ev_2026-06-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-05.json), [pipeline_events_2026-06-05.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-05.jsonl), [test_ai_engine_openai_transport.py](/home/ubuntu/KORStockScan/src/tests/test_ai_engine_openai_transport.py)
  - IN scope: analyze_target `entry_screen_v2` replay/report-only candidate, state-change early refresh one-per-cooldown guard, BUY/WAIT/DROP-only prompt boundary.
  - OUT scope: order price decision, provider route change, score threshold mutation, Telegram BUY alert expansion, broker guard relaxation.
  - Acceptance: cooldown duplicate-call guard holds, state-change trigger reason is audited, prompt does not decide price/quantity/holding/exit, output schema remains `entry_v1`.
  - Go/no-go: pass이면 holding_flow와 별도 날짜에만 sequential rollout로 넘긴다. fail이면 `entry_screen_v2_rework_required`로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-06-04` postclose -> `2026-06-05`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[SwingPreFinalAutoAndFinalApprovalPreopen0605] 스윙 pre-final auto state 및 final approval artifact 확인` (`Due: 2026-06-05`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-06-04.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-04.json), [threshold_cycle_ev_2026-06-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-04.json)
  - 판정 기준: pre-final은 parsed AI Tier2 auto state가 있어야 하고, final-stage는 사용자 승인 artifact가 있어야 한다.
  - 금지: 스윙 full-live 전환, cap release, provider/bot 변경, hard-safety 완화를 pre-final auto state로 처리하지 않는다.
  - 다음 액션: `pre_final_auto_selected`, `final_approval_artifact_present`, `blocked_by_policy` 중 하나로 닫는다.
  - 처리 결과: `blocked_by_policy`
  - 판정: 스윙 pre-final/final runtime 변경은 없다. final-stage approval artifact도 요구되지 않았다.
  - 근거: [swing_runtime_approval_2026-06-04.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-04.json)은 `summary.requested=0`, `summary.approved=0`, `summary.blocked=12`, `summary.runtime_change=false`, `approval_requests=[]`이고 `final_user_approval_boundary=full_live_only`를 유지한다. [threshold_apply_2026-06-05.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-05.json)의 `swing_runtime_approval`도 `requested=0`, `approved=0`, `selected=[]`, `approval_artifact=null`, `dry_run_forced=false`다.
  - 다음 액션: 스윙 full-live 전환, cap release, provider/bot 변경, hard-safety 완화는 하지 않는다. 장후 스윙 관련 후보는 postclose 산출물에서 pre-final과 final approval boundary를 다시 분리한다.

- [x] `[ThresholdEnvAutoApplyPreopen0605] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-06-05`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-04.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 처리 결과: `applied_guard_passed_env`
  - 판정: PREOPEN wrapper는 성공했고 `auto_bounded_live` guard 통과분만 runtime env에 반영됐다. 수동 사용자 개입 또는 blocked family 우회는 확인되지 않았다.
  - 근거: [threshold_cycle_preopen_2026-06-05.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-06-05.status.json)은 `status=succeeded`다. [threshold_apply_2026-06-05.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-05.json)은 `source_date=2026-06-04`, `status=auto_bounded_live_ready`, `runtime_change=true`, `warnings=[]`이고 selected auto apply는 `soft_stop_whipsaw_confirmation` 1건이다. [threshold_runtime_env_2026-06-05.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-05.json)은 selected families `soft_stop_whipsaw_confirmation`, `scalp_sim_auto_approval`, `swing_sim_auto_approval`를 남겼다. bridge live-auto 후보 `entry_wait6579_score66_69_recovery_gate_v1`와 `scale_in_bucket_runtime_policy_v1`는 `blocked_source_quality`, `bootstrap_pending`, `runtime_apply_not_allowed`, `runtime_apply_bridge_auto_live_contract_missing`으로 정상 차단됐다.
  - 다음 액션: 장중 threshold mutation은 하지 않는다. bridge blocked family, position sizing approval request, sim-auto policy를 broker/order/provider/bot/cap 변경 근거로 쓰지 않고 장중 provenance와 postclose attribution으로만 확인한다.

- [x] `[PreopenAutomationHealthCheck20260605] 장전 자동화체인 상태 확인` (`Due: 2026-06-05`, `Slot: PREOPEN`, `TimeWindow: 08:00~09:00`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [threshold_apply_2026-06-05.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-05.json), [threshold_runtime_env_2026-06-05.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-05.json)
  - 판정: `pass`
  - 근거: `logs/threshold_cycle_preopen_cron.log`는 `[DONE] threshold-cycle preopen target_date=2026-06-05 finished_at=2026-06-05T07:35:02+0900` marker를 남겼고, [threshold_cycle_preopen_2026-06-05.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-06-05.status.json)은 `status=succeeded`다. [threshold_apply_2026-06-05.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-05.json)은 `status=auto_bounded_live_ready`, `runtime_change=true`, `warnings=[]`이며 [threshold_runtime_env_2026-06-05.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-05.env)을 생성했다. `logs/ensemble_scanner.log`는 `[DONE] final_ensemble_scanner target_date=2026-06-05 finished_at=2026-06-05T07:21:15` marker를 남겼다.
  - 다음 액션: 장중에는 selected PREOPEN env 축의 provenance, sim/probe authority split, source-quality gate만 관찰한다. 이 RunbookOps 확인은 threshold/order/provider/bot/env/cap/hard-safety 변경 권한을 열지 않는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0605] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-06-05`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-04.json)
  - 판정 기준: selected_families=bad_entry_refined_canary, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0605] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-06-05`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-06-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-04.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0605] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-06-05`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-06-05.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-05.jsonl), [threshold_events_2026-06-05.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-06-05.jsonl), [observation_source_quality_audit_2026-06-05.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-05.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-06-05 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[PostcloseSourceQualityGateReview0605] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-06-05`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-06-05.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-05.json), [threshold_cycle_ev_2026-06-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-05.json), [code_improvement_workorder_2026-06-05.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-05.json), [threshold_cycle_postclose_verification_2026-06-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-05.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0605] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-06-05`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-04.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[CodeImprovementWorkorderReview0605] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-06-05`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-06-04.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-04.md), [code_improvement_workorder_2026-06-04.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-04.json)
  - 판정 기준: selected_order_count=84와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0605] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-06-05`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-04.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[LifecycleQuietGapReview0605] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-06-05`, `Slot: POSTCLOSE`, `TimeWindow: 17:30~17:45`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-06-04.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-04.json), [runtime_apply_gap_audit_2026-06-04.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-04.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`212`, rollup_required_count=`212`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'exclusion_dimension_candidate': 3, 'parent_conflict_child': 10, 'positive_source_only_keep_collecting': 201}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0605] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-06-05`, `Slot: POSTCLOSE`, `TimeWindow: 18:10~18:25`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-06-04.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-06-04.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`15`, run_count=`14`, skip_count=`1`, source_missing_count=`0`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, scalp_sim_ai_deferred_review, pattern_lab_currentness_audit`, skip_steps_sample=`codebase_performance_workorder`, top_reasons=`upstream_drift_signal:14, upstream_artifact_newer:2, fresh_outputs_no_trigger:1, output_missing_or_unreadable:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->



## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
