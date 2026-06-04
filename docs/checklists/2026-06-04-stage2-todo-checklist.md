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

- [x] `[SwingPreFinalAutoAndFinalApprovalPreopen0604] 스윙 pre-final auto state 및 final approval artifact 확인` (`Due: 2026-06-04`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-06-02.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-02.json), [threshold_cycle_ev_2026-06-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-02.json)
  - 판정 기준: pre-final은 parsed AI Tier2 auto state가 있어야 하고, final-stage는 사용자 승인 artifact가 있어야 한다.
  - 금지: 스윙 full-live 전환, cap release, provider/bot 변경, hard-safety 완화를 pre-final auto state로 처리하지 않는다.
  - 다음 액션: `pre_final_auto_selected`, `final_approval_artifact_present`, `blocked_by_policy` 중 하나로 닫는다.
  - 처리 결과 (`2026-06-04 07:58 KST`, Project `PVTI_lAHOAXZuE84BUTcPzguemtQ`): 판정 `pass / blocked_no_final_approval_required`. [swing_runtime_approval_2026-06-02.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-02.json)은 `summary={'requested': 0, 'blocked': 12, 'approved': 0, 'runtime_change': false}`이고 `final_user_approval_boundary=full_live_only`, `runtime_apply_requires_user_approval_artifact=false`, `final_full_live_requires_user_approval=true` 계약을 유지한다. 12개 blocked request는 `severe_downside_guard`와 일부 `runtime_family_guard_missing` 등으로 닫혀 2026-06-04 PREOPEN full-live/final approval artifact 소비 대상이 없다. 다음 액션은 `blocked_by_policy`로 보관하고 스윙 full-live 전환, cap release, provider/bot 변경, hard/protect/emergency safety 완화는 열지 않는다.

- [x] `[ThresholdEnvAutoApplyPreopen0604] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-06-04`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-02.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 처리 결과 (`2026-06-04 07:58 KST`, Project `PVTI_lAHOAXZuE84BUTcPzguemu4`): 판정 `pass / applied_guard_passed_env`. [threshold_cycle_preopen_2026-06-04.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-06-04.status.json)은 `status=succeeded`, `exit_code=0`, `runtime_effect=preopen_runtime_env_apply_only`이고, [threshold_apply_2026-06-04.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-04.json)은 `source_date=2026-06-02`, `status=auto_bounded_live_ready`, `apply_mode=auto_bounded_live`, `runtime_change=true`, `warnings=[]`다. [threshold_runtime_env_2026-06-04.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-04.json)은 selected families `bad_entry_refined_canary`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `lifecycle_decision_matrix_runtime`, `scalp_sim_auto_approval`, `swing_sim_auto_approval`를 남긴다. bridge live-auto 후보 `entry_wait6579_score66_69_recovery_gate_v1`, `scale_in_bucket_runtime_policy_v1`는 `blocked_source_quality`, `bootstrap_pending`, `runtime_apply_not_allowed`, `runtime_apply_bridge_auto_live_contract_missing`으로 차단되어 수동 env override 없이 보관했다. `tmux bot` 세션과 `bot_main.py` PID는 살아 있어 `run_bot.sh` runtime env 소비 상태도 확인됐다.

