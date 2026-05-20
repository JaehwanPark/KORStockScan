# 2026-05-20 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-05-19` postclose -> `2026-05-20`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0520] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-20`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-19.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 실행 메모 (`2026-05-20 07:49 KST`): `threshold_apply_2026-05-20.json`은 `status=auto_bounded_live_ready`, `apply_mode=auto_bounded_live`, `runtime_change=true`, `source_date=2026-05-19`, `warnings=[]`였다. `threshold_runtime_env_2026-05-20.{json,env}`는 07:35 생성됐고 selected family는 `soft_stop_whipsaw_confirmation`, `latency_classifier_runtime_profile`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `lifecycle_decision_matrix_runtime`, `scalp_sim_scale_in_window_expansion`이다. swing approval은 `requested=0`, `approved=0`이며 별도 사용자 개입 artifact는 없었다. `logs/threshold_cycle_preopen_cron.log`에는 `[DONE] threshold-cycle preopen target_date=2026-05-20 finished_at=2026-05-20T07:35:01+0900`가 남았다.
  - 판정 결과: `applied_guard_passed_env`
  - 다음 액션: 장중에는 runtime threshold mutation 없이 `RuntimeEnvIntradayObserve0520`에서 selected family provenance와 rollback guard만 관찰한다.

- [x] `[OpenAIWSPreopenConfirm0520] OpenAI WS 유지 설정 및 entry_price/analyze_target provenance 확인` (`Due: 2026-05-20`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-19.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-19.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 OpenAI route/Responses WS 설정과 `analyze_target`, `entry_price` transport provenance를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 다음 액션: entry_price transport 표본이 부족하면 장중 표본 재확인 항목과 연결한다.
  - 실행 메모 (`2026-05-20 07:49 KST`): `run_bot.sh` 기본값은 `KORSTOCKSCAN_SCALPING_AI_ROUTE=openai`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true`, pool size `2`, timeout `15000ms`다. `bot_history.log` 07:40 startup에서 OpenAI 엔진 초기화, `메인 스캘핑 OpenAI 엔진 고정 완료`, `AI 라우팅 활성화: role=main route=openai (main_scalping_openai=ON / main_scalping_deepseek=OFF)`를 확인했다. 전일 WS 리포트는 unique WS calls `3960`, endpoint counts `analyze_target=3854`, `entry_price=106`, WS fallback `0`, success rate `1.0`, entry_price transport observable `106`으로 provenance 표본이 충분했다.
  - 판정 결과: `pass`
  - 다음 액션: provider transport 확인은 threshold/주문가/수량 guard 변경 근거로 쓰지 않고, 장중 실제 표본은 `RuntimeEnvIntradayObserve0520`/관련 provenance 관찰에서만 분리 확인한다.

## Runbook 운영 확인 완료 기록

- `PreopenAutomationHealthCheck20260520` (`Slot: PREOPEN`, `TimeWindow: 08:00~09:00`, `Track: RunbookOps`) 판정: `pass`
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md) `장전 확인 절차`
  - 근거: 07:35 preopen wrapper가 `[DONE]`으로 종료했고, error detector 로그의 07:35/07:40/07:45 run에서 `threshold_cycle_preopen_status=pass`, `threshold_runtime_env_status=pass`, `threshold_apply_plan_status=pass`가 확인됐다. 07:40 tmux `bot` 세션과 `bot_main.py` 프로세스가 기동 중이며 키움 WS 연결/로그인과 조건검색식 등록이 완료됐다.
  - 다음 액션: 반복 운영 확인은 완료로 보며, 이후 장중 항목은 별도 checklist owner가 소유한다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RuntimeEnvIntradayObserve0520] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-20`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-19.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, latency_classifier_runtime_profile, score65_74_recovery_probe가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.
  - 실행 메모 (`2026-05-20 09:37 KST`): `threshold_apply_2026-05-20.json`은 `status=auto_bounded_live_ready`, `apply_mode=auto_bounded_live`, `runtime_change=true`, `source_date=2026-05-19`였다. `threshold_runtime_env_2026-05-20.json/.env` selected family는 `soft_stop_whipsaw_confirmation`, `latency_classifier_runtime_profile`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `lifecycle_decision_matrix_runtime`, `scalp_sim_scale_in_window_expansion`이다. 장중 pipeline event에서는 `scalp_sim_candidate_window_expansion` 376건, `scalp_sim_scale_in_window_expansion` 30건, `soft_stop_whipsaw_confirmation` 28건의 provenance hit가 확인됐다. `latency_classifier_runtime_profile`과 `lifecycle_decision_matrix_runtime`은 env/policy 로드는 확인됐으나 09:37 기준 runtime event text hit는 아직 없었다. rollback mention은 0건이었다.
  - 판정 결과: `warning`
  - 근거: selected runtime env는 적용됐고 bot process/tmux도 실행 중이나, 일부 selected family는 아직 장중 event 표본이 부족하다. rollback guard breach 징후는 없다.
  - 다음 액션: 장중 runtime mutation 없이 다음 중간 점검에서 `latency_classifier_runtime_profile`/`lifecycle_decision_matrix_runtime` runtime event hit 발생 여부만 재확인한다.

- [x] `[SimProbeIntradayCoverage0520] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-20`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-19.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.
  - 실행 메모 (`2026-05-20 09:37 KST`): `data/runtime/scalp_live_simulator_state.json` active position은 8개이며 모두 `status=HOLDING`, `actual_order_submitted=false`였다. pipeline event nested `fields` 기준 sim/probe stage는 2,226건이고 `actual_order_submitted=false` 2,166건, `true` 0건이다. `None` 60건은 `swing_probe_state_restored/persisted`와 `scalp_sim_duplicate_buy_signal` 같은 state/provenance 이벤트이며 주문 실행 이벤트가 아니다. `broker_order_forbidden=true`도 2,166건으로 주문 금지 provenance가 유지됐다. `scalp_sim_ai_holding_live_call` 340건, `scalp_sim_ai_holding_deferred` 149건, `sim_ai_budget_exhausted` 149건, `sim_ai_critical_bypass` 207건으로 sim-only AI budget attribution도 남았다.
  - 판정 결과: `pass`
  - 근거: 실제 주문 제출 true 표본이 없고 active sim state도 false로 유지된다. source-quality 필드는 일부 state 이벤트에는 없지만 주문/체결형 sim event에는 `simulated_order=true`, `broker_order_forbidden=true`, `decision_authority=sim_observation_only`가 남아 real execution과 분리된다.
  - 다음 액션: sim/probe 성과는 장후 EV/source-quality 입력으로만 사용하고, broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.

## Runbook 운영 확인 완료 기록

- `IntradayAutomationHealthCheck20260520` (`Slot: INTRADAY`, `TimeWindow: 09:05~15:30`, `Track: RunbookOps`) 판정: `pass`
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md) `장중 확인 절차`
  - 근거: `tmux bot` 세션과 `bot_main.py` PID 16237이 실행 중이고, `error_detector --mode full --dry-run` 결과 `summary_severity=pass`였다. `cron_completion`, `process_health`, `artifact_freshness`, `resource_usage`, `stale_lock`가 모두 pass이며 `pipeline_events_age_sec=0.1`, `threshold_events_age_sec=0.1`, sentinel report들도 fresh 상태다.
  - 테스트/검증: `PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run` 실행 결과 pass.
  - 다음 액션: 장중 반복 확인은 완료로 보며, 이후 신규 fail/warning 알림이 오면 해당 detector/report owner로 분리 대응한다.

