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
- RunbookOps 처리 메모 (`2026-06-01 19:58 KST`, Project `PVTI_lAHOAXZuE84BUTcPzguLnZQ`): 시간이 지난 반복 PREOPEN 항목도 재확인 원칙에 따라 다시 실행했다. 판정은 `pass`이며, 근거와 다음 액션은 [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)의 `[PreopenAutomationHealthCheck20260601]` 완료 기록을 따른다.
- RunbookOps 처리 메모 (`2026-06-01 20:01 KST`, Project `PVTI_lAHOAXZuE84BUTcPzguLnaE`): 시간이 지난 반복 INTRADAY 항목도 재확인 원칙에 따라 다시 실행했다. 판정은 `warning`이며, 근거와 다음 액션은 [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)의 `[IntradayAutomationHealthCheck20260601]` 완료 기록과 추가 재확인 메모를 따른다.
- RunbookOps 처리 메모 (`2026-06-01 20:36 KST`, Project `PVTI_lAHOAXZuE84BUTcPzguLna8`): 시간이 지난 반복 POSTCLOSE 항목도 재확인 원칙에 따라 다시 실행했다. 판정은 `warning`, Tuning Chain Control State는 `YELLOW`이며, 근거와 다음 액션은 [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)의 `[PostcloseAutomationHealthCheck20260601]` 완료 기록을 따른다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0601] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-06-01`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-29.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 처리 결과(2026-06-01 KST 재확인): `partial_apply_with_blocked_families`.
  - 근거: [threshold_cycle_preopen_2026-06-01.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-06-01.status.json)은 `status=succeeded`, `apply_mode=auto_bounded_live`, `exit_code=0`, `runtime_effect=preopen_runtime_env_apply_only`다. [threshold_apply_2026-06-01.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-01.json)은 `status=auto_bounded_live_ready`, `runtime_change=true`, `warnings=[]`이며 source date는 `2026-05-29`다. [threshold_runtime_env_2026-06-01.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-01.json)은 selected family `soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `lifecycle_decision_matrix_runtime`, `scalp_sim_auto_approval`, `swing_sim_auto_approval`를 runtime env로 생성했다. bot PID `2696` 환경에는 `KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED=true`, `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`, `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`, `KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED=true`, `KORSTOCKSCAN_SCALP_SIM_AI_BUDGET_ENABLED=true`, `KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_ENABLED=true`가 실제 로드되어 있다. 반면 apply plan의 `runtime_apply_bridge.blocked`에는 `entry_wait6579_score66_69_recovery_gate_v1`가 `blocked_source_quality`, `runtime_apply_not_allowed`, `runtime_apply_bridge_auto_live_contract_missing`으로 남고 `scale_in_bucket_runtime_policy_v1`도 `bootstrap_pending`으로 차단되어 수동 env override 없이 blocked family로 분리해야 한다.
  - 다음 액션: 오늘 장중/장후 관찰은 적용된 PREOPEN env 축만 provenance와 rollback guard 기준으로 확인하고, bridge blocked family는 postclose bridge/source-quality 산출물에서만 재판정한다. 장중 threshold mutation, env 수동 override, approval artifact 없는 live bridge 강제 반영은 하지 않는다.

- [x] `[OpenAIWSPreopenConfirm0601] OpenAI WS 유지 설정 및 entry_price/analyze_target provenance 확인` (`Due: 2026-06-01`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-29.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-29.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 OpenAI route/Responses WS 설정과 `analyze_target`, `entry_price` transport provenance를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 다음 액션: entry_price transport 표본이 부족하면 장중 표본 재확인 항목과 연결한다.
  - 2026-05-30 operator override: `entry_price`는 Bedrock Qwen3 32B primary + Nova Lite v2 failback으로 확인한다. Nova Lite v2도 실패하면 OpenAI 3차 failback 없이 기존 defensive entry-price fallback으로 닫는다. `holding_flow`는 Nova Lite v2 primary + OpenAI failback을 유지한다.
  - 2026-05-31 implementation note: `entry_screen_v2`, `entry_price_v2`, `holding_flow_v2`, watching state-change refresh, entry-price refresh, and holding-flow state-change review flags are added as disabled-by-default implementation surfaces. They do not change provider route, threshold, order guard, quantity, or bot state unless a later checklist owner explicitly enables them.
  - 처리 결과(2026-06-01 KST 재확인): `keep_ws_confirmed_with_entry_price_bedrock_override`.
  - 근거: [openai_ws_stability_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-29.json)은 `decision=keep_ws`, `ws_summary.n=3422`, `endpoint_counts.analyze_target=3422`, `ws_http_fallback=0`, `ws_success_rate=1.0`, `entry_price_ws_sample_count=0`, `entry_price_canary_summary.instrumentation_gap=false`다. [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)는 `KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_POOL_SIZE=2`, `KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE=primary`, `KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_PRIMARY_FAMILY=qwen3_32b`, `KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_FAILBACK_FAMILY=lite_v2`, `KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_ENDPOINTS=holding_flow`를 export한다. bot PID `2696` 환경에도 같은 route/transport 설정이 로드되어 있다. 별도 provider provenance artifact인 [bedrock_nova_primary_provider_2026-05-29.jsonl](/home/ubuntu/KORStockScan/data/report/bedrock_nova_primary_provider/bedrock_nova_primary_provider_2026-05-29.jsonl)에는 `entry_price:*`와 `holding_flow:*` 요청이 다수 기록되며 `primary_provider=bedrock`, `endpoint_name=entry_price`, `decision_authority=runtime_primary_with_openai_failback`, `model_id=global.amazon.nova-2-lite-v1:0`가 남아 `entry_price`가 OpenAI WS가 아니라 Bedrock override 경로로 집계됐음을 확인했다.
  - 다음 액션: `analyze_target`은 OpenAI Responses WS 유지로 닫고, `entry_price`는 2026-05-30 operator override의 Bedrock primary/Nova Lite v2 failback provenance로 분리 관찰한다. `entry_price_ws_sample_count=0`은 WS 실패가 아니라 route override/표본 분리로 해석하며, provider transport 확인을 threshold/order guard/provider 추가 변경으로 연결하지 않는다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RuntimeEnvIntradayObserve0601] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-06-01`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-29.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.
  - 처리 결과(2026-06-01 KST 재확인): `partial_provenance_present_without_rollback_breach`.
  - 근거: [threshold_runtime_env_2026-06-01.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-01.json)의 selected family는 `soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `lifecycle_decision_matrix_runtime`, `scalp_sim_auto_approval`, `swing_sim_auto_approval`다. 당일 [pipeline_events_2026-06-01.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-01.jsonl) 재집계에서는 `soft_stop_whipsaw_confirmation=6`, `score65_74_recovery_probe=2`, `scalp_sim_candidate_window_expansion` field hit `1599`, `lifecycle_decision_matrix_runtime` context hit `2420`으로 provenance가 확인됐다. `scalp_sim_ai_budget_manager`는 family명 direct hit는 없지만 같은 source에서 `ai_budget*` field hit `384`와 `scalp_sim_ai_holding_deferred` stage가 남아 sim holding budget 경로 증적은 존재한다. 반면 direct family label로는 `0`건이라 family-name provenance는 incomplete로 분리한다. 같은 event 재집계에서 `rollback|revert|breach` mention은 `0`건이었다.
  - 다음 액션: `scalp_sim_ai_budget_manager`는 direct family label 미노출을 postclose attribution/source-quality follow-up으로 넘기고, 장중에는 현재 PREOPEN selected family를 유지한 채 threshold/env/provider/order 변경 없이 provenance 관찰만 계속한다.

