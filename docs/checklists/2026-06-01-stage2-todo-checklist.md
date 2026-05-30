# 2026-06-01 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-05-29` postclose -> `2026-06-01`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0601] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-06-01`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-29.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[OpenAIWSPreopenConfirm0601] OpenAI WS 유지 설정 및 entry_price/analyze_target provenance 확인` (`Due: 2026-06-01`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-29.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-29.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 OpenAI route/Responses WS 설정과 `analyze_target`, `entry_price` transport provenance를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 다음 액션: entry_price transport 표본이 부족하면 장중 표본 재확인 항목과 연결한다.
  - 2026-05-30 operator override: `entry_price`는 Bedrock Qwen3 32B primary + Nova Lite v2 failback으로 확인한다. Nova Lite v2도 실패하면 OpenAI 3차 failback 없이 기존 defensive entry-price fallback으로 닫는다. `holding_flow`는 Nova Lite v2 primary + OpenAI failback을 유지한다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0601] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-06-01`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-29.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0601] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-06-01`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-29.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[ThresholdDailyEVReport0601] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-05-29.json), [threshold_cycle_ev_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-29.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[SwingLifecycleBucketHealth0601] 스윙 lifecycle bucket source-only/complete-flow 상태 확인` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: SwingLogic`)
  - Source: [swing_lifecycle_decision_matrix_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-06-01.json), [swing_lifecycle_bucket_discovery_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-06-01.json), [swing_lifecycle_bucket_discovery_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-05-29.json)
  - 판정 기준: `source_contract_status=pass`, `ai_two_pass_review_status=parsed`, `state_counts`, `sim_auto_approved_count`, `flow_sim_auto_approved_count`, `complete_flow_count`, `complete_flow_rate`, `pending_future_quote_count`, `workorder_count`, `automation_handoff_gap_count`를 전일 baseline과 비교한다.
  - 금지: `source_only_keep_collecting`, pending future quote, sim/probe 표본, dry-run EV를 실주문 전환, full-live, provider/bot 변경, cap release 근거로 단독 사용하지 않는다.
  - 다음 액션: `keep_collecting`, `complete_flow_improved`, `source_quality_followup`, `handoff_gap_fail`, `sim_auto_candidate_review` 중 하나로 닫는다.