## 장후 체크리스트 (16:30~18:55)

- [x] `[ThresholdDailyEVReport0520] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-05-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-20.json), [runtime_approval_summary_2026-05-20.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-20.json)
  - 판정 기준: real/sim/combined split, selected/blocked family, runtime_change, warning을 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.
  - 처리 결과(2026-05-20 17:39 KST): `pass / daily_ev_split_available_runtime_apply_ready`. real `sample=2`, `avg_profit_rate_pct=-0.265`, sim `sample=343`, `avg=-0.4434`, combined `sample=345`, `avg=-0.4424`로 분리 확인했다. `runtime_apply.status=auto_bounded_live_ready`, `runtime_change=true`, selected family는 `soft_stop_whipsaw_confirmation`, `latency_classifier_runtime_profile`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `lifecycle_decision_matrix_runtime`다. 경고는 `lifecycle_ai_context_runtime_provenance_missing`, swing pending future quotes/sample floor, pattern lab propagation audit fail로 분리하며 live execution 품질 근거로 쓰지 않는다.

- [x] `[CodeImprovementWorkorderReview0520] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-05-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-20.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-20.md), [code_improvement_workorder_2026-05-20.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-20.json)
  - 판정 기준: selected_order_count=12와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.
  - 처리 결과(2026-05-20 17:39 KST): `pass / no_new_implement_now`. `source_order_count=38`, `selected_order_count=12`, 분류는 `attach_existing_family=18`, `design_family_candidate=6`, `defer_evidence=11`, `reject=3`이며 재생성 후 신규 `implement_now=0`이다. 앞서 사용자 지시로 처리한 runtime_effect=false 계열은 구현/리포트 재생성 후 workorder diff에서 닫힌 상태로 확인했다.