- [x] `[SimProbeIntradayCoverage0601] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-06-01`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-29.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.
  - 처리 결과(2026-06-01 KST 재확인): `source_split_pass_with_minor_state_metadata_gap`.
  - 근거: 당일 [pipeline_events_2026-06-01.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-01.jsonl)에서 sim/probe-like stage 재집계 결과는 total `7830`, `actual_order_submitted=false` `7765`, `broker_order_forbidden=true` `6250`, probe-like `538`, `actual_order_submitted=true` `0`이다. `actual_order_submitted=false` 누락 사례 65건은 `swing_probe_state_restored`, `swing_probe_state_persisted`, `score65_74_recovery_probe_entry_unlocked`처럼 상태 복원/메타데이터 성격의 event이며 real submit provenance는 없었다. [scalp_live_simulator_state.json](/home/ubuntu/KORStockScan/data/runtime/scalp_live_simulator_state.json)와 [swing_intraday_probe_state.json](/home/ubuntu/KORStockScan/data/runtime/swing_intraday_probe_state.json) active state는 존재하지만, event 자체의 `status/state` 메타데이터는 open/closed count 집계에 충분히 일관적이지 않아 `open_like=0`, `closed_like=0`으로 남았다.
  - 중간점검(2026-06-01 10:58 KST): `sim_like_event_count=18642`, `sim_unique_records=181`, `sim_unique_stocks=111`, `actual_order_submitted=true=0`, `actual_order_submitted=false=18642`, `broker_order_forbidden=true=18361`로 실주문 분리는 유지됐다. `scalp_live_simulator_state.json` 기준 active simulated holding은 20건이다. 주요 sim stage는 `scalp_sim_panic_scale_in_blocked=4785`, `scalp_sim_panic_level1_partial_skipped_min_remaining=2911`, `scalp_sim_ai_holding_live_call=1263`, `sim_ai_critical_bypass=886`, `sim_ai_budget_exhausted=614`, `scalp_sim_buy_order_assumed_filled=181`이다. sim profit_rate 표본은 `n=13493`, 평균 `-0.1598`, 중앙값 `-0.37`, 범위 `-4.05~8.02`이며 peak_profit 표본은 `n=10410`, 평균 `0.6913`, 중앙값 `0.46`이다. lifecycle bucket match는 `matched=3250`, `no_match=3166`으로 장후 source-quality/lifecycle attribution 확인이 필요하다.
  - 다음 액션: sim/probe source split 자체는 pass로 유지하고, open/closed state 메타데이터 부족분은 source-quality follow-up으로만 넘긴다. 장중에는 sim/probe EV를 실주문 품질·전환 근거로 사용하지 않는다.

## 장후 체크리스트 (16:30~18:55)

