# 2026-05-26 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact 또는 명시적 phase0 auto-approval 계약과 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.
- `gpt-5.4-mini` Tier2 중 `entry_price`/`holding_flow`는 10:13 KST 사용자 override 이후 Nova Lite v2 primary, Nova Lite v1 shadow 비교, OpenAI failback을 확인한다.
- Nova Micro는 2026-05-22 사용자 최종 override로 shadow/duel과 누적 판정을 중단한다. Tier1은 OpenAI `gpt-5-nano` 라우팅을 유지한다.
- OFI/QI stale/missing 급증과 스윙 probe handoff gap은 runtime 변경이 아니라 source-quality/producer readiness 작업으로 닫는다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- Nova Lite v2 primary 적용 범위는 `entry_price,holding_flow`로 제한한다. 기타 Tier2 endpoint는 OpenAI 유지다.
- Nova Lite v1은 Nova Lite v2 primary와 비교하는 shadow-only다. v1 shadow 결과를 threshold/order guard 변경 근거와 혼합하지 않는다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- pattern lab AI review warning은 source-only warning으로만 보고, 명시적 workorder/code patch가 생성될 때만 구현 대상으로 삼는다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-05-22` postclose -> `2026-05-26`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:40~09:00)

운영 확인 기록 (`PreopenAutomationHealthCheck20260526`, Project `PVTI_lAHOAXZuE84BUTcPzgti7Fg`): 판정은 `pass`. [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)의 `Runbook 운영 확인 큐 / 장전 확인 절차` 기준으로 시간이 지난 반복 RunbookOps 항목을 재확인했다. [threshold_cycle_preopen_2026-05-26.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-05-26.status.json)은 `status=succeeded`, `exit_code=0`이고, [threshold_apply_2026-05-26.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-26.json)은 `status=auto_bounded_live_ready`, `runtime_change=true`, `warnings=[]`다. `2026-05-26 09:36 KST` 재검증에서 `tmux bot` 세션, `run_bot.sh`, `bot_main.py` PID `37967`이 살아 있고 `PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run`은 `summary_severity=pass`, `cron_completion=pass`, `process_health=pass`, `artifact_freshness=pass`, `resource_usage=pass`, `stale_lock=pass`다. 다음 액션은 장중 `RuntimeEnvIntradayObserve0526`, `SimProbeIntradayCoverage0526`, `OFIQProducerReadiness0526`, `SwingProbeSourceBookHandoff0526`에서 provenance/source-quality를 확인하는 것이며, 이 장전 확인을 threshold/order/provider/bot 변경 근거로 확장하지 않는다.

- [x] `[SimSubmitPathBucketInstrumentationPreopen0526] sim submit-path liquidity/overbought guard bucket instrumentation 장전 보강` (`Due: 2026-05-26`, `Slot: PREOPEN`, `TimeWindow: 08:35~08:40`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-22.json), [lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_decision_matrix.py), [scalp_entry_action_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/scalp_entry_action_decision_matrix.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: `scalp_sim_pre_submit_liquidity_guard_would_block/pass/unknown`와 `scalp_sim_pre_submit_overbought_guard_would_block/pass`가 `actual_order_submitted=false`, `broker_order_forbidden=true`, `runtime_effect=false`, `decision_authority=sim_submit_path_observation_only`로 기록되고, real/sim shared pre-submit guard evaluator verdict가 submit 이후 pending/fill/holding/sell completion까지 전파되며, LDM submit bucket이 `liquidity_guard_action`, `liquidity_bucket`, `overbought_guard_action`, `overbought_bucket`, `latency_state`, `latency_reason`을 생성한다.
  - 금지: sim `WOULD_BLOCK`를 real broker submit 차단 해제, threshold 변경, provider route 변경, bot restart trigger, 실주문 전환 근거로 해석하지 않는다. sim 가상체결 흐름은 counterfactual verdict와 별개로 계속 진행한다.
  - 판정: `implemented_source_only_counterfactual_bucket_instrumentation`
  - 근거: sim submit 직전 guard verdict 이벤트와 LDM/ADM/source-quality contract를 추가했다. `WOULD_BLOCK`은 `SKIP_PRE_SUBMIT_SAFETY` 원인축으로 귀속되지만 broker/order/runtime env 동작은 변경하지 않는다.
  - 다음 액션: 장후 `lifecycle_decision_matrix`와 `threshold_cycle_ev`에서 submit bucket이 `liquidity_unknown` 대신 liquidity/latency/overbought bucket으로 분해되는지 확인한다.

- [x] `[BedrockNovaLiteRouteAndV2ShadowPreopen0526] Nova Lite v1 entry_price/holding_flow primary 및 v2 shadow 계약 확인` (`Due: 2026-05-26`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:45`, `Track: AITransport`)
  - Source: [2026-05-22 checklist](/home/ubuntu/KORStockScan/docs/checklists/2026-05-22-stage2-todo-checklist.md), [bedrock_nova_lite_shadow.py](/home/ubuntu/KORStockScan/src/engine/bedrock_nova_lite_shadow.py), [bedrock_nova_lite_v2_shadow.py](/home/ubuntu/KORStockScan/src/engine/bedrock_nova_lite_v2_shadow.py), [bedrock_nova_provider.py](/home/ubuntu/KORStockScan/src/engine/bedrock_nova_provider.py), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), AWS Bedrock Nova 2 Lite model documentation
  - 판정 기준: startup env에 `KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE=primary`, `KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_ENDPOINTS=entry_price,holding_flow`, `KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_SHADOW_ENABLED=true`가 있고, provider audit에서 `entry_price`/`holding_flow`만 Bedrock Lite primary로 들어가며 OpenAI failback guard가 켜져 있는지 확인한다. v2 shadow는 `bedrock_nova_lite_v2_shadow_YYYY-MM-DD.jsonl`에 `baseline_bedrock_model_id`, `candidate_bedrock_model_id`, `v1_v2_action_match`, `v2_parse_ok`, `v2_latency_ms`, `v2_estimated_cost_usd`를 남겨야 한다.
  - 금지: Lite v2 shadow를 Lite v1 route candidate, OpenAI `gpt-5.4-mini` 즉시 대체, provider route 변경, threshold/order guard 변경, bot restart trigger로 해석하지 않는다.
  - 다음 액션: `lite_v1_primary_scope_confirmed_v2_shadow_collecting`, `openai_failback_active_with_v2_shadow_gap`, `defer_region_or_model_gap`, `fail_endpoint_scope_leak` 중 하나로 닫는다.
  - 판정: `openai_failback_active_with_v2_shadow_gap`
  - 근거: [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)에 `KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE=primary`, `KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_ENDPOINTS=entry_price,holding_flow`, `KORSTOCKSCAN_BEDROCK_PRIMARY_FAILBACK_TO_OPENAI=true`, `KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_SHADOW_ENABLED=true`가 고정되어 endpoint scope와 failback guard는 닫혔다. 다만 [bedrock_nova_lite_v2_shadow_report_2026-05-26.json](/home/ubuntu/KORStockScan/data/report/bedrock_nova_lite_v2_shadow/bedrock_nova_lite_v2_shadow_report_2026-05-26.json)은 `decision_authority=shadow_observation_only`, `runtime_effect=false`, `row_count=0`이므로 v2 비교 표본은 아직 없다.
  - 보정 기록 (`2026-05-26 09:45 KST`): Lite v2 shadow 실패 원인은 Bedrock `amazon.nova-2-lite-v1:0` direct model ID가 on-demand 호출을 지원하지 않는 계약 gap이었다. [bedrock_nova_provider.py](/home/ubuntu/KORStockScan/src/engine/bedrock_nova_provider.py)와 [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)의 v2 shadow model ID를 inference profile ID `global.amazon.nova-2-lite-v1:0`로 보정했다. 이 변경은 `decision_authority=shadow_observation_only`, `runtime_effect=false` provider shadow 설정 보정이며 Lite v1 primary, OpenAI failback, threshold, order guard, bot restart 권한을 바꾸지 않는다. 현재 실행 중인 봇에는 다음 재기동 이후 적용된다.
  - 런타임 반영 확인 (`2026-05-26 09:44~09:45 KST`): `restart.flag`만으로는 기존 `run_bot.sh` 래퍼 셸의 export가 재로딩되지 않아 1차 재기동 PID `46621`에는 direct model ID가 남았다. tmux `bot` 세션을 재생성해 래퍼를 함께 로드한 뒤 새 PID `47022`에서 `KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_MODEL_ID=global.amazon.nova-2-lite-v1:0`, `KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_SHADOW_ENABLED=true`, `KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE=primary`를 확인했다. `error_detector --mode health_only --dry-run`은 `summary_severity=pass`, `process_health=pass`이고, 실제 Bedrock smoke call은 `model_id=global.amazon.nova-2-lite-v1:0`, `parse_ok=True`, `latency_ms=907`, `estimated_cost_usd=0.00001044`로 통과했다. shadow artifact도 `2026-05-26T09:44:56+09:00` holding_flow 행에서 `model_id=global.amazon.nova-2-lite-v1:0`, `parse_ok=true`, `nova_action=TRIM`, `nova_score=73`, `runtime_effect=false`로 생성됐다.
  - 구조 전환 기록 (`2026-05-26 10:13 KST`): 사용자 명시 override로 `entry_price`/`holding_flow` 운영 endpoint를 Nova Lite v2 primary로 전환하고 Nova Lite v1을 shadow 비교 대상으로 바꿨다. [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)는 `KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE=primary`, `KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_FAMILY=lite_v2`, `KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_ENDPOINTS=entry_price,holding_flow`, `KORSTOCKSCAN_BEDROCK_NOVA_LITE_SHADOW_ENABLED=true`, `KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_SHADOW_ENABLED=false`, `KORSTOCKSCAN_BEDROCK_PRIMARY_FAILBACK_TO_OPENAI=true`를 로드한다. 우아한 래퍼 재기동 후 새 `bot_main.py` PID `57578`에서 오늘 runtime env와 `run_bot.sh`의 `KORSTOCKSCAN_*` export 94개가 모두 로드됐고 mismatch는 `0`이다. 실제 route smoke는 primary `model_id=global.amazon.nova-2-lite-v1:0`, `parse_ok=true`, `bedrock_primary_used=true`, `bedrock_failback_used=false`; v1 shadow row는 `baseline_provider=bedrock_nova_lite_v2_primary`, `candidate_provider=bedrock_nova_lite_v1_shadow`, `model_id=apac.amazon.nova-lite-v1:0`, `parse_ok=true`, `actual_order_submitted=false`, `runtime_effect=false`로 생성됐다.
  - 다음 액션: 장중 `entry_price`/`holding_flow` 호출 후 v2 primary provenance와 v1 shadow row 생성을 계속 확인한다. v1/v2 차이는 source-quality 관찰이며 threshold/order guard/bot restart 변경 근거로 쓰지 않는다.