- [x] `[HumanInterventionSummary0520] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-20.json), [runtime_approval_summary_2026-05-20.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-20.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.
  - 처리 결과(2026-05-20 17:39 KST): `warning / one_approved_sim_only_artifact_next_preopen_pending`. 사용자 승인 artifact는 [scalp_sim_scale_in_window_expansion_2026-05-20.json](/home/ubuntu/KORStockScan/data/threshold_cycle/approvals/scalp_sim_scale_in_window_expansion_2026-05-20.json)이며 `approved=true`, `decision_authority=sim_observation_only`, `actual_order_submitted=false`다. swing approval은 `requested=0/approved=0`, panic approval request는 `0`, Codex 신규 implement_now는 `0`. Project/Calendar 동기화는 사용자가 표준 명령으로 수동 실행해야 한다.

- [x] `[SourceQualityWorkorderGapReview0520] source-quality/workorder 누락 보강 필요 여부 명시 판정` (`Due: 2026-05-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:25`, `Track: ScalpingLogic`)
  - Source: [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py), [build_code_improvement_workorder.py](/home/ubuntu/KORStockScan/src/engine/build_code_improvement_workorder.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: postclose `observation_source_quality_audit_2026-05-20`와 `code_improvement_workorder_2026-05-20`를 대조해 `soft_stop_whipsaw_confirmation.flow_state`, `loss_fallback_probe.fallback_reason`, `scalp_sim_panic_action_deduped` 반복 이벤트 throttle 보강이 workorder에 명시됐는지 확인한다.
  - 금지: source-quality/workorder gap을 runtime threshold mutation, real order gate, Telegram BUY/SELL, provider route, bot restart 근거로 쓰지 않는다.
  - 다음 액션: `covered_by_generated_workorder`, `manual_codex_order_required`, `next_day_checklist_required`, `defer_no_repro` 중 하나로 닫고, 자동 생성 workorder에 없으면 수동 구현 지시 대상 또는 다음 영업일 checklist 항목으로 승격한다.
  - 처리 결과(2026-05-20 19:20 KST): `pass / remediated_and_regenerated`. `observation_source_quality_audit_2026-05-20`는 `status=pass`, warning stage `0`, high-volume no-source-field stage `0`으로 재생성했다. `loss_fallback_probe.fallback_reason`과 `soft_stop_whipsaw_confirmation.flow_state`는 과거 이벤트 audit normalization 및 향후 runtime provenance 보강으로 닫았고, `scalp_sim_panic_action_deduped`는 동일 `position_id + epoch + level + action` 반복 로그를 interval throttle하도록 보강했다. 후행 `code_improvement_workorder`, `threshold_cycle_ev`, `runtime_approval_summary`, `pattern_lab_propagation_audit`, `threshold_cycle_postclose_verification`를 재생성했고, `pattern_lab_propagation_audit`와 postclose verification 모두 `pass`다. 5/21 checklist 항목은 신규 workorder 생성 요구가 아니라 재발 여부 확인으로 유지한다.

- [x] `[LifecycleAIContextV2Decision0520] AI-generated context v2 승격 필요 여부 판정` (`Due: 2026-05-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:45~17:55`, `Track: ScalpingLogic`)
  - Source: [lifecycle_ai_context.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_ai_context.py), [lifecycle_ai_context_2026-05-20.json](/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-05-20.json), [lifecycle_ai_context_attribution_2026-05-20.json](/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-05-20.json), [threshold_cycle_ev_2026-05-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-20.json)
  - 판정 기준: v1 deterministic summary context의 `context_applied_count`, stage별 `ai_action_alignment_rate`, `ai_action_delta_rate`, `ai_score_delta_avg`, `source_quality_adjusted_ev_pct`, `context_contribution_score`, no-context replay coverage를 확인하고, AI-generated context v2가 필요한지 판정한다.
  - v2 후보 조건: deterministic summary가 과도하게 기계적이거나 stage별 해석 누락이 확인되고, context 적용 표본/리플레이 표본이 충분하며, AI-generated context가 `ai_advisory_prompt_context_only`와 schema/forbidden uses를 유지할 수 있을 때만 `design_family_candidate`로 승격한다.
  - 금지: AI-generated context v2를 real order gate, deterministic bias, scale-in 생성, threshold env mutation, provider route, Telegram BUY/SELL, bot restart trigger로 직접 연결하지 않는다. v2 설계 전에는 `lifecycle_ai_context_v1` deterministic fallback을 유지한다.
  - 다음 액션: `keep_deterministic_v1`, `design_ai_generated_context_v2`, `hold_sample_until_attribution`, `workorder_candidate_context_quality`, `reject_runtime_risk` 중 하나로 닫고, v2 검토가 필요하면 다음 영업일 checklist와 code-improvement workorder에 parser-friendly 항목으로 남긴다.
  - 처리 결과(2026-05-20 17:39 KST): `hold_sample_until_attribution`. `lifecycle_ai_context_2026-05-20`은 `provider=none`, `status=deterministic_fallback`, `prompt_stage_count=3`, `runtime_effect=false`다. attribution은 `context_eligible_count=0`, `context_applied_count=0`, `no_context_replay_sample=0`, `stage_quality_counts.hold_sample=5`, warning=`lifecycle_ai_context_runtime_provenance_missing`이므로 오늘 v2 승격 근거가 없다.

- [x] `[ScalpSimLdmSamplePolicy0520] LDM 샘플 수집 목적의 scalp sim max_daily 160 및 reserve/bucket quota 구현` (`Due: 2026-05-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:25~17:45`, `Track: ScalpingLogic`)
  - Source: [lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_decision_matrix.py), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [threshold_runtime_env_2026-05-20.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-20.env)
  - 판정 기준: `SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY=80`이 LDM stage floor는 통과 가능하나 시간대/시장상태/action bucket 수집에는 부족한지 postclose 원장과 LDM row coverage로 확인한다. 다음 PREOPEN 적용 후보는 `160`으로 두되, 오전 소진 방지를 위해 `blocked_ai_score <= 60%`, `first_ai_wait >= 30%`, panic/euphoria lifecycle source는 별도 cap보다 reserve 소비 허용 원칙을 코드/테스트/문서에 반영한다.
  - 구현 기준: 시간대 reserve 초안은 `09:00~10:00 max 56`, `10:00~12:00 reserve 32`, `12:00~14:00 max 40`, `14:00~close reserve 32`로 시작한다. quota 판단은 sim-only candidate window에만 적용하며 real entry, broker submit, Telegram BUY/SELL, provider route, bot restart trigger와 연결하지 않는다.
  - 금지: 장중 runtime env 직접 수정, restart만으로 max_daily 변경, sim/probe 표본을 real execution 품질이나 실주문 전환 근거로 사용하는 것을 금지한다.
  - 다음 액션: `implemented_preopen_candidate_160_with_quota`, `implemented_160_only_quota_deferred`, `hold_80_sample_enough`, `needs_persistent_daily_counter_first`, `defer_source_quality_gap` 중 하나로 닫고, 후보 승인 시 다음 PREOPEN `threshold_cycle_preopen_apply` 산출물의 `KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY=160` 및 quota env/정책 반영 여부를 확인한다.
  - 처리 결과(2026-05-20 17:44 KST): `implemented_preopen_candidate_160_with_quota`. `SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY` 기본값과 operator runtime lock을 `160`으로 상향하고, sim-only candidate window에 `blocked_ai_score <= 60%`, `first_ai_wait >= 30%` reserve, 시간대 quota `09:00-10:00=56,10:00-12:00=32,12:00-14:00=40,14:00-15:30=32`를 구현했다. panic/euphoria source는 별도 cap 차단 대신 reserve 소비를 허용한다. 검증으로 [threshold_runtime_env_2026-05-21.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-21.env)에 `KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY=160` 및 quota env가 생성됨을 확인했다.

- [x] `[ShadowCanaryCohortReview0520] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-20`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 당일 변경/관찰 결과를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 상태 변동 여부를 닫는다.
  - 금지: shadow 금지, canary-only, baseline 승격 원칙을 코드/문서 상태와 분리하지 않는다.
  - 다음 액션: 변경이 있으면 기준문서와 checklist를 함께 갱신하고 cohort 잠금 필드를 남긴다.
  - 처리 결과(2026-05-20 17:39 KST): `pass / no_shadow_runtime_reopen`. 5/20 selected runtime family는 PREOPEN bounded env 후보 또는 sim-only/provenance-only 축이며, 폐기된 shadow 축 재개나 baseline 승격은 확인되지 않았다. 신규 `scalp_sim_candidate_window_expansion`, `scalp_sim_scale_in_window_expansion`, `lifecycle_ai_context`는 real order gate/provider/bot restart 권한이 없는 sim/advisory 계층으로 유지한다.

### Runbook 운영 확인 완료 기록

- `[PostcloseAutomationHealthCheck20260520]` 판정: `pass`
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [threshold_cycle_postclose_cron.log](/home/ubuntu/KORStockScan/logs/threshold_cycle_postclose_cron.log), [error_detection](/home/ubuntu/KORStockScan/data/report/error_detection/error_detection_2026-05-20.json)
  - 근거: `deploy/run_threshold_cycle_postclose.sh` status는 `succeeded`, 시작 `16:10:02`, 종료 `17:07:44`로 확인했다. `PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run` 결과 `summary_severity=pass`, `cron_completion=pass`, `artifact_freshness=pass`, `process_health=pass`, `resource_usage=pass`다. 20:05 이후 tuning monitoring, 21:00 이후 KOSPI update, 23시대 archive/cleanup은 아직 `not_yet_due`다.
  - 다음 액션: 지금 시점의 POSTCLOSE 핵심 체인은 pass로 닫고, 아직 due 전인 야간 cron은 해당 시간대 runbook 확인에서 별도 판정한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

## 수동 개발 반영 기록

- [x] `[SwingStrategyDiscoveryFollowupV1Implement0520] Swing Strategy Discovery Sim v1 label/EV/source-only 자동화체인 1차 구현` (`Due: 2026-05-20`, `Slot: POSTCLOSE`, `TimeWindow: 19:00~20:30`, `Track: SwingLogic`)
  - Source: [swing-strategy-discovery-sim-v1.md](/home/ubuntu/KORStockScan/docs/swing-strategy-discovery-sim-v1.md), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 판정 기준: candidate/arm 생성 후 label builder, EV report, sector/theme source, postclose wrapper, threshold EV/runtime summary/code-improvement source-only 연결이 모두 `runtime_effect=false` 계약을 유지한다.
  - 금지: 실주문, `recommendation_history` 대체, runtime env apply, broker guard 변경.
  - 실행 메모 (`2026-05-20 Codex`): `swing_sector_theme_source`, `swing_strategy_discovery_label_builder`, `swing_strategy_discovery_ev_report`를 추가하고 postclose wrapper에 `swing_daily_simulation -> discovery sim -> label builder -> discovery EV -> swing lifecycle audit` 순서를 연결했다. `threshold_cycle_ev`, `runtime_approval_summary`, `build_code_improvement_workorder`는 source-only 요약/주문만 소비한다.
  - 판정 결과: `implemented_source_only`
  - 다음 액션: 다음 postclose에서 `swing_strategy_discovery_ev_YYYY-MM-DD` 생성 여부와 `pending_future_quotes` 감소/성숙 label 갱신을 확인한다.

- [x] `[ErrorDetectorPipelineEventsStartupGrace0520] 장 시작 직후 pipeline_events stale 과민 fail 보정` (`Due: 2026-05-20`, `Slot: INTRADAY`, `TimeWindow: 09:00~09:10`, `Track: RuntimeStability`)
  - Source: [artifact_freshness.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/artifact_freshness.py), [run_error_detection.log](/home/ubuntu/KORStockScan/logs/run_error_detection.log)
  - 판정 기준: 09:00 정각 직후 `pipeline_events`가 존재하지만 직전 이벤트가 stale인 경우에도 `window_grace_sec` 내이면 startup grace로 처리하고, grace 이후 stale은 기존처럼 fail로 유지한다.
  - 금지: runtime threshold mutation, bot restart, order/provider 변경으로 해석하지 않는다.
  - 실행 메모 (`2026-05-20 Codex`): 09:00 error detection은 `pipeline_events: stale (923s > 600s)`로 fail 되었으나 09:05 재검사에서 `pipeline_events_age_sec=1.5`, `pipeline_events_status=pass`로 회복됐다. 파일 미존재에만 적용되던 startup grace를 파일 존재+stale에도 적용하도록 보정했다.
  - 판정 결과: `implemented_detector_grace_fix`
  - 테스트/검증: `src/tests/test_error_detector_artifact_freshness.py` 25개 통과, `py_compile` 통과, `error_detector --mode full` 재실행에서 `pipeline_events_status=pass`.
  - 다음 액션: 비critical `panic_buying_report` warning은 다음 scheduled sentinel cycle에서 생성 여부만 모니터링한다.

- [x] `[PanicSellTelegramTransitionFix0520] 패닉셀 단일시장 risk-off 구간 해제 알림 오발송 방지` (`Due: 2026-05-20`, `Slot: INTRADAY`, `TimeWindow: 09:08~09:20`, `Track: RuntimeStability`)
  - Source: [notify_panic_state_transition.py](/home/ubuntu/KORStockScan/src/engine/notify_panic_state_transition.py), [panic_sell_defense_2026-05-20.json](/home/ubuntu/KORStockScan/data/report/panic_sell_defense/panic_sell_defense_2026-05-20.json), [market_panic_breadth_2026-05-20.json](/home/ubuntu/KORStockScan/data/report/market_panic_breadth/market_panic_breadth_2026-05-20.json)
  - 판정 기준: `panic_state=NORMAL`이어도 `market_panic_breadth_single_market_risk_off_advisory=true`이면 텔레그램 전환 상태는 해제가 아니라 active watch로 해석한다.
  - 금지: panic source를 runtime threshold, order submit, auto sell, provider route, bot restart 변경으로 해석하지 않는다.
  - 실행 메모 (`2026-05-20 Codex`): 09:08 panic sell report는 `panic_state=NORMAL`이지만 `market_panic_breadth_single_market_risk_off_advisory=true`였다. 알림 모듈은 `panic_state`만 보고 `NORMAL -> release`로 해석할 수 있었으므로, 단일시장 risk-off를 `RECOVERY_WATCH` active phase로 파생해 해제 메시지를 막고 breadth watch 메시지로 분류하도록 보정했다.
  - 판정 결과: `implemented_alert_transition_fix`
  - 테스트/검증: `src/tests/test_notify_panic_state_transition.py`와 `src/tests/test_panic_sell_defense_report.py` 총 21개 통과, `py_compile` 통과, 현재 report dry-run 파생값은 `derived_state_value=RECOVERY_WATCH`, `derived_phase=active`, `message_context=market_breadth_watch`.
  - 다음 액션: 후속 panic report에서 `single_market_risk_off_advisory`가 유지되면 해제가 아니라 watch 상태로 유지하고, 전체 breadth/micro panic confirmation 여부만 계속 관찰한다.

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-05-20 15:46:58`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-05-20.md`
- `Trade Review`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