- [x] `[ThresholdDailyEVReport0601] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-05-29.json), [threshold_cycle_ev_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-29.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 처리 결과(2026-06-01 KST): `sim_progress_no_live_bucket`.
  - 근거: [threshold_cycle_ev_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-01.json)은 `generated_at=2026-06-01T20:28:37+09:00`이며 real/sim/combined split을 분리했다. real sample `33`, avg `-0.4497`, sim sample `1074`, avg `-0.8811`, combined sample `1107`, avg `-0.8683`이고 combined authority는 `diagnostic_only_not_family_candidate_input`이다. [tuning_performance_control_tower_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-06-01.json)은 `primary_verdict=sim_progress_no_live_bucket`, `lifecycle_sim_auto_approved_count=95`, `lifecycle_live_auto_apply_ready_count=0`, `bridge_live_auto_apply_ready_count=0`, `source_freshness_status=pass`, `verifier_status=warning`이다.
  - 다음 액션: 다음 PREOPEN 입력으로는 기존 selected runtime env만 확인한다. 2026-06-01 daily EV의 sim/combined 값은 source-quality/관찰 입력으로 유지하고 broker execution 품질 또는 live 전환 근거로 쓰지 않는다.

- [x] `[SwingLifecycleBucketHealth0601] 스윙 lifecycle bucket source-only/complete-flow 상태 확인` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: SwingLogic`)
  - Source: [swing_lifecycle_decision_matrix_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-06-01.json), [swing_lifecycle_bucket_discovery_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-06-01.json), [swing_lifecycle_bucket_discovery_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-05-29.json)
  - 판정 기준: `source_contract_status=pass`, `ai_two_pass_review_status=parsed`, `state_counts`, `sim_auto_approved_count`, `flow_sim_auto_approved_count`, `complete_flow_count`, `complete_flow_rate`, `pending_future_quote_count`, `workorder_count`, `automation_handoff_gap_count`를 전일 baseline과 비교한다.
  - 금지: `source_only_keep_collecting`, pending future quote, sim/probe 표본, dry-run EV를 실주문 전환, full-live, provider/bot 변경, cap release 근거로 단독 사용하지 않는다.
  - 운영 보강(2026-06-01): 표준 postclose 완료 후 `deploy/run_swing_ldm_rolling_backfill_once.sh 2026-06-01` 일회성 실행으로 2026-05-18~2026-06-01 거래일 스윙 LDM/bucket/audit 산출물을 재정렬한다. 휴일/주말은 제외하며 runtime threshold/order/provider/bot 변경 권한은 없다.
  - 처리 결과(2026-06-01 KST): `keep_collecting_with_complete_flow_improved`.
  - 근거: [swing_lifecycle_decision_matrix_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-06-01.json)은 `status=pass`, `raw_swing_event_count=96819`, `ldm_consumed_event_count=91483`, `ldm_event_coverage_rate=0.944887`, `total_rows=95919`, `complete_flow_count=47`, `incomplete_flow_count=4314`, `sim_auto_candidate_count=0`, `workorder_count=8`이다. [swing_lifecycle_bucket_discovery_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-06-01.json)은 `status=pass`, `source_contract_status=pass`, `candidate_count=477`, `surfaced_candidate_count=477`, `source_only_keep_collecting_count=477`, `sim_auto_approved_count=0`, `pre_review_sim_auto_candidate_count=0`, `automation_handoff_gap_count=0`이다.
  - 다음 액션: 스윙 bucket은 source-only keep collecting으로 유지한다. `ai_two_pass_review_missing_source_only`는 sim-auto 후보가 0건인 상태의 warning이므로 다음 postclose에서 `pre_review_sim_auto_candidate_count > 0`으로 바뀔 때 AI review 필요성을 재판정한다.

- [x] `[SwingBucketParentReadiness0601] 스윙 버킷 parent 재구성 검토 조건 확인` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: SwingLogic`)
  - Source: [swing_lifecycle_bucket_discovery_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-06-01.json), [swing_lifecycle_decision_matrix_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-06-01.json), [threshold_cycle_ev_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-01.json)
  - 판정 기준: 현재 `source_only_keep_collecting` 중심 구조에서 complete lifecycle 표본이 parent EV 해석 가능한 수준으로 증가했는지, conflict child 후보가 parent 전체를 막는 대신 exclusion 후보로 분리 가능한지 확인한다.
  - 금지: 스윙 parent 재구성 검토를 scalping runtime bridge와 혼동하지 않는다. 스윙 dry-run/sim-only 체인은 `actual_order_submitted=false`, `broker_order_forbidden=true`, `runtime_effect=false` 상태를 유지한다.
  - 처리 결과(2026-06-01 KST): `not_ready_keep_collecting`.
  - 근거: 스윙 discovery는 `candidate_count=477`, `stage_only_source_only_count=431`, `state_counts.source_only_keep_collecting=477`, `selected_decision_counts.keep_bucket=431`, `selected_decision_counts.merge=46`이며 `sim_auto_approved_count=0`, `flow_sim_auto_approved_count=0`이다. complete flow는 `47`, complete flow rate는 `0.010777`로 parent EV authority를 만들기에는 아직 source-only 표본 중심이다.
  - 다음 액션: parent 재구성은 보류하고 complete flow와 label 축적을 더 모은다. conflict child/exclusion 후보가 sim/live 후보와 연결될 때만 다음 workorder 또는 parent review 항목으로 승격한다.

- [x] `[CodeImprovementWorkorderReview0601] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-01.json)
  - 판정 기준: selected_order_count=106와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `defer_evidence`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 처리 결과(2026-06-01 KST): `implement_now_items_present_user_instruction_required`.
  - 근거: [code_improvement_workorder_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-01.json)은 `source_order_count=131`, `selected_order_count=106`, `selected_decision_counts.implement_now=6`, `selected_decision_counts.attach_existing_family=100`, `selected_runtime_effect_false_count=106`, `selected_unimplemented_runtime_effect_false_count=6`이다. `implement_now` 6건은 `source_dimension_gap_resolution` 5건과 `runtime_instrumentation` 1건이며 모두 `runtime_effect=false`, `allowed_runtime_apply=false`다. `new_selected_order_count=0`, `removed_selected_order_count=0`, `decision_changed_order_count=0`으로 lineage drift는 없다.
  - 다음 액션: 자동 구현하지 않는다. 사용자가 별도 지시할 경우 `runtime_effect=false` 범위에서 6건만 2-pass 구현/재생성/review로 처리한다.
  - non-implement 재판정(2026-06-01 KST): `non_implement_routed_no_code_change`.
  - non-implement 근거: selected non-implement 100건은 모두 `attach_existing_family`이며 route는 `existing_family=91`, `performance_optimization_order=4`, `ai_review_coverage_review=1`, `parent_conflict_exclusion_review=1`, `positive_source_only_review=1`, `source_dimension_rollup=1`, `attach_existing_family=1`이다. 이는 기존 family/provenance/rollup evidence로 유지할 항목이고 신규 repo 구현 대상이 아니다. non-selected 25건은 `attach_existing_family=7`, `design_family_candidate=6`, `defer_evidence=9`, `reject=3`으로 재분류된다. `design_family_candidate`는 pattern/lab/source-only 설계 후보, `defer_evidence`는 표본·source-quality·수동검토 부족, `reject`는 현재 범위 밖 또는 기존 family로 충분한 항목이다. 전체 non-implement 항목은 `runtime_effect=false`, `allowed_runtime_apply=false` 범위이며 threshold/order/provider/bot/env 변경 권한이 없다.
  - non-implement 다음 액션: 당일 구현하지 않는다. selected `attach_existing_family` 100건은 다음 postclose 산출물의 evidence/provenance로 누적하고, non-selected `design_family_candidate` 6건은 LDM/discovery/runtime bridge 계약이 닫힐 때만 새 workorder 후보로 재승격한다. `defer_evidence` 9건은 표본 또는 source-quality 조건이 충족될 때 재검토하고, `reject` 3건은 새 owner/checklist 없이는 재오픈하지 않는다.

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

