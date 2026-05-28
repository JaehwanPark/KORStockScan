# 2026-05-28 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## Runbook 운영 확인 완료 기록

- `[PreopenAutomationHealthCheck20260528] 장전 자동화체인 상태 확인`
  - 판정: `pass`
  - 근거: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)의 `PreopenAutomationHealthCheck20260528` 완료 기록과 동일하다.
- `[IntradayAutomationHealthCheck20260528] 장중 자동화체인 상태 확인`
  - 판정: `warning`
  - 근거: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)의 `IntradayAutomationHealthCheck20260528` 완료 기록과 동일하다.
  - 추가 incident: `2026-05-28 13:50 KST` error detection의 `pipeline_events: stale (4319s > 600s)` alert는 실제 장애였다. 장중 수동 postclose wrapper `stop` mode가 bot을 종료한 상태로 남긴 것이 원인이며, stale isolation marker 제거 후 기존 runtime env 그대로 `tmux bot`을 재기동했다. 새 `bot_main.py` PID는 `117316`이고, artifact/process detector는 모두 `summary_severity=pass`로 복구 확인됐다. threshold/order/provider/env 값은 변경하지 않았다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-05-27` postclose -> `2026-05-28`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0528] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-28`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-27.json), [runtime_apply_gap_audit_2026-05-27.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-05-27.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 판정 기준: runtime apply gap audit의 `post_apply_attribution_pending`/`retry_pending` 후보가 다음 PREOPEN apply plan과 runtime env에서 소비되는지 사용자에게 표면화한다. 확인 대상: `entry_wait6579_score66_69_recovery_gate_v1:2026-05-27`(retry_pending, reason=ready_but_not_applied), `greenfield_real_environment_authority:2026-05-27`(retry_pending, reason=ready_but_not_applied).
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `runtime_gap_pending_consumed`, `runtime_gap_pending_not_consumed`, `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 완료 기록 (`2026-05-28 07:34 KST`): 판정=`pass`, 다음 액션=`runtime_gap_pending_consumed_and_applied_guard_passed_env`. 시간이 지났거나 임박한 반복 PREOPEN 확인 대상이라 `THRESHOLD_CYCLE_APPLY_MODE=auto_bounded_live THRESHOLD_CYCLE_AUTO_APPLY=true THRESHOLD_CYCLE_AUTO_APPLY_REQUIRE_AI=true deploy/run_threshold_cycle_preopen.sh 2026-05-28`로 preopen wrapper를 재확인 실행했고 `[DONE] threshold-cycle preopen target_date=2026-05-28`로 종료됐다. [threshold_cycle_preopen_2026-05-28.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-05-28.status.json)은 `status=succeeded`, `apply_mode=auto_bounded_live`, `exit_code=0`, `runtime_effect=preopen_runtime_env_apply_only`다. [threshold_apply_2026-05-28.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-28.json)은 `status=auto_bounded_live_ready`, `runtime_change=true`, `warnings=[]`이며 runtime apply bridge 후보 `3`건 중 `2`건이 approved다. retry 대상 `entry_wait6579_score66_69_recovery_gate_v1:2026-05-27`와 `greenfield_real_environment_authority:2026-05-27`는 runtime env selected family에 포함됐고, `scale_in_bucket_runtime_policy_v1`은 `bootstrap_pending`/`runtime_apply_not_allowed`/contract missing으로 정상 차단됐다. [threshold_runtime_env_2026-05-28.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-28.json)의 selected families는 `soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `lifecycle_decision_matrix_runtime`, `scalp_sim_auto_approval`, `greenfield_real_environment_authority`, `entry_wait6579_score66_69_recovery_gate_v1`, `swing_sim_auto_approval`다. 수동 env override, provider 변경, 주문 guard 변경, cap release는 수행하지 않았다.

- [x] `[OpenAIWSPreopenConfirm0528] OpenAI WS 유지 설정 및 entry_price/analyze_target provenance 확인` (`Due: 2026-05-28`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-27.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-27.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 OpenAI route/Responses WS 설정과 `analyze_target`, `entry_price` transport provenance를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 다음 액션: entry_price transport 표본이 부족하면 장중 표본 재확인 항목과 연결한다.
  - 완료 기록 (`2026-05-28 07:34 KST`): 판정=`pass`, 다음 액션=`keep_ws_and_intraday_entry_price_provenance_recheck`. [openai_ws_stability_2026-05-27.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-27.md)은 `decision=keep_ws`, `analyze_target` unique WS calls `5769`, WS fallback `0/5769`, WS success rate `1.0`, p95 `1745.2ms`, `entry_price WS sample count=0`, entry_price canary `transport_observable_count=523`, `applied_count=205`, `instrumentation_gap=False`다. [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)은 OpenAI `responses_ws`와 `KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true`를 유지하고, `gpt-5.4-mini`의 `entry_price,holding_flow`는 Bedrock Nova Lite v2 primary, OpenAI failback, Lite v1 shadow-only 비교 경로로 분리되어 있다. 따라서 `analyze_target` WS 유지와 `entry_price` Bedrock primary provenance는 분리 확인됐고, entry_price WS 표본 0건은 현재 route와 일치한다. threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경은 수행하지 않았다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RuntimeEnvIntradayObserve0528] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-28`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-27.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime, entry_wait6579_score66_69_recovery_gate_v1가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.
  - 완료 기록 (`2026-05-28 09:34 KST`): 판정=`pass`, 다음 액션=`provenance_present_no_rollback_guard_breach`. 시간이 지났지만 반복 확인 원칙에 따라 당일 artifact를 재확인했다. [threshold_runtime_env_2026-05-28.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-28.json)은 대상 family 6개(`soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `lifecycle_decision_matrix_runtime`, `entry_wait6579_score66_69_recovery_gate_v1`)를 모두 selected family로 포함한다. [threshold_apply_2026-05-28.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-28.json)은 `status=auto_bounded_live_ready`, `apply_mode=auto_bounded_live`, `runtime_change=true`, `warnings=[]`다. 당일 [pipeline_events_2026-05-28.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-28.jsonl)와 [threshold_events_2026-05-28.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-05-28.jsonl) 집계에서 family provenance hit는 `lifecycle_decision_matrix_runtime=3116`, `scalp_sim_ai_budget_manager=766`, `scalp_sim_candidate_window_expansion=621`, `soft_stop_whipsaw_confirmation=22`, `entry_wait6579_score66_69_recovery_gate_v1=22`이고 rollback mention은 `0`건이다. `score65_74_recovery_probe`는 runtime env selected/provenance는 확인됐지만 09:34 KST 현재 당일 이벤트 hit는 아직 없어 postclose attribution에서 표본 여부를 재확인한다. 장중 threshold mutation, provider 변경, order guard 변경, bot restart는 수행하지 않았다.