- [x] `[ThresholdEnvAutoApplyPreopen0526] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-26`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-22.json), [runtime_apply_gap_audit_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-05-22.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다. 특히 runtime apply gap retry queue의 `entry_wait6579_score66_69_recovery_gate_v1:2026-05-22`는 `producer_state=live_auto_apply_ready`, `bridge_state=live_auto_apply_ready`, `runtime_hook_state=mapped`, `failure_state=retry_pending`, `next_retry_stage=preopen_apply_candidate`이므로 05-26 장전 apply plan/runtime env에서 소비됐는지 family 단위로 확인한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `entry_wait6579_score66_69_env_generated`, `entry_wait6579_score66_69_retry_not_consumed`, `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 판정: `entry_wait6579_score66_69_env_generated`
  - 근거: [threshold_apply_2026-05-26.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-26.json)은 `status=auto_bounded_live_ready`, `apply_mode=auto_bounded_live`, `runtime_change=true`, `warnings=[]`이며 [threshold_runtime_env_2026-05-26.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-26.env)이 생성됐다. env에는 `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_CALIBRATION_STATE=runtime_apply_bridge:live_auto_apply_ready`, `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_THRESHOLD_VERSION=entry_wait6579_score66_69_recovery_gate_v1:2026-05-22`, `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_SCORE=66`, `MAX_SCORE=69`가 기록됐다.
  - 다음 액션: 장중 `RuntimeEnvIntradayObserve0526`에서 runtime event provenance와 rollback guard breach 여부를 확인한다. 이 확인은 장중 threshold mutation 근거가 아니다.

- [x] `[OpenAIAndLiteTransportPreopenConfirm0526] OpenAI WS 유지 및 Lite endpoint provenance 확인` (`Due: 2026-05-26`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-22.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-22.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 OpenAI route/Responses WS 설정과 `analyze_target` OpenAI provenance, `entry_price`/`holding_flow` Lite primary provenance, 기타 Tier2 endpoint OpenAI 유지 여부를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 다음 액션: Lite endpoint 또는 OpenAI 유지 표본이 부족하면 장중 표본 재확인 항목과 연결한다.
  - 판정: `openai_ws_keep_lite_primary_scope_confirmed_sample_pending`
  - 근거: [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)는 `KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_TIMEOUT_MS=15000`를 유지한다. [openai_ws_stability_2026-05-22.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-22.md)는 `decision=keep_ws`, unique WS calls `3715`, fallback `0/3715`, WS success rate `1.0`, `entry_price` WS sample `134`를 기록했다. Lite primary endpoint는 `entry_price,holding_flow`로 제한되어 있으나 05-26 장중 provider provenance 표본은 아직 전이다.
  - 다음 액션: 장중 `analyze_target` OpenAI WS provenance와 `entry_price`/`holding_flow` Bedrock Lite primary/failback provenance를 분리 확인한다. provider transport 확인을 threshold/order/swing dry-run 변경으로 확장하지 않는다.

- [x] `[SwingPreFinalAutoAndFinalApprovalPreopen0526] 스윙 pre-final auto state 및 final approval artifact 확인` (`Due: 2026-05-26`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-22.json), [threshold_cycle_ev_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-22.json)
  - 판정 기준: pre-final 후보는 parsed AI Tier2 auto state가 있어야 env apply 대상이고, final-stage 후보만 사용자 승인 artifact가 필요하다. 확인 대상은 `swing_runtime_approval:2026-05-22:swing_model_floor`, `swing_runtime_approval:2026-05-22:swing_gatekeeper_reject_cooldown`, `swing_one_share_real_canary:2026-05-22:phase0`다. `swing_one_share_real_canary_phase0`와 `swing_scale_in_real_canary_phase0`는 parsed AI Tier2 review와 source report hard floor/source-quality/allowlist/cap 통과 시 phase0 auto-approval로 소비하며, 별도 artifact는 allowlist/cap narrowing 용도다.
  - 금지: 스윙 dry-run 해제, full real-order conversion, floor 일반 runtime 변경, cap release를 phase0 real canary auto-approval과 섞지 않는다.
  - 다음 액션: `general_approval_artifact_present`, `general_approval_artifact_missing`, `real_canary_phase0_auto_approved`, `real_canary_blocked_by_policy` 중 하나로 닫는다.
  - 판정: `general_approval_artifact_present + real_canary_phase0_auto_approved`
  - 근거: 사용자 승인으로 [swing_runtime_approvals_2026-05-22.json](/home/ubuntu/KORStockScan/data/threshold_cycle/approvals/swing_runtime_approvals_2026-05-22.json)과 [swing_one_share_real_canary_2026-05-22.json](/home/ubuntu/KORStockScan/data/threshold_cycle/approvals/swing_one_share_real_canary_2026-05-22.json)을 생성했다. [threshold_apply_2026-05-26.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-26.json)은 swing `requested=3`, `approved=3`, `blocked=[]`로 소비했고 env에는 `KORSTOCKSCAN_ML_GATEKEEPER_REJECT_COOLDOWN=6600`, `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true`, `KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_ENABLED=true`, `KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES=000100,028050,092200`, 1주/1일/3포지션/300000 KRW cap이 기록됐다.
  - 다음 액션: 장중 real canary는 승인 allowlist와 cap 안의 `BUY_INITIAL`/`SELL_CLOSE`만 확인한다. 스윙 dry-run 해제, full real-order conversion, scale-in real canary, cap release, provider/bot 변경은 승인 범위 밖이다.

## 장중 체크리스트 (09:05~15:20)

운영 확인 기록 (`IntradayAutomationHealthCheck20260526`, Project `PVTI_lAHOAXZuE84BUTcPzgti7Gg`): 판정은 `pass`. [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)의 `Runbook 운영 확인 큐 / 장중 확인 절차` 기준으로 시간이 지난 반복 RunbookOps 항목을 확인했다. `2026-05-26 10:03:56 KST`에 `PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run`을 실행했고 `summary_severity=pass`, `cron_completion=pass`, `process_health=pass`, `artifact_freshness=pass`, `resource_usage=pass`, `stale_lock=pass`다. `bot_main.py` PID `47022`는 살아 있고 `pipeline_events_age_sec=0.9`, `threshold_events_age_sec=0.9`, sentinel/panic report status는 pass다. 다음 액션은 16:10 이후 postclose 산출물에서 Swing LDM source_book handoff와 누적 provenance를 재확인하는 것이며, 장중 확인 결과를 threshold/order/provider/bot 변경 근거로 확장하지 않는다.

- [x] `[RuntimeEnvIntradayObserve0526] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-26`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-22.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime, swing_one_share_real_canary_phase0, swing_gatekeeper_reject_cooldown가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.
  - 처리 기록 (`2026-05-26 10:03~10:06 KST`, Project `PVTI_lAHOAXZuE84BUTcPzgthNlE`):
    - 판정: `warning`
    - 근거: `bot_main.py` PID `47022`의 런타임 env에는 `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`, `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`, `KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED=true`, `KORSTOCKSCAN_SCALP_SIM_AI_BUDGET_ENABLED=true`, `KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_ENABLED=true`, `KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_ENABLED=true`, `KORSTOCKSCAN_ML_GATEKEEPER_REJECT_COOLDOWN=6600`가 로드되어 있다. [pipeline_events_2026-05-26.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-26.jsonl)와 [threshold_events_2026-05-26.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-05-26.jsonl) 집계에서 `soft_stop_whipsaw_confirmation=44`, `scalp_sim_candidate_window_expansion=1804`, `scalp_sim_ai_budget_manager=2528`, `lifecycle_decision_matrix_runtime=7095`, `swing_gatekeeper_reject_cooldown=64`건의 provenance가 확인됐고 rollback breach record는 `0`건이다. `score65_74_recovery_probe`와 `swing_one_share_real_canary_phase0`는 env는 로드됐으나 10:06 KST 기준 해당 family event가 아직 발생하지 않아 source-quality 관찰 경고로 분리한다.
    - 다음 액션: 오늘 장중 이벤트가 더 쌓인 뒤 `score65_74_recovery_probe`와 승인 allowlist 기반 `swing_one_share_real_canary_phase0` 발생 여부를 재확인한다. 이 기록은 threshold/order/provider/bot 변경 근거가 아니다.

- [x] `[SimProbeIntradayCoverage0526] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-26`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-22.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.
  - 처리 기록 (`2026-05-26 10:03~10:06 KST`, Project `PVTI_lAHOAXZuE84BUTcPzgthNlk`):
    - 판정: `pass`
    - 근거: 장중 sim/probe/shadow 관련 이벤트는 `17549`건이고 `actual_order_submitted` 누수는 `0`건이다. 주요 stage는 `bad_entry_refined_candidate=2865`, `scalp_sim_panic_scale_in_blocked=2672`, `scalp_entry_action_decision_snapshot=1441`, `swing_probe_discarded=1229`, `scalp_sim_ai_holding_live_call=668`, `scalp_sim_ai_holding_deferred=344`, `sim_ai_budget_exhausted=344`다. [swing_intraday_probe_state.json](/home/ubuntu/KORStockScan/data/runtime/swing_intraday_probe_state.json)은 `simulation_book=swing_intraday_live_equiv_probe`, `owner=SwingIntradayLiveEquivalentProbe0511`, `updated_at=2026-05-26T10:01:13`이고 active probe holdings에 `actual_order_submitted=false`, `broker_order_forbidden=true`, `simulated_order=true`가 유지된다.
    - 다음 액션: sim/probe EV는 postclose source bundle과 source-quality adjusted EV에서만 사용하고, broker execution 품질/실주문 전환/threshold mutation 근거로 단독 사용하지 않는다.

- [x] `[OFIQProducerReadiness0526] OFI/QI producer readiness 및 stale/missing reason별 수집 보강 확인` (`Due: 2026-05-26`, `Slot: INTRADAY`, `TimeWindow: 09:50~10:05`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-22.json), [observation_source_quality_audit_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-05-22.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: `swing_lab_dq:OFI/QI stale/missing ratio=0.915 (517/565)`를 기준으로 `micro_missing`, `micro_stale`, `observer_unhealthy`, `micro_not_ready`, `state_insufficient`, `observer_gap_with_fresh_ws_quote`를 reason별 count와 unique record count로 분해한다. producer/consumer readiness는 WS quote freshness, orderbook micro cache ready, state sufficient, symbol coverage를 분리해서 확인한다.
  - 금지: OFI/QI missing/stale warning을 단독 BUY/EXIT/scale-in hard gate, threshold 변경, provider route 변경, bot restart trigger로 해석하지 않는다.
  - 다음 액션: `producer_ready_warning_resolved`, `source_quality_keep_collecting`, `code_workorder_needed_for_missing_field`, `fail_producer_handoff_gap` 중 하나로 닫는다.
  - 처리 기록 (`2026-05-26 10:03~10:06 KST`, Project `PVTI_lAHOAXZuE84BUTcPzgthNmM`):
    - 판정: `pass` (`producer_ready_warning_resolved`)
    - 근거: 10:06 KST 기준 orderbook micro/OFI/QI 필드가 있는 장중 record는 `1321`건, unique symbol은 `92`개다. producer readiness는 `orderbook_micro_ready=True 1139`, `False 182`로 05-22 stale/missing 기준보다 개선됐고, reason 분해는 `ready=1139`, `missing_snapshot=141`, `micro_context_missing=40`, `insufficient_samples=1`, `missing_trade=1`이다. observer는 `observer_healthy=True 1139`, `False 182`, `observer_missing_reason=ok 1139`로 분리된다. 주요 consumer stage는 `scalp_entry_action_decision_snapshot=406`, `orderbook_stability_observed=358`, `holding_flow_ofi_smoothing_applied=195`, `entry_ai_price_canary_fallback=106`, `entry_ai_price_canary_applied=69`다.
    - 다음 액션: `missing_snapshot`과 `micro_context_missing`은 source-quality 태그로 계속 수집한다. 오늘 확인 결과만으로 BUY/EXIT/scale-in hard gate, threshold 변경, provider route 변경, bot restart를 수행하지 않는다.

- [x] `[SwingProbeSourceBookHandoff0526] swing_intraday_live_equiv_probe 생성 및 Swing LDM source_book handoff 확인` (`Due: 2026-05-26`, `Slot: INTRADAY`, `TimeWindow: 10:05~10:20`, `Track: SwingLogic`)
  - Source: [swing_lifecycle_decision_matrix_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-05-22.json), [threshold_cycle_ev_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-22.json), [swing_lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/swing_lifecycle_decision_matrix.py)
  - 판정 기준: 장중 `swing_intraday_live_equiv_probe` source row가 생성되고, 장후 Swing LDM의 `source_book_counts`에 `swing_intraday_live_equiv_probe > 0`으로 소비되는지 확인한다. `swing_lifecycle_decision_matrix:swing_intraday_live_equiv_probe_missing`이 재발하면 source producer, event naming, source_book join, postclose wrapper input 순서 중 어느 단계 gap인지 분리한다.
  - 금지: probe source gap을 스윙 real order 승인, dry-run 해제, threshold apply, broker/provider/bot 변경 근거로 쓰지 않는다.
  - 다음 액션: `probe_handoff_pass`, `producer_missing`, `source_book_join_gap`, `postclose_consumer_gap` 중 하나로 닫는다.
  - 처리 기록 (`2026-05-26 10:06 KST`, Project `PVTI_lAHOAXZuE84BUTcPzgthNnQ`):
    - 판정: `warning` (`probe_handoff_pass` for intraday producer, postclose consumer pending)
    - 근거: 장중 source producer는 동작 중이다. `swing_intraday_live_equiv_probe`/swing probe 관련 이벤트는 `1541`건이고 주요 stage는 `swing_probe_discarded=1229`, `swing_reentry_counterfactual_after_loss=165`, `swing_probe_state_persisted=42`, `swing_probe_entry_candidate=18`, `swing_probe_holding_started=18`, `swing_probe_scale_in_order_assumed_filled=11`, `swing_probe_exit_signal=10`, `swing_probe_sell_order_assumed_filled=10`이다. [swing_intraday_probe_state.json](/home/ubuntu/KORStockScan/data/runtime/swing_intraday_probe_state.json)은 `simulation_book=swing_intraday_live_equiv_probe`로 active state를 보존한다. 장후 Swing LDM `source_book_counts` 소비 여부는 16:10 이후 산출물이 필요해 아직 확정할 수 없다.
    - 다음 액션: postclose Swing LDM 산출물에서 `source_book_counts.swing_intraday_live_equiv_probe > 0`을 확인해 `postclose_consumer_gap` 여부를 닫는다. 이 warning은 스윙 real order 승인, dry-run 해제, threshold apply, broker/provider/bot 변경 근거가 아니다.

## 장후 체크리스트 (16:30~19:10)

- [x] `[BedrockNovaMicroCumulativeDecision0526] Nova Micro 하루 추가 관찰 후 누적 exact join 판정` (`Due: 2026-05-26`, `Slot: POSTCLOSE`, `TimeWindow: 17:40~18:05`, `Track: AITransport`)
  - Source: [bedrock_nova_micro_one_day_decision.py](/home/ubuntu/KORStockScan/src/tests/bedrock_nova_micro_one_day_decision.py), [bedrock_nova_micro_shadow_2026-05-21.jsonl](/home/ubuntu/KORStockScan/data/report/bedrock_nova_micro_shadow/bedrock_nova_micro_shadow_2026-05-21.jsonl), [bedrock_nova_micro_shadow_2026-05-22.jsonl](/home/ubuntu/KORStockScan/data/report/bedrock_nova_micro_shadow/bedrock_nova_micro_shadow_2026-05-22.jsonl), `bedrock_nova_micro_shadow_2026-05-26.jsonl`, `sim_post_sell_evaluations_YYYY-MM-DD.jsonl`
  - 실행 명령: `PYTHONPATH=. .venv/bin/python -m src.tests.bedrock_nova_micro_one_day_decision --start-date 2026-05-21 --date 2026-05-26`
  - 판정 기준: 05-21/05-22/05-26 누적 exact join만 primary로 쓰고, `entry_watch_buy`와 `holding_continuation`을 분리한다. action match, parse_ok, latency, cost, token/cache 절감, 일일 단독 EV로 winner를 정하지 않는다.
  - 금지: 누적 판정 전 Micro shadow/duel OFF, global provider route 변경, threshold/order guard 변경, bot restart trigger 금지.
  - 다음 액션: `winner_openai_turn_micro_shadow_off`, `winner_nova_micro_record_profile_candidate_turn_shadow_off`, `keep_shadow_collecting_source_quality_gap`, `fail_primary_metric_join_contract` 중 하나로 닫는다.
  - 취소 기록 (`2026-05-22`): 사용자 최종 override로 Micro shadow/duel과 누적 판정을 중단한다. 이유는 Micro action score가 `WAIT->BUY 95`로 과도하게 공격적인 편향을 보였고 손실 BUY 표본이 현재 LDM/ADM 기준 자동 BUY 대상이 아니었기 때문이다. 05-26에는 `bedrock_nova_micro_shadow_2026-05-26.jsonl`을 만들지 않고 Tier1 OpenAI `gpt-5-nano` 라우팅을 유지한다. 이 취소는 provider route를 Micro로 변경하지 않으며 threshold/order guard/bot restart 권한이 없다.

- [ ] `[ThresholdDailyEVReport0526] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-05-26`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-22.json)
  - 판정 기준: real/sim/combined split, selected/blocked family, runtime_change, warning을 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[CodeImprovementWorkorderReview0526] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-05-26`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-22.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-22.md), [code_improvement_workorder_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-22.json)
  - 판정 기준: selected_order_count=29와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [ ] `[PatternLabAIReviewWarningDisposition0526] pattern_lab_ai_review_warning source-only 처리 및 workorder 표면화 여부 확인` (`Due: 2026-05-26`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:25`, `Track: RuntimeStability`)
  - Source: [pattern_lab_ai_review_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-05-22.json), [runtime_approval_summary_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-22.json), [code_improvement_workorder_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-22.json)
  - 판정 기준: `pattern_lab_ai_review_warning`은 `decision_authority=pattern_lab_ai_review_source_only`, `runtime_effect=false`로 유지한다. `fail_count`, `warning_count`, `code_improvement_order_count`, `explicit_gap_type`, `source_paths`, `forbidden_runtime_uses`를 확인하고, 명시적 source-quality/automation handoff gap이 있을 때만 code workorder로 표면화한다.
  - 금지: AI review ambiguity 또는 source-only warning을 runtime mutation, threshold/order/provider/bot 변경, 자동 approval artifact 생성으로 연결하지 않는다.
  - 다음 액션: `source_only_no_workorder`, `workorder_surface_required`, `fail_runtime_mutation_leak` 중 하나로 닫는다.

- [ ] `[ProducerGapDiscoveryPostclose0526] missing producer 자동 발굴 및 workorder handoff 확인` (`Due: 2026-05-26`, `Slot: POSTCLOSE`, `TimeWindow: 17:25~17:35`, `Track: RuntimeStability`)
  - Source: [producer_gap_discovery.py](/home/ubuntu/KORStockScan/src/engine/automation/producer_gap_discovery.py), [build_code_improvement_workorder.py](/home/ubuntu/KORStockScan/src/engine/build_code_improvement_workorder.py), [verify_threshold_cycle_postclose_chain.py](/home/ubuntu/KORStockScan/src/engine/verify_threshold_cycle_postclose_chain.py), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: `producer_gap_discovery_2026-05-26.json`이 `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`로 생성되고, AI two-pass review가 `parsed` 및 audit `pass`로 닫힌다. high-priority `code_improvement_orders`가 있으면 `code_improvement_workorder_2026-05-26.json` selected order에 포함되고 verifier가 `producer_gap_discovery_handoff.status=pass`로 닫는다.
  - 금지: missing producer 후보를 실주문 enable, threshold mutation, provider change, bot restart, cap release, entry/exit override 근거로 사용하지 않는다. AI unavailable/parse reject/audit fail은 경고 지속이 아니라 fail-closed로 처리한다.
  - 다음 액션: `pass_workorder_handoff`, `fail_ai_review`, `fail_workorder_handoff`, `source_only_no_candidate` 중 하나로 닫는다.

- [ ] `[BottomReboundSimHandoffPostclose0526] bottom_rebound source 후보의 swing discovery sim DB handoff 확인` (`Due: 2026-05-26`, `Slot: POSTCLOSE`, `TimeWindow: 17:35~17:40`, `Track: SwingLogic`)
  - Source: [swing_strategy_discovery_sim.py](/home/ubuntu/KORStockScan/src/engine/swing_strategy_discovery_sim.py), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [verify_threshold_cycle_postclose_chain.py](/home/ubuntu/KORStockScan/src/engine/verify_threshold_cycle_postclose_chain.py), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: `swing_bottom_rebound_candidate_source_2026-05-26.json`이 source-only contract pass이고 후보가 있으면 postclose wrapper가 `swing_strategy_discovery_sim --include-bottom-rebound-source`를 실행한다. sim report의 `bottom_rebound_selected_candidate_count`, `bottom_rebound_arm_count`, `bottom_rebound_persisted_candidate_count`, `bottom_rebound_persisted_arm_count`가 모두 0보다 크고 verifier가 `bottom_rebound_sim_handoff.status=pass`로 닫혀야 한다.
  - 금지: bottom rebound source 후보 또는 virtual arm을 실주문, swing real canary, threshold apply, provider route, bot restart, recommendation_history 변경 근거로 쓰지 않는다.
  - 다음 액션: `pass_bottom_rebound_persisted`, `safe_pool_only_source_missing_or_invalid`, `fail_bottom_rebound_persist_missing`, `fail_source_only_contract` 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0526] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-26`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-22.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[SwingModelMLflowTracking0526] 스윙 학습모델 MLflow 추적성 및 active artifact 승격 계약 확인` (`Due: 2026-05-26`, `Slot: POSTCLOSE`, `TimeWindow: 18:25~18:40`, `Track: RuntimeStability`)
  - Source: [model-training-traceability.md](/home/ubuntu/KORStockScan/docs/model-training-traceability.md), [swing_retrain_pipeline.py](/home/ubuntu/KORStockScan/src/model/swing_retrain_pipeline.py), [swing_model_upgrade.py](/home/ubuntu/KORStockScan/src/model/swing_model_upgrade.py)
  - 판정 기준: MLflow tracking URI는 `file:data/model_registry/swing_v2/mlruns`, experiment는 `korstockscan_swing_v2_model_upgrade`이며, promotion manifest에는 `active_live_behavior=true`, `runtime_change=model_artifact_promote_only`, `swing_live_order_dry_run_required=true`가 있어야 한다. active 적용 범위는 model artifact와 `daily_recommendations_v2` 생성 경로까지다.
  - 금지: MLflow run 또는 model artifact promotion을 스윙 dry-run 해제, real-order conversion, cap release, provider route 변경, bot restart, hard safety 완화, 장중 threshold mutation 근거로 쓰지 않는다.
  - 다음 액션: `tracking_contract_pass`, `tracking_missing`, `promotion_gate_blocked`, `active_artifact_promoted_model_only`, `fail_runtime_authority_leak` 중 하나로 닫는다.

- [ ] `[SwingModelAutoRetrainNoHuman0526] 사람 개입 없는 스윙 모델 학습/AI Tier2/승격 자동화 계약 확인` (`Due: 2026-05-26`, `Slot: POSTCLOSE`, `TimeWindow: 18:10~18:25`, `Track: RuntimeStability`)
  - Source: [auto_retrain_pipeline.sh](/home/ubuntu/KORStockScan/auto_retrain_pipeline.sh), [swing_retrain_pipeline.py](/home/ubuntu/KORStockScan/src/model/swing_retrain_pipeline.py), [swing_model_tier2_review.py](/home/ubuntu/KORStockScan/src/model/swing_model_tier2_review.py), [model-training-traceability.md](/home/ubuntu/KORStockScan/docs/model-training-traceability.md)
  - 판정 기준: 17:30 KST 자동학습은 `train -> backtest -> deterministic gate -> AI Tier2 review -> active artifact promotion -> recommendation CSV smoke` 순서이며, `auto_retrain` status에는 `ai_tier2_review`, `selected_candidate_family`, `current_manifest`, `recommendation_smoke`, `rollback_files`가 있어야 한다. AI Tier2는 `status=parsed` 및 `decision=approved`일 때만 승격을 계속 진행하고, 차단 시 `blocked_ai_tier2` 또는 `not_promoted_ai_tier2_blocked`로 active artifact를 유지한다.
  - 금지: no-human 자동화를 스윙 dry-run 해제, phase0 real canary, real-order conversion, cap release, provider/bot 변경, hard safety 완화, 장중 threshold mutation 권한으로 해석하지 않는다.
  - 다음 액션: `model_auto_retrain_promoted`, `blocked_ai_tier2`, `blocked_deterministic_gate`, `rolled_back_smoke_schema`, `fail_runtime_authority_leak` 중 하나로 닫는다.

- [ ] `[SwingModelAutoRemediationNoHuman0526] AI Tier2 차단 사유 자동 조치 및 다음 cron 재학습 계약 확인` (`Due: 2026-05-26`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:10`, `Track: RuntimeStability`)
  - Source: [auto_retrain_pipeline.sh](/home/ubuntu/KORStockScan/auto_retrain_pipeline.sh), [swing_retrain_pipeline.py](/home/ubuntu/KORStockScan/src/model/swing_retrain_pipeline.py), [swing_model_auto_remediation.py](/home/ubuntu/KORStockScan/src/model/swing_model_auto_remediation.py), [model-training-traceability.md](/home/ubuntu/KORStockScan/docs/model-training-traceability.md)
  - 판정 기준: `blocked_ai_tier2` 발생 시 remediation manifest/report가 생성되고, 다음 cron은 `retry_allowed`에서 allowlist env만 적용한다. `retry_deferred`, `manual_required`, `blocked_forbidden_use`는 active artifact를 유지하며, retry 후에도 deterministic gate, AI Tier2 approved, recommendation smoke를 모두 통과해야 승격된다.
  - 금지: remediation을 label policy, feature semantics, metric contract, active promotion 기준, dry-run 해제, real-order conversion, cap release, provider/bot 변경, hard safety 완화, 장중 threshold mutation 변경 권한으로 해석하지 않는다.
  - 다음 액션: `remediation_retry_allowed`, `remediation_retry_deferred`, `remediation_manual_required`, `remediation_blocked_forbidden_use`, `fail_remediation_runtime_authority_leak` 중 하나로 닫는다.