- [x] `[DashboardArchiveSameDayCron0601] dashboard DB archive 금요일 평문 잔존 방지 및 same-day 검증 압축 운영 반영` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 18:20~18:35`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [run_dashboard_db_archive_cron.sh](/home/ubuntu/KORStockScan/deploy/run_dashboard_db_archive_cron.sh), crontab `DASHBOARD_DB_ARCHIVE_2310`
  - 판정 기준: 서버는 주말에 꺼져 있으므로 주말 cron에 의존하지 않는다. 금요일 대형 `pipeline_events` raw/snapshot이 월요일 장중까지 평문으로 남지 않도록 평일 23:10 `dashboard_db_archive`를 same-day verified/backfilled 압축으로 전환한다.
  - 처리 결과(2026-06-01 KST): `same_day_verified_archive_cron_applied`.
  - 근거: 실제 crontab의 `DASHBOARD_DB_ARCHIVE_2310`를 `10 23 * * 1-5 /home/ubuntu/KORStockScan/deploy/run_dashboard_db_archive_cron.sh 0 ...`로 변경했다. `compress_db_backfilled_files --days 0 --date 2026-05-29 --dry-run`은 2026-05-29 raw와 threshold snapshot을 verified compression 대상으로 잡아 약 `2.2GB` 저장공간 회수 가능성을 보였다. `--days 0 --date 2026-06-01 --dry-run`은 2026-06-01 threshold snapshot을 포함해 verified snapshot을 압축 대상으로 잡지만, 2026-06-01 raw pipeline은 parquet 검증이 없으면 skip된다. 미검증 raw는 압축하지 않는 기존 guard를 유지한다.
  - 금지: 미검증 파일 강제 삭제, 당일 raw 수동 삭제, threshold/order/provider/bot 변경으로 해석하지 않는다.

- [x] `[HumanInterventionSummary0601] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 17:30~17:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-01.json), [runtime_approval_summary_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-06-01.json), [code_improvement_workorder_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-01.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.
  - 처리 결과(2026-06-01 KST): `approval_and_codex_action_split_recorded`.
  - 근거: [runtime_approval_summary_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-06-01.json)은 scalping selected auto-bounded-live `3`, swing requested `3`, swing approved `0`, swing blocked `14`, lifecycle live-auto ready `0`, swing lifecycle sim-auto approved `0`으로 닫았다. [tuning_performance_control_tower_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-06-01.json)은 `primary_verdict=sim_progress_no_live_bucket`, `bridge_live_auto_apply_ready_count=0`, `source_freshness_status=pass`, `verifier_status=warning`이다. [code_improvement_workorder_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-01.json)은 selected order `106`, `implement_now=6`, `selected_unimplemented_runtime_effect_false_count=6`이며 모두 source-quality/instrumentation 범위다. Project/Calendar 반영은 문서 수정 후 사용자 표준 sync 명령 대상이다.
  - 다음 액션: approval artifact 없는 env/provider/order/bot/threshold 변경은 하지 않는다. `implement_now=6`은 자동 해소하지 않고 사용자가 별도 Codex 구현 지시를 줄 때 runtime_effect=false 범위에서 처리한다. Project/Calendar 동기화는 문서 parser 검증 후 하단 표준 명령으로만 수행한다.

- [x] `[RuntimeApplyGapDirectiveReview0601] runtime apply gap Codex 작업지시 표면화 및 구현 여부 확인` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 17:45~18:00`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-01.json), [runtime_apply_gap_audit_2026-06-01.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-01.md), [runtime-apply-gap-audit-user-guide.md](/home/ubuntu/KORStockScan/docs/runtime-apply-gap-audit-user-guide.md)
  - 판정 기준: runtime apply gap audit의 Codex 작업지시 `FIX_PRODUCER_CONSUMER_HANDOFF`:lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_(block=producer_consumer_contract)를 구현 필요, 이미 해결, 설계 보류, reject로 분류한다.
  - 금지: 작업지시를 approval artifact나 즉시 runtime env 수정으로 해석하지 않는다. broker/order/provider/cap guard 우회와 장중 threshold mutation은 금지한다.
  - 다음 액션: `implement_now`, `already_implemented`, `defer_design`, `reject`, `needs_new_workorder` 중 하나로 닫고, 구현 시 테스트와 postclose verifier handoff를 같이 확인한다.
  - 처리 결과(2026-06-01 KST): `directives_surface_pass_no_runtime_apply`.
  - 근거: [runtime_apply_gap_audit_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-01.json)은 `status=pass`, `candidate_count=593`, `codex_directive_count=4`, `critical_failure_count=0`, `retry_queue_count=0`, `actionable_unknown_gap_count=5`, `source_dimension_gap_count=150`, `quiet_gap_count=287`, `quiet_gap_codex_directive_count=1`이다. [threshold_cycle_postclose_verification_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-01.json)은 final status `warning`이지만 missing/stale/source_generation warning은 없고, handoff warning은 스윙 AI two-pass source-only/missing fail-closed 2건으로 제한된다.
  - 다음 액션: runtime gap directive 4건은 Codex/source-quality 검토 queue로 유지한다. `runtime_apply_gap_audit` 결과만으로 runtime env, threshold, provider, broker/order guard, bot restart를 변경하지 않는다. 구현은 별도 사용자 지시가 있을 때 workorder와 verifier handoff를 같이 확인한다.

- [x] `[SubmitDroughtAttributionTriage0601] submit drought 병목 추가 구현 필요성 보류/승격 판정` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:15`, `Track: ScalpingLogic`)
  - Source: [buy_funnel_sentinel_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-06-01.json), [threshold_cycle_ev_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-01.json), [pipeline_events_2026-06-01.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-01.jsonl)
  - 판정 기준: 신규 detector/report/provenance 구현 없이 기존 artifact만으로 `SUBMIT_DROUGHT_CRITICAL` 반복 여부, `latency_state_danger`, price guard, upstream AI WAIT/score block, broker submit/receipt 구간별 missed-upside 또는 avoided-loss를 분리한다.
  - 구현 승격 조건: `반복 병목 + positive missed-upside + 현재 artifact로 원인 분리가 불가능` 세 조건이 동시에 확인될 때만 `needs_new_workorder` 또는 `implement_now_candidate`로 닫는다.
  - 금지: 데이터 수집량 확대 자체를 목적으로 새 detector/report를 만들지 않는다. sim/probe/counterfactual EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다. threshold/order/provider/bot/env 변경, broker guard 우회, Telegram BUY alert 확대는 금지한다.
  - 다음 액션: `observe_existing_artifacts`, `hold_no_new_instrumentation`, `needs_new_workorder`, `implement_now_candidate`, `reject_more_granularity` 중 하나로 닫고, 구현 후보가 생기면 code-improvement workorder와 postclose verifier handoff로 넘긴다.
  - 처리 결과(2026-06-01 KST): `observe_existing_artifacts_hold_no_new_instrumentation`.
  - 근거: [buy_funnel_sentinel_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-06-01.json)의 `entry_submit_drought_contract.primary=SUBMIT_DROUGHT_CRITICAL`, `critical=true`, `operator_action_required=false`이며 stage unique는 `ai_confirmed=146`, `budget_pass=83`, `latency_pass=32`, `order_bundle_submitted=17`이다. 같은 contract의 ratio는 submitted-to-ai `11.6%`, submitted-to-budget `20.5%`, budget-to-ai `56.8%`, latency-to-budget `38.6%`다. [threshold_cycle_ev_2026-06-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-01.json)의 entry funnel은 `latency_block_events=25222`, `latency_pass_events=173`, `recommended_action=reject`, `recommended_action_reason=recovery_count=0 below floor=2522`, `would_recovery_canary_events=0`, `counterfactual_joined_sample=0`, `broker_guard_bypass_candidates=0`이고 submit bucket attribution은 `submit_rows=382`, `bucket_count=70`, `contract_gap_count=0`, `workorder_count=0`, `runtime_candidate_count=0`이다.
  - 다음 액션: submit drought는 반복 병목으로 관찰하되, 현재 artifact만으로 병목 축이 분리되고 positive missed-upside/counterfactual 근거가 부족하므로 새 detector/report/provenance 구현은 보류한다. 다음 postclose에서도 `positive missed-upside + 원인 분리 불가`가 동시에 확인될 때만 신규 workorder로 승격한다.