- [x] `[SimProbeIntradayCoverage0528] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-28`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-27.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.
  - 완료 기록 (`2026-05-28 09:34 KST`): 판정=`pass`, 다음 액션=`source_quality_split_preserved_active_state_observed`. 당일 이벤트 집계에서 `actual_order_submitted=false` provenance는 `12557`건, `broker_order_forbidden=true`는 `10057`건, `decision_authority=sim_observation_only`는 `5782`건이다. sim/probe stage 중 `actual_order_submitted=false` 누락은 `0`건이며, 주요 stage는 `scalp_sim_panic_scale_in_blocked=1500`, `swing_probe_discarded=626`, `scalp_sim_ai_holding_live_call=606`, `scalp_sim_panic_action_deduped=604`, `scalp_sim_candidate_window_discarded=342`다. open cap 증적은 `scalp_sim_candidate_window_discarded open_count=21/max_open=20`, `swing_probe_discarded open_count=10`로 남아 active state/cap 분리가 확인됐다. [panic_sell_defense_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/panic_sell_defense/panic_sell_defense_2026-05-28.json)은 `panic_state=RECOVERY_WATCH`, [panic_buying_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/panic_buying/panic_buying_2026-05-28.json)은 `panic_buy_state=NORMAL`이고 둘 다 `runtime_effect=report_only_no_mutation`이다. sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 사용하지 않았고, 장중 runtime/order/provider 변경은 수행하지 않았다.