- [x] `[AITransportPreopenConfirm0604] AI transport 유지 설정 및 entry_price/analyze_target provenance 확인` (`Due: 2026-06-04`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-06-02.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-06-02.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 endpoint별 transport를 확인한다. `analyze_target`은 OpenAI Responses WS, `entry_price`는 Bedrock Qwen3 32B primary -> Nova Lite v2 failback provenance를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 다음 액션: entry_price Bedrock provenance 또는 analyze_target WS 표본이 부족하면 장중 표본 재확인 항목과 연결한다.
  - 처리 결과 (`2026-06-04 07:58 KST`, Project `PVTI_lAHOAXZuE84BUTcPzguemw0`): 판정 `pass / transport_provenance_split_confirmed`. [openai_ws_stability_2026-06-02.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-06-02.md)은 `decision=keep_ws`, endpoint counts `{'analyze_target': 5994}`, `WS fallback=0/5994`, `WS success rate=1.0`로 `analyze_target` OpenAI Responses WS 유지를 확인한다. 같은 report는 `entry_price_ws_sample_count=0`을 OpenAI WS 실패가 아니라 표본 부족/비WS route로 분리하고, entry_price canary `transport_observable_count=479`, `instrumentation_gap=false`를 남긴다. [bedrock_nova_primary_provider_2026-06-02.jsonl](/home/ubuntu/KORStockScan/data/report/bedrock_nova_primary_provider/bedrock_nova_primary_provider_2026-06-02.jsonl)은 `entry_price` 1412건이 `primary_provider=bedrock`, `bedrock_primary_family=qwen3_32b`, `decision_authority=runtime_primary_with_bedrock_failback_defensive_close`로 기록되어 entry_price Qwen3 32B primary provenance를 확인했다. 다음 액션은 장중 표본에서 failback 발생 여부만 관찰하고 provider route, threshold, 주문가/수량 guard, 스윙 dry-run guard는 변경하지 않는 것이다.

- [x] `[PreopenAutomationHealthCheck20260604] 장전 자동화체인 상태 확인` (`Due: 2026-06-04`, `Slot: PREOPEN`, `TimeWindow: 08:00~09:00`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정: `pass`
  - 처리 결과 (`2026-06-04 07:58 KST`, Project `PVTI_lAHOAXZuE84BUTcPzguoq6k`): 장전 반복 확인은 시간창 경과 후에도 실행했고 scanner, threshold preopen wrapper/status/apply/runtime env, tmux bot session, swing approval boundary, AI transport provenance를 모두 확인했다. Tuning Chain Control State는 `GREEN`, blocked_stage는 `-`다. 세부 근거와 다음 액션은 [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)의 `PreopenAutomationHealthCheck20260604` 완료 기록에 남겼다. 이 확인은 threshold/order/provider/bot/env/cap 변경 권한을 열지 않는다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RuntimeEnvIntradayObserve0604] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-06-04`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-02.json)
  - 판정 기준: selected_families=score65_74_recovery_probe, bad_entry_refined_canary, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime, swing_one_share_real_canary_phase0, swing_market_regime_sensitivity가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.
  - 처리 결과 (`2026-06-04 09:37 KST`, Project `PVTI_lAHOAXZuE84BUTcPzguemx0`): 판정 `pass / current_selected_env_provenance_present`. [threshold_runtime_env_2026-06-04.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-04.json) 기준 current selected families는 `bad_entry_refined_canary`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `lifecycle_decision_matrix_runtime`, `scalp_sim_auto_approval`, `swing_sim_auto_approval`다. [pipeline_events_2026-06-04.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-04.jsonl)은 09:37 기준 `lifecycle_decision_matrix_runtime` 1833건, `scalp_sim_auto_approval` 1478건, `scalp_sim_candidate_window_expansion` 1240건, `bad_entry_refined_canary` 1128건을 포함한다. [threshold_events_2026-06-04.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-06-04.jsonl)은 `scalp_sim_ai_budget_manager` 798건, `lifecycle_decision_matrix_runtime` 6건을 family field로 남긴다. checklist의 `score65_74_recovery_probe`, `swing_one_share_real_canary_phase0`, `swing_market_regime_sensitivity` 기대값은 current 2026-06-04 runtime env selected list에는 없으므로 missing runtime breach가 아니라 stale expected list로 분리한다. rollback/safety breach는 확인되지 않았고, runtime threshold mutation은 수행하지 않았다.

- [x] `[AITransportIntradaySample0604] AI transport 장중 표본 및 fallback/fail-closed 재확인` (`Due: 2026-06-04`, `Slot: INTRADAY`, `TimeWindow: 09:20~09:35`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-06-02.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-06-02.md)
  - 판정 기준: `analyze_target` OpenAI WS latency/fallback과 `entry_price` Bedrock transport metadata 누락 여부를 별도 표본으로 확인한다.
  - 금지: entry_price 표본 0건 또는 instrumentation gap을 OpenAI WS runtime 효과 0으로 해석하지 않고, Bedrock provenance 확인을 provider route 변경 근거로 쓰지 않는다.
  - 다음 액션: 표본 부족이면 postclose provenance 보강 workorder로 분리한다.
  - 처리 결과 (`2026-06-04 09:37 KST`, Project `PVTI_lAHOAXZuE84BUTcPzguemy4`): 판정 `pass / intraday_transport_sample_present`. [bedrock_nova_primary_provider_2026-06-04.jsonl](/home/ubuntu/KORStockScan/data/report/bedrock_nova_primary_provider/bedrock_nova_primary_provider_2026-06-04.jsonl)은 09:37 기준 `entry_price` Bedrock Qwen3 32B 72건과 `holding_flow` Bedrock 86건을 기록했고, `parse_ok=True` 158건, `bedrock_failback_used=False` 158건, 최대 latency 4366ms다. [pipeline_events_2026-06-04.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-04.jsonl)은 WS 관련 event text 6400건을 포함한다. Bedrock provenance는 provider route 변경 근거가 아니라 endpoint별 transport 확인으로만 사용했고, threshold 값/주문가/수량 guard/스윙 dry-run guard 변경은 수행하지 않았다.

- [x] `[SimProbeIntradayCoverage0604] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-06-04`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-06-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-02.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.
  - 처리 결과 (`2026-06-04 09:37 KST`, Project `PVTI_lAHOAXZuE84BUTcPzguemzs`): 판정 `pass / sim_probe_authority_split_preserved`. [pipeline_events_2026-06-04.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-04.jsonl)은 09:37 기준 `actual_order_submitted=False` 6366건, `broker_order_forbidden=True` 5366건, `decision_authority=sim_observation_only` 3252건을 포함하고 `actual_order_submitted=True` 표본은 없었다. [threshold_events_2026-06-04.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-06-04.jsonl)도 `actual_order_submitted=False` 6325건, `broker_order_forbidden=True` 5335건, `decision_authority=sim_observation_only` 3252건을 남긴다. 주요 sim/probe stages는 `latency_block`, `scalp_sim_panic_scale_in_blocked`, `swing_probe_discarded`, `scalp_sim_ai_holding_live_call`, `scalp_sim_buy_order_assumed_filled` 등이며 real execution 품질이나 live 전환 근거로 사용하지 않는다.

- [x] `[IntradayAutomationHealthCheck20260604] 장중 자동화체인 상태 확인` (`Due: 2026-06-04`, `Slot: INTRADAY`, `TimeWindow: 09:05~15:30`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정: `not_yet_due / partial_intraday_pass`
  - 처리 결과 (`2026-06-04 09:37 KST`, Project `PVTI_lAHOAXZuE84BUTcPzguoq7k`): 장중 자동화체인 확인은 09:37 KST 현재 가능한 범위에서 실행했다. BUY Funnel Sentinel은 09:15~09:35 반복 `[DONE]` marker와 `SUBMIT_DROUGHT_CRITICAL`, `PRICE_GUARD_DROUGHT`, `LATENCY_DROUGHT`, `UPSTREAM_AI_THRESHOLD`를 남겼고 followup은 `entry_submit_drought_auto_workorder`, `operator_action_required=false`, `runtime_effect=auto_workorder_no_intraday_mutation`이다. HOLD/EXIT Sentinel은 09:10~09:35 반복 `[DONE]` marker와 `HOLD_DEFER_DANGER`, `AI_HOLDING_OPS`, `runtime_effect=report_only_no_mutation`을 남겼다. panic sell/buying은 모두 `NORMAL`, error detector는 `summary_severity=pass`다. 전체 09:05~15:30 창은 아직 진행 중이므로 최종 장중 RunbookOps 판정은 아래 후속 recheck에서 닫는다. 이 확인은 threshold/order/provider/bot/env/cap 변경 권한을 열지 않는다.

- [ ] `[IntradayAutomationHealthFinalRecheck0604] 장중 자동화체인 15:30 마감 재확인` (`Due: 2026-06-04`, `Slot: INTRADAY`, `TimeWindow: 15:30~15:40`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 09:37 partial pass 이후 15:30까지 sentinel, panic, error detector, pipeline/threshold event append, sim/probe authority split이 유지됐는지 확인한다.
  - 금지: sentinel/error detector/panic 결과로 runtime threshold, provider route, 주문, bot restart를 변경하지 않는다.
  - 다음 액션: `pass`, `warning`, `fail` 중 하나로 닫고 필요 시 postclose source-quality/workorder handoff로만 넘긴다.

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

- [ ] `[SwingSimProbeWorkorderCoverage0604] 스윙 sim/probe stale state 및 priority provenance gap의 code-improvement workorder 포착 여부 확인` (`Due: 2026-06-04`, `Slot: POSTCLOSE`, `TimeWindow: 18:25~18:40`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-06-04.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-04.json), [code_improvement_workorder_2026-06-04.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-04.md), [threshold_cycle_postclose_verification_2026-06-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-04.json), [swing_intraday_probe_state.json](/home/ubuntu/KORStockScan/data/runtime/swing_intraday_probe_state.json)
  - 판정 기준: 장중 확인된 `swing_intraday_probe_state` stale/test-like open rows, `SWING_PROBE_EVENT_FIELD_CONFLICT`(`curr_price` protected field conflict), swing active policy `priority_policy_id` runtime provenance 미관찰이 장후 자동화체인의 `code_improvement_workorder` 또는 postclose verifier에서 source-quality/instrumentation/workorder로 표면화됐는지 먼저 확인한다.
  - 우선순위: workorder/verifier가 이미 포착했으면 해당 workorder의 `implement_now|attach_existing_family|design_family_candidate|reject` 분류를 따른다. 포착하지 못했으면 개별 stale/provenance 문제를 바로 처리하기 전에 `automation_handoff_gap` 또는 `code_improvement_workorder_coverage_gap`으로 자동화체인 보수 workorder를 먼저 만든다.
  - IN scope: stale probe cleanup detector, protected-field conflict producer/parser fix, swing active priority runtime provenance field emission, workorder/verifier handoff coverage, 다음 영업일 checklist 누락 방지.
  - OUT scope: 스윙 full-live 전환, broker submit 허용, provider/bot 변경, cap release, hard/protect/emergency safety 완화, 장중 runtime mutation.
  - Acceptance: `code_improvement_workorder`가 문제를 포착한 경우 근거 order id와 후속 구현 범위를 남긴다. 포착하지 못한 경우 자동화체인 보수 항목을 다음 checklist 또는 workorder에 parser-friendly로 남긴 뒤, 그 보수 이후 stale/provenance 문제 처리를 진행하도록 닫는다.
  - Go/no-go: `covered_by_workorder`, `covered_by_verifier`, `automation_chain_coverage_gap_first`, `defer_until_postclose_artifacts`, `reject_not_reproducible` 중 하나로 닫는다.

- [ ] `[LegacyRealBuyCutoverGuard0604] SIM-derived live 전환 시 기존 스캘핑 real BUY fallback 차단 guard 설계 확인` (`Due: 2026-06-04`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: ScalpingLogic`)
  - Source: [threshold_apply_2026-06-04.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-04.json), [threshold_runtime_env_2026-06-04.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-04.env), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `runtime_apply_bridge` 또는 greenfield/policy-authorized real mode가 SIM-derived `live_auto_apply_ready` policy를 실브로커 주문으로 전환할 때, promoted bucket/policy allowlist 밖의 기존 스캘핑 real BUY 경로가 broker submit까지 도달하지 못하도록 fail-closed guard와 attribution split을 정의한다.
  - IN scope: legacy/default real BUY fallback 차단 조건, promoted policy allowlist 확인, hard-safety/broker/stale/account/order/quantity/cooldown guard 유지, post-apply attribution에서 `legacy_fallback_blocked`와 `policy_authorized_real` 분리, 다음 PREOPEN 적용 전 verifier 조건.
  - OUT scope: 장중 env 수정, bot restart, provider route 변경, broker/order guard 완화, cap release, hard/protect/emergency safety 완화, 오늘 real 주문 중단/재개.
  - Acceptance: 기존 주문 plumbing은 공통 실행 인프라로 유지하되 real BUY decision authority는 승인된 policy로만 제한하는 설계가 문서화되고, policy 없음/allowlist miss/contract gap이면 `actual_order_submitted=false` 또는 submit block으로 닫는 다음 구현 workorder 필요 여부를 분리한다.
  - Go/no-go: 구현 필요하면 `legacy_real_buy_cutover_guard_workorder_required`로 닫고 다음 영업일 checklist 또는 code-improvement workorder에 넘긴다. 구현 불필요하거나 이미 guard가 있으면 근거 파일/이벤트를 남기고 `already_guarded`로 닫는다.

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