- [x] `[LifecycleSourceDimensionFix0601] holding combo bucket의 not_applicable/start 차원 보존 여부 확인 및 보정` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 18:15~18:30`, `Track: ScalpingLogic`)
  - Source: [lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_decision_matrix.py), [test_lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/tests/test_lifecycle_decision_matrix.py), [lifecycle_bucket_discovery_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-29.json)
  - 판정 기준: `holding_started`와 같은 초기 lifecycle row에서 `profit/held/action` 차원이 helper와 동일한 `not_applicable_at_start` semantics를 유지하고, combo bucket이 helper를 우회해 `profit_unknown`으로 축약되지 않아야 한다.
  - 금지: 이 확인 결과를 threshold/provider/order/bot/env 변경 근거로 사용하지 않는다. source-quality와 lifecycle bucket attribution 범위로만 닫는다.
  - 처리 결과(2026-06-01 KST): `helper_aligned_bucket_key_fixed`.
  - 근거: `sim probe` 조사 중 `holding` 차원은 helper `_holding_profit_bucket`, `_holding_held_bucket`, `_holding_action_bucket`가 `profit_not_applicable_at_start`, `held_not_applicable_at_start`, `holding_action_not_applicable_at_start`를 정의하지만, `combo_holding_flow` bucket key는 profit만 direct `_numeric_band(..., unknown='profit_unknown')`를 사용해 helper semantics를 우회하고 있었다. 이를 helper 기반 `buckets['profit_band']`, `buckets['held_bucket']`, `buckets['holding_action']`로 정렬해 lifecycle bucket key가 source semantics를 그대로 보존하도록 수정했다.
  - 다음 액션: 다음 postclose `lifecycle_bucket_discovery`에서 `holding` 축의 `unknown_source_dimensions`가 감소하는지 관찰하고, 남는 건은 `entry` upstream `liquidity/overbought/stale` source 부재로 분리 추적한다.

- [x] `[LifecycleEntryDimensionFallback0601] entry combo bucket의 pre-submit guard 차원 fallback 정렬` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 18:30~18:45`, `Track: ScalpingLogic`)
  - Source: [lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_decision_matrix.py), [test_lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/tests/test_lifecycle_decision_matrix.py), [lifecycle_bucket_discovery_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-29.json)
  - 판정 기준: entry `combo_entry_spot`이 `liquidity_bucket` 또는 `overbought_bucket` 명시값이 비었거나 unknown인 경우에도 이미 수집된 `sim_pre_submit_*` guard action/reason/source 값을 사용해 canonical bucket을 만들 수 있어야 한다.
  - 금지: guard fallback은 source-quality attribution 보정이며 broker submit, threshold/env, provider, bot 상태를 변경하지 않는다.
  - 처리 결과(2026-06-01 KST): `entry_guard_fallback_aligned`.
  - 근거: `scalp_entry_action_decision_matrix`와 sim pre-submit 경로는 `sim_pre_submit_liquidity_guard_action/reason`, `sim_pre_submit_overbought_guard_action/reason`을 남기지만, `entry` bucket feature는 기존 `liquidity_bucket`/`overbought_bucket` 명시값만 읽어 unknown으로 남길 수 있었다. entry helper를 보강해 explicit non-unknown 값을 우선 사용하고, explicit 값이 없거나 unknown이면 기존 submit guard bucket 해석을 재사용하도록 정렬했다. lifecycle flow 조합에서도 entry row가 unknown이고 submit row에 guard 차원이 있는 경우 submit runtime feature를 fallback source로 전달해 `entry_bucket_id`가 실제 수집된 guard 차원을 반영하도록 보정했다.
  - 다음 액션: 다음 postclose 산출물에서 `entry` 축 `unknown_source_dimensions` 감소 여부를 확인한다. 그래도 남는 건은 실제 source 부재(`liquidity_value`, `overbought_risk_state`, quote freshness 없음)로 분리해 producer 보강 후보로 넘긴다.