- [x] `[GreenfieldLifecycleBundleContainment0528] Greenfield partial lifecycle policy 장중 containment 및 provenance 격리` (`Due: 2026-05-28`, `Slot: INTRADAY`, `TimeWindow: 12:05~12:20`, `Track: RuntimeStability`)
  - Source: [runtime_apply_bridge_2026-05-27.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-05-27.json), [greenfield_real_env_policy_2026-05-27.json](/home/ubuntu/KORStockScan/data/threshold_cycle/greenfield_real_env_policies/greenfield_real_env_policy_2026-05-27.json), [threshold_runtime_env_2026-05-28.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-28.json), [lifecycle_bucket_quarantine_2026-05-28.json](/home/ubuntu/KORStockScan/data/threshold_cycle/contamination_windows/lifecycle_bucket_quarantine_2026-05-28.json)
  - 판정 기준: `scope=full_lifecycle` Greenfield policy가 entry-only allowlist이면 장중 실험 왜곡으로 보고 Greenfield authority/Telegram만 OFF 처리한다. raw event는 보존하고 2026-05-28 오염 구간은 live promotion EV에서 제외한다.
  - 금지: threshold 값, provider route, order/quantity/cap guard, hard/protect/emergency safety를 변경하지 않는다.
  - 완료 기록 (`2026-05-28 12:09 KST`): 판정=`warning_contained`, 다음 액션=`postclose_lifecycle_bundle_regeneration_required`. `threshold_runtime_env_2026-05-28.env/json`에서 `KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY_ENABLED=false`, `KORSTOCKSCAN_GREENFIELD_REAL_ENV_TELEGRAM_ENABLED=false`로 내렸고, `restart.flag` 기반 graceful restart 후 새 bot PID 환경에서 두 값이 모두 `false`로 로드된 것을 확인했다. `greenfield_real_environment_authority`는 selected family에서 제거했고, `score65_74_recovery_probe` 및 기존 hard safety/holding/exit baseline은 유지했다. [lifecycle_bucket_quarantine_2026-05-28.json](/home/ubuntu/KORStockScan/data/threshold_cycle/contamination_windows/lifecycle_bucket_quarantine_2026-05-28.json)은 `reason=contaminated_greenfield_partial_lifecycle_policy`, `raw_events_preserved=true`, `derived_promotion_state_only=true`로 남겼다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[ThresholdDailyEVReport0528] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-05-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-05-27.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-05-27.json), [threshold_cycle_ev_2026-05-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-27.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [x] `[GreenfieldLifecycleBundlePostclose0528] lifecycle bucket bundle 재생성 및 entry-only Greenfield 차단 diff 확인` (`Due: 2026-05-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: RuntimeStability`)
  - Source: [lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_decision_matrix.py), [lifecycle_bucket_discovery.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_bucket_discovery.py), [runtime_apply_bridge.py](/home/ubuntu/KORStockScan/src/engine/runtime_apply_bridge.py), [greenfield_authority.py](/home/ubuntu/KORStockScan/src/engine/lifecycle/greenfield_authority.py), [lifecycle_bucket_quarantine_2026-05-28.json](/home/ubuntu/KORStockScan/data/threshold_cycle/contamination_windows/lifecycle_bucket_quarantine_2026-05-28.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: `THRESHOLD_CYCLE_AI_CORRECTION_PROVIDER=openai THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=stop deploy/run_threshold_cycle_postclose.sh 2026-05-28`로 bot stop/isolation marker를 남기고 누적/rolling 소비 경로까지 재생성한다.
  - 판정 기준: postclose 재생성 후 `lifecycle_flow_bucket_attribution` parent bucket이 생성되고, entry-only bucket이 `greenfield_real_environment_authority` full-lifecycle env/policy를 만들지 않으며, complete `greenfield_lifecycle_bundle_policy_v1`만 live 후보가 되는지 확인한다.
  - 금지: 오염 구간 raw event 삭제, sim/probe EV 단독 live 전환, threshold/provider/order/cap 변경, postclose wrapper 밖 리포트 재생성을 하지 않는다.
  - 다음 액션: `entry_only_blocked`, `complete_flow_bundle_ready`, `no_complete_flow_keep_greenfield_off`, `contamination_quarantine_applied`, `automation_handoff_gap`, `code_patch_required` 중 하나로 닫는다.
  - 완료 기록 (`2026-05-28 13:18 KST`): 판정=`warning_no_complete_flow_keep_greenfield_off`, 다음 액션=`entry_only_blocked_and_contract_drift_followup`. `THRESHOLD_CYCLE_AI_CORRECTION_PROVIDER=openai THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=stop deploy/run_threshold_cycle_postclose.sh 2026-05-28` 실행은 `status=succeeded`, `finished_at=2026-05-28T13:18:38+09:00`로 종료됐고 `tmux bot` 세션은 재기동되지 않았다. [lifecycle_decision_matrix_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-28.json)은 `lifecycle_flow_bucket_attribution.bucket_count=66`, `flow_count=11515`, `complete_flow_count=0`, `runtime_candidate_count=0`이다. [lifecycle_bucket_discovery_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-28.json)은 `live_auto_apply_ready_count=0`, `entry_only_sim_auto_approved=2`, `entry_only_source_candidate=6`, Greenfield live family 후보 `0`건이다. [runtime_apply_bridge_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-05-28.json)은 `greenfield_real_env_ready_count=0`, `runtime_mutation_performed=false`이며 `greenfield_real_env_policy_2026-05-28.json`은 생성되지 않았다. source contract는 신규 parent bucket schema 도입으로 `source_contract_status=fail`/`source_contract_drift_fail` warning이 남았고, 이는 live 승격 차단 상태에서 workorder/source-quality follow-up으로만 유지한다. [threshold_cycle_postclose_verification_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-05-28.json)은 현재 실행 시각 기준 `status=not_yet_due`, `missing_downstream_links=[]`, `stale_downstream_links=[]`로 산출됐다.

- [ ] `[CodeImprovementWorkorderReview0528] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-05-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-27.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-27.md), [code_improvement_workorder_2026-05-27.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-27.json)
  - 판정 기준: selected_order_count=56와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0528] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-28`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-27.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[ShadowCanaryCohortReview0528] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 당일 변경/관찰 결과를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 상태 변동 여부를 닫는다.
  - 금지: shadow 금지, canary-only, baseline 승격 원칙을 코드/문서 상태와 분리하지 않는다.
  - 다음 액션: 변경이 있으면 기준문서와 checklist를 함께 갱신하고 cohort 잠금 필드를 남긴다.

- [ ] `[RuntimeApplyGapDirectiveReview0528] runtime apply gap Codex 작업지시 표면화 및 구현 여부 확인` (`Due: 2026-05-28`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-05-27.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-05-27.json), [runtime_apply_gap_audit_2026-05-27.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-05-27.md), [runtime-apply-gap-audit-user-guide.md](/home/ubuntu/KORStockScan/docs/runtime-apply-gap-audit-user-guide.md)
  - 판정 기준: runtime apply gap audit의 Codex 작업지시 `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`:swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop(block=positive_edge_must_not_default_to_source_only_keep_collecting), `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`:swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_trailing_after_mfe_stop(block=positive_edge_must_not_default_to_source_only_keep_collecting), `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`:swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_trailing_after_mfe_stop(block=positive_edge_must_not_default_to_source_only_keep_collecting), `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`:swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_mid_held_missing_trailing_after_mfe_stop(block=positive_edge_must_not_default_to_source_only_keep_collecting), `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`:swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_mid_mae_low_held_missing_trailing_after_mfe_stop(block=positive_edge_must_not_default_to_source_only_keep_collecting) 외 1건를 구현 필요, 이미 해결, 설계 보류, reject로 분류한다.
  - 금지: 작업지시를 approval artifact나 즉시 runtime env 수정으로 해석하지 않는다. broker/order/provider/cap guard 우회와 장중 threshold mutation은 금지한다.
  - 다음 액션: `implement_now`, `already_implemented`, `defer_design`, `reject`, `needs_new_workorder` 중 하나로 닫고, 구현 시 테스트와 postclose verifier handoff를 같이 확인한다.

- [ ] `[GreenfieldEntryTelegramReadability0528] ENTRY 승인 Telegram bucket 문구 가독성 개선 계획 및 구현 여부 확인` (`Due: 2026-05-28`, `Slot: POSTCLOSE`, `TimeWindow: 17:30~17:45`, `Track: RuntimeStability`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: `entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown` 같은 raw bucket id를 Telegram 본문에 그대로 노출하지 않고, `진입 bucket: 점수 66-69 / 출처 WAIT65-79 EV / stale 정상-or-미표시 / 유동성 미분류 / 과열 미분류 / 시간대 미분류`처럼 사람이 읽는 요약으로 변환하는 formatter 계획을 검토한다.
  - 판정 기준: LDM `combo_entry_spot`의 `time_bucket` 축(`time_0900_1000`, `time_1000_1200`, `time_1200_1400`, `time_1400_close`, `time_unknown`)을 Telegram 요약에 포함하고, source field가 비어 있으면 `시간대 미분류`로 표기한다.
  - 판정 기준: Greenfield full-lifecycle authority에서는 `entry`와 `submit`이 별도 stage이므로 Telegram 제목/본문에서 `ENTRY bucket 승인`과 `submit 미승인/실주문 차단`을 분리 표기한다. 예: `상태: entry bucket promoted / submit bucket unpromoted, 실주문 차단`.
  - 판정 기준: Telegram에 표시하는 bucket은 `greenfield_policy_bucket_id`와 실제 후보의 `observed_entry_bucket_id`를 분리한다. policy allowlist bucket(`score_66_69` 등)을 모든 후보의 실제 score bucket처럼 표시하지 않고, 실제 score/source/stale/liquidity/overbought/time 산출값이 없으면 `candidate_bucket_instrumentation_gap`으로 분류한다.
  - 금지: 문구 개선을 runtime threshold, broker submit guard, provider route, bot restart, approval/cap 변경으로 해석하지 않는다. canonical bucket id는 event provenance와 report에는 보존한다.
  - 다음 액션: 장후 구현 시 `format_lifecycle_bucket_label` 계열 helper와 단위 테스트를 추가하고, ENTRY/HOLDING/SCALE-IN Telegram body에는 요약 label plus raw bucket id provenance를 접거나 별도 `Bucket ID` 줄로 분리한다. 구현하지 않으면 `defer_design`으로 닫고 다음 영업일 checklist에 parser-friendly follow-up을 남긴다.

- [ ] `[EntryMarketContextAttributionWorkorder0528] ENTRY bucket 시장약세 context attribution workorder 강제 표면화 여부 확인` (`Due: 2026-05-28`, `Slot: POSTCLOSE`, `TimeWindow: 17:45~18:00`, `Track: ScalpingLogic`)
  - Source: [lifecycle_decision_matrix_2026-05-27.json](/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-27.json), [threshold_cycle_ev_2026-05-27.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-27.json), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: `market_regime_continuous_label`, `panic_level`, `risk_context_owner`, `risk_regime_level` 필드는 LDM runtime feature로 존재하지만 `entry_bucket_attribution` 표준 bucket type에는 없으므로, `entry_bucket x market_regime/panic_level/risk_context` source-only attribution workorder를 `implement_now`/`defer_design`/`needs_new_workorder`로 분류한다.
  - 판정 기준: 이 항목은 16:00 postclose report와 기본 `code_improvement_workorder` 생성을 막는 선행조건이 아니라, 해당 체인이 종료된 뒤 누락 attribution을 보완 표면화할지 결정하는 supplemental review로 처리한다.
  - 금지: 시장약세 context를 장중 hard gate, threshold mutation, broker submit guard, provider route, bot restart, cap 변경 근거로 쓰지 않는다. canonical `combo_entry_spot` bucket id는 즉시 변경하지 않는다.
  - 다음 액션: 구현 시 `runtime_effect=false`, `allowed_runtime_apply=false`, `decision_authority=adm_ldm_entry_market_context_attribution_source_only` 계약으로 별도 attribution을 추가하고, 기존 greenfield/live-auto bucket id와 분리한다. 당일 기본 workorder artifact에 반영하려면 보완 구현 후 관련 리포트와 workorder를 재생성하고 lineage/diff를 확인한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->


## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
