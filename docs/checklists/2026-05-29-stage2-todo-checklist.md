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
  - 처리 결과(2026-05-29 KST 재확인): `partial_apply_with_blocked_families`.
  - 근거: [threshold_cycle_preopen_2026-05-29.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-05-29.status.json)은 `status=succeeded`, `apply_mode=auto_bounded_live`, `auto_apply=true`, `runtime_effect=preopen_runtime_env_apply_only`다. [threshold_apply_2026-05-29.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-29.json)은 `status=auto_bounded_live_ready`, `runtime_change=true`이며 runtime env 파일은 [threshold_runtime_env_2026-05-29.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-29.env)다. 현재 bot PID 환경에는 `KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED=true`, `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`, `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`, `KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED=true`, `KORSTOCKSCAN_SCALP_SIM_AI_BUDGET_ENABLED=true`, `KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_ENABLED=true`, `KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED=true`가 로딩되어 있다. 단, `entry_wait6579_score66_69_recovery_gate_v1`는 apply plan에 `runtime_apply_blocked_bridge_not_ready:runtime_blocked_contract_gap`, `runtime_apply_not_allowed`, `runtime_apply_bridge_auto_live_contract_missing`로 남아 있어 수동 env override 없이 blocked family로 분리한다.
  - 다음 액션: 적용된 PREOPEN env 축만 장중 provenance/rollback guard로 관찰하고, blocked family는 장후 bridge/source-quality 산출물에서 재판정한다. 장중 threshold mutation과 수동 env override는 하지 않는다.