- [x] `[LifecycleSourceDimensionGapAutomation0601] unknown source dimension gap 자동 표면화 체인 보강` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 18:45~19:00`, `Track: ScalpingLogic`)
  - Source: [lifecycle_bucket_discovery.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_bucket_discovery.py), [build_code_improvement_workorder.py](/home/ubuntu/KORStockScan/src/engine/build_code_improvement_workorder.py), [runtime_apply_gap_audit.py](/home/ubuntu/KORStockScan/src/engine/runtime_apply_gap_audit.py), [verify_threshold_cycle_postclose_chain.py](/home/ubuntu/KORStockScan/src/engine/verify_threshold_cycle_postclose_chain.py), [build_next_stage2_checklist.py](/home/ubuntu/KORStockScan/src/engine/build_next_stage2_checklist.py)
  - 판정 기준: `unknown_source_dimensions`와 `lifecycle_flow_incomplete_stage_contract`가 discovery metadata에만 머물지 않고 summary, workorder, runtime gap directive, verifier, next checklist 중 하나로 자동 표면화되어야 한다.
  - 금지: source-dimension gap 표면화를 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다. 장후 보고서 재생성은 표준 postclose 체인에서만 수행한다.
  - 처리 결과(2026-06-01 KST): `source_dimension_gap_surface_chain_implemented`.
  - 근거: `lifecycle_bucket_discovery`에 `source_dimension_gap_summary`를 추가해 gap/stage/bucket/state/resolution/missing key를 집계하고, `resolve_unknown_source_dimensions`/`emit_or_backfill_source_field`는 actionable gap으로 분리했다. `build_code_improvement_workorder`는 actionable gap을 `source_dimension_gap_resolution` workorder로 만들고 rollup gap은 `attach_existing_family` evidence로 남긴다. `runtime_apply_gap_audit`는 `RESOLVE_SOURCE_DIMENSION_GAP` directive를 생성하며, verifier는 actionable gap이 workorder로 표면화되지 않으면 warning 또는 sim/live 후보의 경우 fail로 닫는다. next checklist builder는 runtime gap directive가 0이어도 actionable summary가 있으면 parser-friendly POSTCLOSE 확인 항목을 생성한다.
  - 자체 코드리뷰/보완: `source_dimension_gap_summary.actionable_unknown_gap_count`가 있어도 `surfaced_candidates` 축약 범위 밖에 있으면 workorder/directive/verifier가 놓칠 수 있는 결함을 확인해 summary 자체를 소비하도록 보강했다. 같은 후보가 ledger와 summary 양쪽에서 들어올 때 `RESOLVE_SOURCE_DIMENSION_GAP` directive가 중복될 수 있어 최종 directive dedupe를 추가했다.
  - 테스트/검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_apply_gap_audit.py src/tests/test_verify_threshold_cycle_postclose_chain.py src/tests/test_build_next_stage2_checklist.py` 통과(141 passed). `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/lifecycle_bucket_discovery.py src/engine/build_code_improvement_workorder.py src/engine/runtime_apply_gap_audit.py src/engine/verify_threshold_cycle_postclose_chain.py src/engine/build_next_stage2_checklist.py` 통과. `git diff --check` 통과.
  - 다음 액션: 2026-06-01 장후 표준 postclose 보고서 재생성 후 `source_dimension_gap_summary.actionable_unknown_gap_count`, `RESOLVE_SOURCE_DIMENSION_GAP`, `lifecycle_source_dimension_gap_handoff_missing` 여부를 확인한다.