- [ ] `[SwingBucketParentReadiness0601] 스윙 버킷 parent 재구성 검토 조건 확인` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: SwingLogic`)
  - Source: [swing_lifecycle_bucket_discovery_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-06-01.json), [swing_lifecycle_decision_matrix_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-06-01.json), [threshold_cycle_ev_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-01.json)
  - 판정 기준: 현재 `source_only_keep_collecting` 중심 구조에서 complete lifecycle 표본이 parent EV 해석 가능한 수준으로 증가했는지, conflict child 후보가 parent 전체를 막는 대신 exclusion 후보로 분리 가능한지 확인한다.
  - 금지: 스윙 parent 재구성 검토를 scalping runtime bridge와 혼동하지 않는다. 스윙 dry-run/sim-only 체인은 `actual_order_submitted=false`, `broker_order_forbidden=true`, `runtime_effect=false` 상태를 유지한다.
  - 다음 액션: `not_ready_keep_collecting`, `ready_for_parent_review`, `conflict_child_exclusion_candidate`, `source_quality_blocked`, `needs_new_workorder` 중 하나로 닫는다.

- [ ] `[CodeImprovementWorkorderReview0601] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-29.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-29.md), [code_improvement_workorder_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-29.json)
  - 판정 기준: selected_order_count=108와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [x] `[MonitoringSamplerConsumerInventory0601] system_metric_sampler consumer_inventory_refreshed 및 2차 게이트 선행 정합성 기록` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 17:50~18:05`, `Track: ScalpingLogic`)
  - Source: [docs/proposals/src-engine-refactor-inventory.md](/home/ubuntu/KORStockScan/docs/proposals/src-engine-refactor-inventory.md), [1779532927562-sunny-canyon.md](/home/ubuntu/KORStockScan/.kilo/plans/1779532927562-sunny-canyon.md), [deploy/run_system_metric_sampler_cron.sh](/home/ubuntu/KORStockScan/deploy/run_system_metric_sampler_cron.sh), [src/engine/backfill_threshold_cycle_events.py](/home/ubuntu/KORStockScan/src/engine/backfill_threshold_cycle_events.py), [src/engine/error_detectors/cron_completion.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/cron_completion.py), [src/engine/monitoring/error_detector_coverage.py](/home/ubuntu/KORStockScan/src/engine/monitoring/error_detector_coverage.py), [src/tests/test_error_detector_coverage.py](/home/ubuntu/KORStockScan/src/tests/test_error_detector_coverage.py), [src/tests/test_engine_location_gate.py](/home/ubuntu/KORStockScan/src/tests/test_engine_location_gate.py)
  - 판정 기준:
    - `deploy/cron`, `error_detector`, `tests`, `backfill`, `runbook` 소비자 인벤토리 정리 완료.
    - old/new CLI smoke plan(현재 문서 반영)이 실행 가능한 형태로 준비됨.
    - `system_metric_sampler` canonical 정착 완료(`src.engine.monitoring.system_metric_sampler` 구현 + root wrapper 유지).
  - 실행 기록(현재): `src.engine.system_metric_sampler` smoke pass, `src.engine.monitoring.system_metric_sampler` smoke pass.
  - 판정: `implemented_with_wrapper`.
  - 금지: wrapper 제거/cron/job id/path semantics 변경.

- [x] `[MonitoringSamplerCanonicalMove0601] system_metric_sampler canonical 이동 구현` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [docs/proposals/src-engine-refactor-inventory.md](/home/ubuntu/KORStockScan/docs/proposals/src-engine-refactor-inventory.md), [1779532927562-sunny-canyon.md](/home/ubuntu/KORStockScan/.kilo/plans/1779532927562-sunny-canyon.md), [src/engine/system_metric_sampler.py](/home/ubuntu/KORStockScan/src/engine/system_metric_sampler.py), [src/engine/monitoring/system_metric_sampler.py](/home/ubuntu/KORStockScan/src/engine/monitoring/system_metric_sampler.py)
  - 판정 기준:
    - `src.engine.monitoring.system_metric_sampler`가 구현체로 동작.
    - `src.engine.system_metric_sampler`는 명시적 wrapper로 old import/CLI 호환 유지.
    - old/new CLI 모두 종료 코드 0.
  - 금지: cron/job id 출력 경로/runtime/path semantics 변경.

- [ ] `[HumanInterventionSummary0601] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 17:30~17:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-29.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[RuntimeApplyGapDirectiveReview0601] runtime apply gap Codex 작업지시 표면화 및 구현 여부 확인` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 17:45~18:00`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-05-29.json), [runtime_apply_gap_audit_2026-05-29.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-05-29.md), [runtime-apply-gap-audit-user-guide.md](/home/ubuntu/KORStockScan/docs/runtime-apply-gap-audit-user-guide.md)
  - 판정 기준: runtime apply gap audit의 Codex 작업지시 `FIX_PRODUCER_CONSUMER_HANDOFF`:lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_(block=producer_consumer_contract)를 구현 필요, 이미 해결, 설계 보류, reject로 분류한다.
  - 금지: 작업지시를 approval artifact나 즉시 runtime env 수정으로 해석하지 않는다. broker/order/provider/cap guard 우회와 장중 threshold mutation은 금지한다.
  - 다음 액션: `implement_now`, `already_implemented`, `defer_design`, `reject`, `needs_new_workorder` 중 하나로 닫고, 구현 시 테스트와 postclose verifier handoff를 같이 확인한다.

- [ ] `[SubmitDroughtAttributionTriage0601] submit drought 병목 추가 구현 필요성 보류/승격 판정` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:15`, `Track: ScalpingLogic`)
  - Source: [buy_funnel_sentinel_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-05-29.json), [threshold_cycle_ev_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-29.json), [missed_entry_counterfactual_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/missed_entry_counterfactual_2026-05-29.json), [pipeline_events_2026-06-01.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-01.jsonl)
  - 판정 기준: 신규 detector/report/provenance 구현 없이 기존 artifact만으로 `SUBMIT_DROUGHT_CRITICAL` 반복 여부, `latency_state_danger`, price guard, upstream AI WAIT/score block, broker submit/receipt 구간별 missed-upside 또는 avoided-loss를 분리한다.
  - 구현 승격 조건: `반복 병목 + positive missed-upside + 현재 artifact로 원인 분리가 불가능` 세 조건이 동시에 확인될 때만 `needs_new_workorder` 또는 `implement_now_candidate`로 닫는다.
  - 금지: 데이터 수집량 확대 자체를 목적으로 새 detector/report를 만들지 않는다. sim/probe/counterfactual EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다. threshold/order/provider/bot/env 변경, broker guard 우회, Telegram BUY alert 확대는 금지한다.
  - 다음 액션: `observe_existing_artifacts`, `hold_no_new_instrumentation`, `needs_new_workorder`, `implement_now_candidate`, `reject_more_granularity` 중 하나로 닫고, 구현 후보가 생기면 code-improvement workorder와 postclose verifier handoff로 넘긴다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->





## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