- [ ] `[PostcloseAutomationHealthCheck20260604] Runbook 운영 확인 큐: 장후 자동화체인 및 DONE controller/Codex runner 감시 결과 확인` (`Due: 2026-06-04`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [run_postclose_done_controller.sh](/home/ubuntu/KORStockScan/deploy/run_postclose_done_controller.sh), [install_postclose_done_controller_cron.sh](/home/ubuntu/KORStockScan/deploy/install_postclose_done_controller_cron.sh)
  - 판정 기준: postclose wrapper `[START]/[DONE]/[FAIL]`, `threshold_cycle_postclose_verification`, `runtime_apply_gap_audit`, `code_improvement_workorder`, `postclose_done_controller`, `codex_workorder_runner`, `tuning_performance_control_tower`, cron logs를 같은 날짜 최신 generation으로 대조한다. `postclose_done_controller`가 recoverable warning/fail을 source refresh, retry queue/workorder regeneration, verifier rerun, guarded same-date wrapper rerun으로 해소했는지 확인하고, Codex workorder runner가 safe-scope `implement_now` 항목만 별도 worktree에서 구현/검증/커밋했는지 확인한다.
  - IN scope: `data/report/postclose_done_controller/postclose_done_controller_2026-06-04.{json,md}`, `data/report/codex_workorder_runner/codex_workorder_runner_2026-06-04.{json,md}`, `logs/postclose_done_controller_cron.log`, `tmp/codex_worktrees/codex-workorder-2026-06-04`, `codex/workorder-2026-06-04-*` branch/commit audit, Codex SDK package/auth/timeout/blocker status.
  - OUT scope: real order authority, PREOPEN live env 직접 수정, provider route 변경, bot restart, cap release, broker/order guard 변경, hard/protect/emergency safety 완화, 장후 wrapper/controller 결과를 근거로 한 수동 threshold mutation.
  - Acceptance: controller status가 `done` 또는 documented blocked state로 닫히고 predecessor wait/timeout/fail, final verifier, required audit/workorder/control-tower freshness가 설명된다. Codex runner는 `completed`, `no_safe_orders`, 또는 `blocked_*`를 명확히 남기며, blocked이면 `codex_package_unavailable|codex_login_required|codex_login_timeout|forbidden_diff|worktree_dirty|worktree_stale_head|unsupported_acceptance_tests` 중 원인을 분리한다.
  - 다음 액션: `postclose_chain_done`, `controller_recovered_and_done`, `controller_blocked_non_recoverable`, `codex_runner_completed`, `codex_runner_blocked_user_action_required`, `postclose_artifact_wait`, `followup_workorder_required` 중 하나로 닫고, 사용자 조치가 필요한 경우 Project/Calendar sync와 분리해 기록한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