- [x] `[LifecycleQuietGapAutomation0601] 조용한 source-only/warning gap 자동 표면화 체인 보강` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 19:00~19:15`, `Track: ScalpingLogic`)
  - Source: [lifecycle_bucket_discovery.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_bucket_discovery.py), [build_code_improvement_workorder.py](/home/ubuntu/KORStockScan/src/engine/build_code_improvement_workorder.py), [runtime_apply_gap_audit.py](/home/ubuntu/KORStockScan/src/engine/runtime_apply_gap_audit.py), [verify_threshold_cycle_postclose_chain.py](/home/ubuntu/KORStockScan/src/engine/verify_threshold_cycle_postclose_chain.py), [build_next_stage2_checklist.py](/home/ubuntu/KORStockScan/src/engine/build_next_stage2_checklist.py)
  - 판정 기준: `parent conflict/exclusion child`, positive `source_only_keep_collecting`, `observation_source_quality_audit` warning, parsed-but-low-coverage AI review가 discovery/workorder/runtime audit/verifier/checklist 중 하나로 자동 표면화되어야 한다.
  - 금지: quiet gap 표면화를 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다. 2026-05-29 산출물은 재생성하지 않고 2026-06-01 장후 표준 postclose 체인에서 새 로직을 확인한다.
  - 처리 결과(2026-06-01 KST): `quiet_gap_surface_chain_implemented`.
  - 근거: `lifecycle_bucket_discovery`에 `quiet_gap_summary`를 추가해 conflict/exclusion child, positive source-only, absorbed parent-policy evidence, AI shard coverage gap을 `runtime_effect=false`, `allowed_runtime_apply=false`, `decision_authority=source_quality_gap_discovery`로 집계한다. `build_code_improvement_workorder`는 quiet gap을 `lifecycle_bucket_discovery_quiet_gap_rollup` order로 만들고 `attach_existing_family`로 분류한다. allowlist 밖 `observation_source_quality_audit` warning도 `order_observation_source_quality_warning_rollup`으로 최소 표면화한다. `runtime_apply_gap_audit`는 quiet gap count/rollup/directive count를 summary에 남기고 missing rollup이면 review directive를 생성한다. verifier는 quiet gap handoff 누락을 warning으로, sim/live 연결 quiet gap 누락을 fail로 닫는다. next checklist builder는 runtime directive가 없어도 `LifecycleQuietGapReview{MMDD}` POSTCLOSE checkbox를 만든다.
  - 자체 코드리뷰/보완: quiet gap rollup order의 `title` 누락을 확인해 보완했다. verifier status는 기존 AI follow-up warning 전체를 warning status로 승격하지 않고, handoff 누락 warning에 한해 status warning으로 올리도록 범위를 제한했다. 추가 리뷰에서 quiet gap rollup이 한 종류만 있어도 전체 handoff 완료로 오판할 수 있는 partial handoff 결함을 확인해, gap type별 required rollup order와 missing order id를 runtime audit directive/verifier에 남기도록 보완했다. 중복 directive는 기존 dedupe 경로로 닫는다.
  - 테스트/검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_apply_gap_audit.py src/tests/test_verify_threshold_cycle_postclose_chain.py src/tests/test_build_next_stage2_checklist.py` 통과(153 passed).
  - 다음 액션: 2026-06-01 장후 표준 postclose 보고서 재생성 후 `quiet_gap_summary.quiet_gap_count`, `quiet_gap_codex_directive_count`, `lifecycle_quiet_gap_handoff_missing`, `LifecycleQuietGapReview0602` 생성 여부를 확인한다.