- [ ] `[ShadowCanaryCohortReview0526] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-26`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 당일 변경/관찰 결과를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 상태 변동 여부를 닫는다.
  - 금지: shadow 금지, canary-only, baseline 승격 원칙을 코드/문서 상태와 분리하지 않는다.
  - 다음 액션: 변경이 있으면 기준문서와 checklist를 함께 갱신하고 cohort 잠금 필드를 남긴다.

- [ ] `[EngineRefactorSafeSliceNext0526] src.engine Phase 2+ 다음 safe slice 선정 및 Phase Final gate 확인` (`Due: 2026-05-26`, `Slot: POSTCLOSE`, `TimeWindow: 18:55~19:10`, `Track: Plan`)
  - Source: [src-engine-refactor-inventory.md](/home/ubuntu/KORStockScan/docs/proposals/src-engine-refactor-inventory.md), [server_report_comparison.py](/home/ubuntu/KORStockScan/src/engine/server_report_comparison.py), [monitoring/server_report_comparison.py](/home/ubuntu/KORStockScan/src/engine/monitoring/server_report_comparison.py), [error_detector_coverage.py](/home/ubuntu/KORStockScan/src/engine/error_detector_coverage.py), [monitoring/error_detector_coverage.py](/home/ubuntu/KORStockScan/src/engine/monitoring/error_detector_coverage.py), [system_metric_sampler.py](/home/ubuntu/KORStockScan/src/engine/system_metric_sampler.py), [threshold_cycle_registry.py](/home/ubuntu/KORStockScan/src/utils/threshold_cycle_registry.py), [src/trading](/home/ubuntu/KORStockScan/src/trading), [src/utils](/home/ubuntu/KORStockScan/src/utils)
  - 판정 기준: Phase 2 Slice 1 wrapper/old-new import/CLI smoke와 targeted test 결과를 기준으로 다음 slice를 report-only 또는 infra 성격 2~4개 파일로만 선정한다. 새 canonical path는 `src.engine.<package>.<module>`로 두고, 기존 `src.engine.<module>` wrapper는 유지한다. Phase Final consumer migration은 안정화된 slice에 한해 deploy/test/docs current path를 점진 변경할 준비 상태만 판정한다. `2026-05-25` prep 기준 바로 검토 가능한 후보는 monitoring `system_metric_sampler -> src.engine.monitoring.system_metric_sampler` 또는 utils boundary `threshold_cycle_registry -> src.engine.automation.threshold_cycle_registry`다. 두 후보를 같은 slice에 섞지 않고, 선택한 후보별 old wrapper, CLI/import smoke, targeted tests를 먼저 확정한다. `src/trading -> src.engine.scalping`은 장기 hierarchy 목표로 등록하되 runtime entry/order hot path이므로 별도 `TradingToScalping` inventory와 pure type/util slice 검증 전에는 이동하지 않는다. `src/utils`는 `UtilsBoundaryAudit`로 shared primitive와 engine-owned automation/infrastructure 후보를 분리한 뒤 pure registry/helper slice만 검토한다.
  - 금지: 초기 slice에서 runtime/order/provider/threshold/bot restart 경로를 이동하지 않는다. bulk move, `MetaPathFinder` shim, preopen/postclose 안정 검증 전 wrapper 제거, retired/offline/backup 파일 재편입을 금지한다. `src/trading` 또는 `src/utils` 전체 일괄 이동, direct import rewrite, `src.engine.scalping.__init__` side effect, broker submit/qty/cooldown/stale quote/config env semantics 변경, 신규 순환 import 생성을 금지한다. `system_metric_sampler` 선택 시 cron/job id 의미를 변경하지 않고, `threshold_cycle_registry` 선택 시 `src.utils`와 `src.engine` 사이 신규 순환 import를 만들지 않는다.
  - 다음 액션: `monitoring_sampler_slice_selected`, `utils_registry_slice_selected`, `trading_to_scalping_inventory_required`, `utils_boundary_inventory_required`, `defer_dirty_worktree`, `consumer_migration_ready_keep_wrappers`, `wrapper_keep_required`, `blocked_by_runtime_path` 중 하나로 닫고, 구현 시 각 slice마다 `구현 -> 코드리뷰 -> 수정보완 -> 재검증` 결과를 남긴다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