- [x] `[OpenAIWSPreopenConfirm0529] OpenAI WS 유지 설정 및 entry_price/analyze_target provenance 확인` (`Due: 2026-05-29`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-28.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-28.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 OpenAI route/Responses WS 설정과 `analyze_target`, `entry_price` transport provenance를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 다음 액션: entry_price transport 표본이 부족하면 장중 표본 재확인 항목과 연결한다.
  - 처리 결과(2026-05-29 KST 재확인): `keep_ws_confirmed_with_entry_price_bedrock_override`.
  - 근거: [openai_ws_stability_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-28.json)은 `decision=keep_ws`, `ws_summary.n=4106`, `endpoint_counts.analyze_target=4101`, `endpoint_counts.entry_price=5`, `ws_success_rate=1.0`, `ws_http_fallback=0`이다. 현재 bot PID 환경은 `KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true`, `KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws`이며, `KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE=primary`, `KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_ENDPOINTS=entry_price,holding_flow`, `KORSTOCKSCAN_BEDROCK_PRIMARY_FAILBACK_TO_OPENAI=true`가 함께 로딩되어 있다. 당일 [pipeline_events_2026-05-29.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-29.jsonl)에서는 `analyze_target`이 `responses_ws`, `openai_ws_used=True`, `openai_ws_http_fallback=False`로 다수 기록됐고, `entry_price`는 의도된 `bedrock_primary` provenance로 기록됐다.
  - 다음 액션: `analyze_target`은 OpenAI Responses WS 유지, `entry_price`는 2026-05-26 운영 override의 Bedrock primary/OpenAI failback으로 분리 관찰한다. provider transport 확인을 threshold/order guard 변경으로 연결하지 않는다.

- [x] `[SwingPreFinalAutoAndFinalApprovalPreopen0529] 스윙 pre-final auto state 및 final approval artifact 확인` (`Due: 2026-05-29`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-28.json), [threshold_cycle_ev_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-28.json)
  - 판정 기준: pre-final은 parsed AI Tier2 auto state가 있어야 하고, final-stage는 사용자 승인 artifact가 있어야 한다.
  - 금지: 스윙 full-live 전환, cap release, provider/bot 변경, hard-safety 완화를 pre-final auto state로 처리하지 않는다.
  - 다음 액션: `pre_final_auto_selected`, `final_approval_artifact_present`, `blocked_by_policy` 중 하나로 닫는다.
  - 처리 결과(2026-05-29 07:26 KST): `blocked_by_policy`.
  - 근거: [swing_runtime_approval_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-28.json)은 `summary.requested=0`, `summary.approved=0`, `summary.blocked=14`, `runtime_change=false`, `approval_requests=[]`이며 주요 block reason은 `severe_downside_guard`다.
  - 다음 액션: 스윙 full-live 전환, cap release, provider/bot 변경, hard-safety 완화는 열지 않고 장후 source report 재판정까지 dry-run/sim-only 경계를 유지한다.

- [x] `[PreopenAutomationHealthCheck20260529] 장전 자동화체인 상태 확인` (`Due: 2026-05-29`, `Slot: PREOPEN`, `TimeWindow: 08:00~09:00`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [threshold_cycle_preopen_2026-05-29.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-05-29.status.json), [threshold_apply_2026-05-29.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-29.json)
  - 판정: `pass`.
  - 근거: 시간창 이후 확인 시 당일 preopen apply 산출물이 누락되어 표준 wrapper를 같은 날짜로 재실행했고, `threshold_cycle_preopen_2026-05-29.status.json`이 `status=succeeded`로 생성됐다. runtime env는 `threshold_runtime_env_2026-05-29.env`로 생성됐으며 approval request/contract gap은 없다.
  - 다음 액션: Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RuntimeEnvIntradayObserve0529] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-29`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-28.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime, entry_wait6579_score66_69_recovery_gate_v1가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.
  - 처리 결과(2026-05-29 KST 재확인): `partial_pass_with_blocked_wait6579_live_apply`.
  - 근거: 당일 [pipeline_events_2026-05-29.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-29.jsonl) 기준 `soft_stop_whipsaw_confirmation` 82건, `score65_74_recovery_probe` 129건, `scalp_sim_candidate_window_expansion` 2,794건, `scalp_sim_ai_budget_manager` 5,470건, `lifecycle_decision_matrix_runtime` 관련 provenance 25,388건이 확인됐다. `entry_wait6579_score66_69_recovery_gate_v1` 자체 live apply event는 없고 `wait6579_probe_canary_applied` stage 8건만 확인되며, 장전 apply plan의 `runtime_apply_blocked_bridge_not_ready:runtime_blocked_contract_gap`, `runtime_apply_not_allowed`, `runtime_apply_bridge_auto_live_contract_missing` 판정과 일치한다. rollback 관련 이벤트는 `same_symbol_loss_reentry_cooldown` 2건으로 hard guard 동작이며 selected runtime family rollback breach는 확인되지 않았다.
  - 다음 액션: 적용된 축은 장후 post-apply attribution으로 넘기고, `entry_wait6579_score66_69_recovery_gate_v1`는 live apply가 아니라 blocked/probe 상태로 유지해 bridge/source-quality 산출물에서 재판정한다. 장중 threshold mutation 또는 수동 env override는 하지 않는다.

- [x] `[SimProbeIntradayCoverage0529] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-29`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-28.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.
  - 처리 결과(2026-05-29 KST 재확인): `pass_with_source_quality_followup`.
  - 근거: 당일 [pipeline_events_2026-05-29.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-29.jsonl)의 strict sim/probe 집계는 34,325건이며 `actual_order_submitted=false`, `broker_order_forbidden=true` 계약 위반은 0건이다. 주요 stage는 `scalp_sim_panic_scale_in_blocked` 10,263건, `scalp_sim_panic_level1_partial_skipped_min_remaining` 7,536건, `scalp_sim_ai_holding_live_call` 2,442건, `scalp_sim_ai_holding_deferred` 1,514건, `scalp_sim_candidate_window_discarded` 1,129건, `scalp_sim_entry_armed/buy_order_virtual_pending/buy_order_assumed_filled/holding_started/sell_order_assumed_filled` 각 192건이다. source-quality provenance는 `sim submit-path guard verdict fields present before broker behavior tuning` 384건, `overnight_decision_coverage` 45건으로 확인됐다. bucket-directed sim match는 아직 `candidate_context_only` 678건으로만 남아 있어 matched 표본 생성은 장후/차기 장중 후속 관찰 대상이다.
  - 다음 액션: sim/probe EV는 실주문 전환 근거로 단독 사용하지 않고, matched bucket-directed sim 표본 부족(`candidate_context_only` 지속)은 postclose LDM/source-quality 입력과 다음 bucket identity 보강 검증으로 넘긴다.

- [x] `[IntradayAutomationHealthCheck20260529] 장중 자동화체인 상태 확인` (`Due: 2026-05-29`, `Slot: INTRADAY`, `TimeWindow: 09:05~15:30`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [pipeline_events_2026-05-29.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-29.jsonl), [threshold_events_2026-05-29.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-05-29.jsonl)
  - 판정: `pass`.
  - 근거: `bash deploy/run_error_detection.sh full`은 `summary_severity=pass`, cron completion/log scanner/Kiwoom auth/process health/artifact freshness/resource/stale lock 모두 pass로 종료됐다. bot main loop PID는 `8061`, `pipeline_events_age_sec=0.5`, `threshold_events_age_sec=0.5`이며 BUY Funnel Sentinel은 `SUBMIT_DROUGHT_CRITICAL`, HOLD/EXIT Sentinel은 `HOLD_DEFER_DANGER`, panic sell/buying은 모두 `NORMAL` 및 `report_only_no_mutation`이다.
  - 다음 액션: sentinel 이상치는 postclose source-quality/workorder 입력으로만 넘기고, 장중 threshold/order/provider/bot/env 변경은 하지 않는다. Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

운영 보완 기록(2026-05-29 07:40 KST 이후 확인): `시장 판독` 부팅 로그는 `risk=RISK_OFF`를 `하락장`으로 렌더링해 KOSPI 실시간 추세 판정처럼 오해될 수 있어 [kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py)에서 제거했다. `시장환경 초기화` 로그는 원본 MarketRegime snapshot 진단으로 유지한다. KOSPI_ML 보유/청산의 `kospi_regime_stop_loss` 경로는 구조적으로 `market_regime == BULL`이면 `STOP_LOSS_BULL`, 그 외는 `STOP_LOSS_BEAR`를 선택하는 exit hard threshold 경로다. 현재 기본값은 둘 다 `-3.0`이라 값 차이는 없지만, 향후 두 값이 달라지면 regime이 손절 발동 임계값에 직접 영향을 준다.

운영 보완 기록(2026-05-29 13:40 KST): Bucket Identity / Swing Source-Only Handoff 보완을 반영했다. `lifecycle_bucket_sim_auto_approval_2026-05-28`은 `approved_bucket_count=160`, `approved_bucket_rows=160`, `approved_unique_source_bucket_count=160`으로 catalog 대조 기준을 `source_bucket_id` 중심으로 보존한다. `swing_lifecycle_bucket_discovery_2026-05-28`은 implemented source-quality waiting sample을 raw `69`, candidate `13`, workorder `13`, total `26`으로 분리한다. Bottom rebound source는 selected candidate `40`, policy auto-loop `sim_auto_approved/promote_policy=true`, postclose verifier bottom rebound handoff `pass`로 닫혔다. 코드 검증은 관련 pytest `64+41+73 passed`, `py_compile`, `git diff --check` 통과이며, 봇 중단 후 산출물 재생성 및 검증 완료 뒤 기존 runtime env 기준으로 bot PID `99944`를 재기동했고 `error_detector --mode health_only --dry-run`은 `summary_severity=pass`다. threshold/order/provider/cap/broker guard 값은 변경하지 않았다.

## 장후 체크리스트 (16:30~18:55)

- [x] `[ThresholdDailyEVReport0529] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-05-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-05-28.json), [threshold_cycle_ev_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-28.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.
  - 판정: `live_bucket_ready_with_report_only_warnings`.
  - 근거: [threshold_cycle_ev_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-29.json)은 real sample `21` / avg `-0.3848`, sim sample `726` / avg `-0.7804`, combined sample `747` / avg `-0.7693`으로 real/sim/combined를 분리했다. [tuning_performance_control_tower_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-05-29.json)은 `primary_verdict=live_bucket_ready`, lifecycle sim-auto `123`, lifecycle live-auto ready `7`, real PnL tuning performance `false`, EV warning `3`이다. [threshold_cycle_postclose_verification_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-05-29.json)은 `status=pass`, missing/stale downstream link `0`이다.
  - 다음 액션: 다음 PREOPEN은 guard 통과 artifact만 소비한다. sim/combined EV는 source-quality와 후보 해석 입력으로만 쓰고 broker execution 품질, full-live 전환, cap/provider/bot 변경 근거로 쓰지 않는다.

- [x] `[CodeImprovementWorkorderReview0529] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-05-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-28.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-28.md), [code_improvement_workorder_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-28.json)
  - 판정 기준: selected_order_count=96와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.
  - 판정: `implemented_and_nonimplement_triaged_no_new_runtime_action`.
  - 근거: [code_improvement_workorder_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-29.json)은 `generation_id=2026-05-29-2a74a2866100`, selected `99`, non-selected `39`, selected `implement_now=2`, selected `attach_existing_family=97`, selected unimplemented runtime_effect=false `2`다. 당일 Codex pass에서 selected implement_now는 instrumentation/report/provenance 및 source-only 제외로 구현/보강했고, non-implement 재판정은 implement_now 승격 `0`, 기존 구현 유지 `12`, 기존 family/source evidence 유지 `8`, 설계 후보 유지 `5`, 중복 병합 `1`, evidence/manual review 보류 `10`, reject 유지 `3`으로 닫았다.
  - 다음 액션: workorder는 다음 재생성 lineage에서 diff만 확인한다. 신규 repo/runtime 수정은 사용자 구현 지시가 다시 있을 때만 수행하고, runtime/order/provider/threshold/bot 변경은 열지 않는다.

- [x] `[HumanInterventionSummary0529] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-29`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-28.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.
  - 판정: `observe_only_no_approval_artifact_required`.
  - 근거: [runtime_approval_summary_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-29.json)은 `runtime_mutation_allowed=false`, panic approval requested `0`, swing requested `0`, swing approved `0`이다. `entry_submit_drought_handoff_selected=true`와 BUY Funnel Sentinel `SUBMIT_DROUGHT_CRITICAL`은 source-quality/decision-integrity 입력이지 사용자 승인 artifact가 아니다.
  - 다음 액션: 누락 승인 요청은 없다. Project/Calendar 반영은 문서 parser 검증 후 사용자 표준 sync 명령으로만 수행하고, 다음 PREOPEN 적용 여부는 generated artifact와 verifier로 확인한다.

- [x] `[ShadowCanaryCohortReview0529] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-29`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 당일 변경/관찰 결과를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 상태 변동 여부를 닫는다.
  - 금지: shadow 금지, canary-only, baseline 승격 원칙을 코드/문서 상태와 분리하지 않는다.
  - 다음 액션: 변경이 있으면 기준문서와 checklist를 함께 갱신하고 cohort 잠금 필드를 남긴다.
  - 판정: `no_runtime_classification_change`.
  - 근거: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)에 2026-05-29 addendum을 추가했다. 신규 `remove`, 신규 `baseline-promote`, 신규 alpha shadow는 없고, active-canary/source-only/sim-only cohort 구분은 유지된다. runtime apply gap은 `codex_directive_count=0`, `critical_failure_count=0`이며 retry queue `1`은 다음 PREOPEN/postclose 확인 대상이다.
  - 다음 액션: live-auto ready bucket은 다음 PREOPEN artifact guard 통과분만 소비한다. cohort 분류 변경이나 baseline 승격은 별도 workorder/rollback guard 없이 수행하지 않는다.

- [x] `[MarketRegimeUsageReview0529] market regime 사용 권한과 runtime 영향 정리` (`Due: 2026-05-29`, `Slot: POSTCLOSE`, `TimeWindow: 17:30~17:45`, `Track: RuntimeStability`)
  - Source: [sniper_market_regime.py](/home/ubuntu/KORStockScan/src/engine/sniper_market_regime.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: market regime 사용처를 `scalping entry no-hard-gate`, `swing entry baseline_prior`, `confirmed_risk_context block`, `KOSPI_ML exit stop-loss threshold selector`, `ADM/LDM runtime feature`, `panic breadth report-only context`로 분리해 현재 runtime/order 영향과 금지 권한을 정리한다.
  - 금지: `risk=RISK_OFF` 또는 `allow_swing=false` 단독으로 신규 threshold, stop, provider, bot restart, 실주문 전환, 스윙 full-live 전환을 열지 않는다.
  - 다음 액션: `documented_current_contract`, `needs_code_workorder`, `needs_doc_contract_patch`, `blocked_by_policy` 중 하나로 닫고, KOSPI_ML `STOP_LOSS_BULL/BEAR`가 같은 값인지와 향후 값 차이 발생 시 승인 경로를 명시한다.
  - 판정: `documented_current_contract`.
  - 근거: `sniper_market_regime.py`와 `sniper_state_handlers.py` 기준으로 market regime은 confirmed risk context에서만 block 성격을 갖고, unconfirmed `allow_swing=false`는 baseline_prior/source context로 기록된다. [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)의 continuous contract도 market regime을 runtime feature/report-only context로 제한한다. KOSPI_ML exit stop selector는 `BULL`이면 `STOP_LOSS_BULL`, 그 외는 `STOP_LOSS_BEAR`를 읽으며 코드 fallback은 동일값 `-2.5`/`-2.5`다.
  - 다음 액션: 현재는 code workorder가 필요 없다. 향후 `STOP_LOSS_BULL/BEAR`를 다른 값으로 분기하거나 market regime을 threshold/stop/provider/bot/order 권한으로 확장하려면 approval artifact, runtime env key, rollback guard, same-stage owner를 새로 둔다.

- [x] `[RuntimeApplyGapDirectiveReview0529] runtime apply gap Codex 작업지시 표면화 및 구현 여부 확인` (`Due: 2026-05-29`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-05-28.json), [runtime_apply_gap_audit_2026-05-28.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-05-28.md), [runtime-apply-gap-audit-user-guide.md](/home/ubuntu/KORStockScan/docs/runtime-apply-gap-audit-user-guide.md)
  - 판정 기준: runtime apply gap audit의 Codex 작업지시 `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`:lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq(block=positive_edge_must_not_default_to_source_only_keep_collecting), `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`:lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid(block=positive_edge_must_not_default_to_source_only_keep_collecting), `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`:lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui(block=positive_edge_must_not_default_to_source_only_keep_collecting), `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`:lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi(block=positive_edge_must_not_default_to_source_only_keep_collecting), `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`:lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq(block=positive_edge_must_not_default_to_source_only_keep_collecting) 외 3건를 구현 필요, 이미 해결, 설계 보류, reject로 분류한다.
  - 금지: 작업지시를 approval artifact나 즉시 runtime env 수정으로 해석하지 않는다. broker/order/provider/cap guard 우회와 장중 threshold mutation은 금지한다.
  - 다음 액션: `implement_now`, `already_implemented`, `defer_design`, `reject`, `needs_new_workorder` 중 하나로 닫고, 구현 시 테스트와 postclose verifier handoff를 같이 확인한다.
  - 판정: `already_implemented_no_codex_directive`.
  - 근거: [runtime_apply_gap_audit_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-05-29.json)은 `status=warning`이지만 `codex_directive_count=0`, `critical_failure_count=0`, `ai_review_status=parsed`, `ai_review_retry_pending=false`, retry queue `1`이다. [threshold_cycle_postclose_verification_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-05-29.json)은 handoff 누락 없이 pass다.
  - 다음 액션: 신규 implement_now 또는 needs_new_workorder는 없다. retry queue `1`은 다음 PREOPEN/postclose source-quality 확인으로 넘기고, runtime env 직접 수정은 하지 않는다.

- [x] `[CodebaseImprovementPlanSupplement0529] 오늘 코드베이스 개선 사항을 반영한 리팩터링 작업계획서 보완` (`Due: 2026-05-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [codebase_performance_workorder_2026-05-28.json](/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-05-28.json), [src-engine-refactor-inventory.md](/home/ubuntu/KORStockScan/docs/proposals/src-engine-refactor-inventory.md), [lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_decision_matrix.py), [test_lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/tests/test_lifecycle_decision_matrix.py)
  - 판정 기준: 오늘 구현된 lifecycle join gap 해소, bundle EV attribution 보강, 관련 테스트/검증 결과를 `src-engine-refactor-inventory.md`의 safe-slice 계획과 consumer/risk/재개 조건에 반영할지 검토한다.
  - 판정 기준: codebase performance workorder와 code improvement workorder는 입력 근거로만 사용하고, 장후 항목의 목적은 즉시 파일 이동/대규모 리팩터링이 아니라 작업계획서 보완으로 한정한다.
  - 금지: runtime/order/provider/threshold/bot restart 경로 이동, cron/job id 변경, output path/JSON schema/metric semantics 변경, wrapper 제거, direct import bulk rewrite를 수행하지 않는다.
  - 다음 액션: `plan_supplemented`, `already_reflected`, `defer_after_postapply_verification`, `needs_new_workorder` 중 하나로 닫고, 문서 수정 시 parser 검증과 표준 수동 sync 명령 안내를 남긴다.
  - 판정: `plan_supplemented_no_new_safe_slice`.
  - 근거: [src-engine-refactor-inventory.md](/home/ubuntu/KORStockScan/docs/proposals/src-engine-refactor-inventory.md)에 2026-05-29 POSTCLOSE 보강 판정을 추가했다. [codebase_performance_workorder_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-05-29.json)은 accepted `7`, implemented `7`, pending accepted `0`, deferred `3`, rejected `2`로 닫혔고, 당일 변경은 report/provenance/instrumentation 보강이라 safe-slice 파일 이동을 새로 열지 않는다.
  - 다음 액션: `system_metric_sampler` 등 파일 이동 후보는 deploy/cron/error detector/test import consumer inventory와 old/new smoke plan이 준비될 때 다시 판단한다. 오늘은 wrapper 제거, cron/job id 변경, output path/JSON schema/metric semantics 변경을 하지 않는다.

## Runbook 운영 확인 기록

- [x] `[PostcloseAutomationHealthCheck20260529] 장후 자동화체인 상태 확인` (`Due: 2026-05-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~20:45`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정: `warning`
  - 근거: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)에 완료 기록을 추가했다. postclose chain은 재실행 후 `[DONE]`으로 종료됐고 verifier는 pass다. warning은 runtime apply gap retry queue `1`과 의도적 postclose bot isolation에 한정된다.
  - 다음 액션: 다음 PREOPEN 전까지 bot restart, runtime env 직접 수정, provider/threshold/order guard 변경을 하지 않는다. Project/Calendar 반영은 표준 수동 sync 명령으로만 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->









## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-05-29 15:46:45`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-05-29.md`
- `Trade Review`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