- [x] `[SwingSimTuningHandoffAIRouteFix0601] 스윙 SIM 튜닝 handoff 및 postclose AI review route 고정 구현` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 19:15~19:35`, `Track: SwingLogic`)
  - Source: [swing_lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/swing_lifecycle_decision_matrix.py), [swing_lifecycle_bucket_discovery.py](/home/ubuntu/KORStockScan/src/engine/swing_lifecycle_bucket_discovery.py), [runtime_apply_gap_audit.py](/home/ubuntu/KORStockScan/src/engine/runtime_apply_gap_audit.py), [verify_threshold_cycle_postclose_chain.py](/home/ubuntu/KORStockScan/src/engine/verify_threshold_cycle_postclose_chain.py), [postclose_review_config.py](/home/ubuntu/KORStockScan/src/engine/ai/postclose_review_config.py), [postclose_structured_review_provider.py](/home/ubuntu/KORStockScan/src/engine/ai/postclose_structured_review_provider.py)
  - 판정 기준: swing SIM 관측 이벤트가 LDM/bucket discovery/runtime gap audit/verifier로 candidate 단위 전달되고, postclose AI review는 `gpt-5.4`, `reasoning_effort=medium`, OpenAI primary, Bedrock Qwen3 failback, Gemini 미사용으로 닫힌다.
  - 금지: 이 구현은 source-quality/postclose review/workorder 표면화 보완이며 runtime threshold, 주문, live provider route, bot restart, cap release를 변경하지 않는다.
  - 처리 결과(2026-06-01 KST): `implemented_source_only_handoff_and_ai_route_fixed`.
  - 근거: Swing LDM이 `swing_sim_buy_order_assumed_filled`, `swing_sim_holding_started`, `swing_sim_sell_order_assumed_filled`, `swing_sim_scale_in_order_assumed_filled`를 source-only lifecycle rows로 소비하도록 확장했다. holding/exit attribution key는 lifecycle flow child bucket key와 동일한 helper를 사용하도록 맞췄다. `runtime_apply_gap_audit`는 swing discovery 후보를 `family` 단위로 병합하지 않고 `candidate_id` 단위로 보존한다. scalping lifecycle bucket discovery의 기존 공통 AI config/직접 OpenAI 호출 계약은 유지하고, `runtime_apply_gap_audit`와 swing bucket discovery 경로에서만 OpenAI primary + Bedrock Qwen3 failback을 국소 고정했다. `runtime_apply_gap_audit`는 bounded shard별 OpenAI 실패/parse reject/schema mismatch를 같은 shard의 Bedrock Qwen3 failback으로만 처리하며 full-context retry를 하지 않는다.
  - 자체 코드리뷰/보완: self-review에서 공통 postclose AI config 변경과 `lifecycle_bucket_discovery` 호출 경로 변경이 scalping sim LDM review contract에 영향을 줄 수 있음을 확인해 기존 default provider mapping, source-only reasoning, OpenAI timeout path를 복구했다. runtime gap audit의 Gemini compatibility wrapper와 Gemini-named shard-size 의존은 제거했고, swing bucket discovery는 provider override를 로컬 config로 제한했다. 추가 리뷰에서 `runtime_apply_gap_audit`가 Swing LDM 후보를 직접 ledger로 소비하지 않는 점과 verifier가 matrix/discovery 후보 ID 연속성 붕괴를 합집합 검증으로 놓칠 수 있음을 확인해 보완했다.
  - 테스트/검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py` 통과(72 passed). `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_gap_audit.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py` 통과(165 passed). `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_lifecycle_decision_matrix.py src/tests/test_swing_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_gap_audit.py src/tests/test_verify_threshold_cycle_postclose_chain.py src/tests/test_threshold_cycle_ev_report.py src/tests/test_runtime_approval_summary.py src/tests/test_postclose_ai_review_config.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py` 통과(242 passed). `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/runtime_apply_gap_audit.py src/engine/verify_threshold_cycle_postclose_chain.py src/engine/swing_lifecycle_decision_matrix.py src/engine/swing_lifecycle_bucket_discovery.py src/engine/threshold_cycle_ev_report.py src/engine/runtime_approval_summary.py src/engine/build_code_improvement_workorder.py` 통과.
  - 다음 액션: 2026-06-01 장후 표준 postclose 체인에서 `raw_swing_event_count`, `ldm_consumed_event_count`, `ldm_event_coverage_rate`, `candidate_route_ledger`의 swing candidate 보존, `ai_reasoning_review.provider_status.primary_provider=openai`, `failback_provider=bedrock_qwen3`, Gemini provider 미사용/disabled 여부를 확인한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 수동 롤아웃 체크리스트: 진입/보유/청산 AI input v2

- [x] `[AIInputV2RolloutMasterGate0601] entry/price/holding AI input v2 단계별 rollout 계획과 일자별 체크리스트 연결 확인` (`Due: 2026-06-01`, `Slot: POSTCLOSE`, `TimeWindow: 18:15~18:30`, `Track: AIPrompt`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-06-02-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-06-02-stage2-todo-checklist.md), [2026-06-03-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-06-03-stage2-todo-checklist.md), [2026-06-04-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-06-04-stage2-todo-checklist.md), [2026-06-05-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-06-05-stage2-todo-checklist.md)
  - 계획 요약: Stage 1 disabled runtime surface 확인, Stage 2 offline replay report, Stage 3 `entry_price_v2` report-only comparison audit, Stage 4 `entry_price` runtime input 전환 go/no-go, Stage 5 `holding_flow`/`analyze_target` 순차 후보화.
  - 판정 기준: 각 stage가 날짜별 checklist에 `Due`, `Slot`, `TimeWindow`, `Track`, Source, IN/OUT scope, acceptance, go/no-go를 가진 parser-friendly checkbox로 존재한다.
  - 금지: 이 항목은 문서/계획 owner만 닫는다. provider route, threshold, broker/order guard, order quantity, bot restart, hard/protect/emergency stop을 변경하지 않는다.
  - 다음 액션: 누락된 stage가 있으면 해당 날짜 checklist에 추가하고 parser 검증을 다시 실행한다. 모든 stage가 존재하면 `rollout_schedule_registered`로 닫는다.
  - 처리 결과(2026-06-01 KST): `rollout_schedule_registered`.
  - 근거: [2026-06-02-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-06-02-stage2-todo-checklist.md)는 Stage 1 disabled surface 확인과 Stage 2 offline replay case plan을 가진다. [2026-06-03-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-06-03-stage2-todo-checklist.md)는 Stage 2 offline replay report와 Stage 3 readiness를 가진다. [2026-06-04-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-06-04-stage2-todo-checklist.md)는 Stage 3 report-only audit와 Stage 4 runtime switch decision을 가진다. [2026-06-05-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-06-05-stage2-todo-checklist.md)는 Stage 4 post-apply attribution과 Stage 5 holding/entry screen sequential decision을 가진다. 각 항목은 `Due`, `Slot`, `TimeWindow`, `Track`, Source, IN/OUT scope, acceptance, go/no-go를 parser-friendly checkbox로 갖는다.
  - 다음 액션: 2026-06-02 Stage 1/2 체크부터 순차 진행한다. rollout plan 확인 자체로 provider route, threshold, broker/order guard, order quantity, bot restart, hard/protect/emergency stop을 변경하지 않는다.





## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-06-01 15:47:24`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-06-01.md`
- `Trade Review`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
