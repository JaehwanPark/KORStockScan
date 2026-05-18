# 2026-05-18 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

### PreopenAutomationHealthCheck20260518 운영 확인 기록

- checked_at: `2026-05-18 08:50 KST`
- 판정: `pass`
- 대상: `[ThresholdEnvAutoApplyPreopen0518]`, `[OpenAIWSPreopenConfirm0518]`, `[SwingApprovalArtifactPreopen0518]`, `[Runbook 운영 확인] 장전 자동화체인 상태 확인`
- 근거: `logs/threshold_cycle_preopen_cron.log`에 `2026-05-18` preopen `[DONE]` marker가 있고, `threshold_apply_2026-05-18.json`은 status=`auto_bounded_live_ready`, apply_mode=`auto_bounded_live`, runtime_change=`true`, source_date=`2026-05-15`다. runtime env는 `threshold_runtime_env_2026-05-18.{env,json}`으로 생성됐고 selected family는 `bad_entry_refined_canary`, `swing_one_share_real_canary_phase0`, `swing_gatekeeper_reject_cooldown`이다. env override는 `KORSTOCKSCAN_SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED=true`, `KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_ENABLED=true`, `KORSTOCKSCAN_ML_GATEKEEPER_REJECT_COOLDOWN=6600`, `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true`를 포함한다.
- OpenAI WS: `src/run_bot.sh`는 startup env로 `KORSTOCKSCAN_SCALPING_AI_ROUTE=openai`, `KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true`를 고정하고, `openai_ws_stability_2026-05-15.md`는 decision=`keep_ws`, unique WS calls=`763`, WS fallback=`0/763`, endpoint counts=`analyze_target:762`, `entry_price:1`, entry_price instrumentation_gap=`False`로 닫혔다.
- swing approval: `swing_runtime_approval_2026-05-15.json`은 approval request 3건을 만들었고, 별도 approval artifact `data/threshold_cycle/approvals/swing_runtime_approvals_2026-05-15.json`과 `data/threshold_cycle/approvals/swing_one_share_real_canary_2026-05-15.json`이 존재한다. preopen apply는 `swing_gatekeeper_reject_cooldown`과 `swing_one_share_real_canary_phase0`만 env에 반영했고, `swing_model_floor`는 selected=`false`, decision_reason=`no_runtime_env_override`로 유지했다. `swing_scale_in_real_canary_phase0`는 scale-in approval artifact 없음으로 차단 상태다.
- runbook 운영 확인: `tmux bot` 세션은 `2026-05-18 07:40 KST`에 기동 상태이고, `src/run_bot.sh`는 오늘 runtime env 파일을 기다린 뒤 source하도록 되어 있다. `logs/ensemble_scanner.log`에는 `final_ensemble_scanner target_date=2026-05-18` `[DONE]` marker와 V2 CSV 3개 종목 적재 로그가 있다. `data/daily_recommendations_v2.csv`는 3행이며 diagnostics는 selected_count=`3`, selection_mode=`SELECTED`다.
- 금지 확인: 확인 과정에서 threshold/provider/order guard, 스윙 dry-run guard, bot restart, broker 주문 상태를 변경하지 않았다. OpenAI provider provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리했다.
- 다음 액션: 오늘 PREOPEN Project 항목은 완료로 닫는다. 장중에는 runtime threshold mutation 없이 selected family provenance, one-share real canary receipt, sim/probe `actual_order_submitted=false` split을 기존 INTRADAY checklist에서 계속 확인한다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.

### PanicSellNotificationOrderFix0518 확인 기록

- checked_at: `2026-05-18 09:35 KST`
- 판정: `fixed_report_only_notification`
- 근거: `logs/run_panic_sell_defense_cron.log`에서 `PANIC_SELL -> RECOVERY_CONFIRMED -> RECOVERY_WATCH -> RECOVERY_CONFIRMED -> RECOVERY_WATCH/PANIC_SELL` 전이가 짧은 간격으로 발생했고, 기존 notifier는 `RECOVERY_CONFIRMED`를 즉시 release로 보내 다음 `RECOVERY_WATCH`를 새 start로 보내는 구조였다. 이 때문에 사용자 수신 순서가 `패닉셀 경보 해제` 뒤 `패닉셀 주의`로 보일 수 있었다.
- 조치: `notify_panic_state_transition`에서 패닉셀 `RECOVERY_CONFIRMED` 1회 관측은 `release_pending`으로 보류하고, 다음 관측이 계속 `RECOVERY_CONFIRMED` 또는 `NORMAL`일 때만 해제 알림을 보내도록 수정했다. 다음 관측이 `RECOVERY_WATCH` 또는 `PANIC_SELL`이면 해제 알림 없이 active 상태를 유지한다.
- 금지 확인: 알림 hysteresis만 보정했고 panic report 판정, threshold/provider/order guard, 자동매도, bot restart, broker 주문 상태는 변경하지 않았다.
- 다음 액션: 장중 panic sell defense 다음 cycle에서 `panic state Telegram notify status`가 `release_pending`, `no_transition`, `sent` 중 어떤 상태로 닫히는지 로그로 확인한다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.

### PanicSellRecoveryConfirmedSensitivityFix0518 확인 기록

- checked_at: `2026-05-18 09:45 KST`
- 판정: `fixed_report_only_state_gate`
- 근거: `RECOVERY_CONFIRMED`는 active sim/probe, post-sell rebound, microstructure recovery 중 하나만 만족해도 열릴 수 있었다. 오늘처럼 live market breadth `risk_off_advisory=true`와 market risk-off가 남아 있는 구간에서는 개별 microstructure `recovery_confirmed_count>0` 단독으로 경보 해제 성격의 `RECOVERY_CONFIRMED`를 여는 것이 과민했다.
- 조치: `panic_sell_defense_report`에서 `confirmed_risk_off_advisory=true` 또는 `market_panic_breadth_risk_off_advisory=true`가 남아 있으면 `micro_recovery_confirmed` 단독으로는 `RECOVERY_CONFIRMED`를 반환하지 않고 `RECOVERY_WATCH`로 제한하도록 보정했다. active sim/probe와 post-sell rebound 기반 confirmation은 기존 기준을 유지한다.
- 금지 확인: report-only 상태 판정 gate만 보정했고 threshold/provider/order guard, 자동매도, bot restart, broker 주문 상태는 변경하지 않았다.
- 다음 액션: 다음 panic sell defense cycle에서 market risk-off가 유지되는 동안 `microstructure recovery confirmed but market risk-off remains` reason이 `RECOVERY_WATCH`로 라우팅되는지 확인한다.

### IntradayAutomationHealthCheck20260518 운영 확인 기록

- checked_at: `2026-05-18 09:41 KST`
- 판정: `pass_with_not_yet_due_subcheck`
- 대상: `[RuntimeEnvIntradayObserve0518]`, `[SimProbeIntradayCoverage0518]`, `[Runbook 운영 확인] 장중 자동화체인 상태 확인`
- 근거: `data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-18.json`은 selected family=`bad_entry_refined_canary`, `swing_one_share_real_canary_phase0`, `swing_gatekeeper_reject_cooldown`이고 `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true`를 유지한다. `data/threshold_cycle/threshold_events_2026-05-18.jsonl`은 09:39 기준 fresh이며 `bad_entry_refined_candidate` 8건, `actual_order_submitted=False` 16건, rollback mention 0건을 기록했다. `soft_stop_whipsaw_confirmation`은 전일 checklist 원문 기준 selected로 적혀 있었지만 오늘 runtime env에는 포함되지 않았으므로 현재 장중 owner로 보지 않는다.
- sim/probe split: `data/pipeline_events/pipeline_events_2026-05-18.jsonl`은 09:40 기준 fresh이고 `actual_order_submitted=False` 1336건, `decision_authority=source_quality_only` 78827건을 기록했다. `scalp_sim_*`, `swing_probe_*`, `swing_sim_*`, `blocked_swing_*` stage가 관찰됐고 sim/probe는 real execution이나 broker order submit 근거로 사용하지 않았다.
- runbook 운영 확인: buy funnel sentinel, holding/exit sentinel, panic sell defense, panic buying은 09:40 전후 `[DONE]` marker와 fresh report를 생성했다. `panic_sell_defense_report --print-json`은 `panic_state=PANIC_SELL`, `runtime_effect=report_only_no_mutation`이고 `panic_buying_report --print-json`은 `panic_buy_state=NORMAL`, `runtime_effect=report_only_no_mutation`이다. `threshold_cycle_calibration_intraday`는 12:05~12:30 window 전이라 `not_yet_due`로 분리했다.
- 검증: `bash deploy/run_error_detection.sh full` 결과 summary_severity=`pass`, detector_count=`7`, `cron_completion`은 intraday calibration 등 미래 window를 `not_yet_due`로 분류했고 process/artifact/resource/lock detector는 pass였다.
- 금지 확인: 장중 threshold mutation, provider 변경, order guard 변경, bot restart, broker order submit, 스윙 dry-run guard 변경을 수행하지 않았다.
- 다음 액션: 12:05 이후 `threshold_cycle_calibration_intraday` `[DONE]` marker와 `threshold_cycle_ai_review_2026-05-18_intraday.md` 생성을 다시 확인한다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-05-15` postclose -> `2026-05-18`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0518] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-18`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-15.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 판정: `applied_guard_passed_env`.
  - 근거: `threshold_apply_2026-05-18.json` status=`auto_bounded_live_ready`, runtime env selected families=`bad_entry_refined_canary`, `swing_one_share_real_canary_phase0`, `swing_gatekeeper_reject_cooldown`; `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true` 유지.

- [x] `[OpenAIWSPreopenConfirm0518] OpenAI WS 유지 설정 및 entry_price/analyze_target provenance 확인` (`Due: 2026-05-18`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-15.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-15.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 OpenAI route/Responses WS 설정과 `analyze_target`, `entry_price` transport provenance를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 다음 액션: entry_price transport 표본이 부족하면 장중 표본 재확인 항목과 연결한다.
  - 판정: `pass_keep_ws`.
  - 근거: startup env는 OpenAI Responses WS 고정이고, `openai_ws_stability_2026-05-15.md`는 decision=`keep_ws`, analyze_target=`762`, entry_price=`1`, WS fallback=`0/763`, entry_price instrumentation_gap=`False`.

- [x] `[SwingApprovalArtifactPreopen0518] 스윙 approval request 및 별도 승인 artifact 존재 여부 확인` (`Due: 2026-05-18`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-05-15.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-15.json), [threshold_cycle_ev_2026-05-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-15.json)
  - 판정 기준: approval request가 있더라도 사용자 승인 artifact가 없으면 env apply 대상이 아니다.
  - 금지: 스윙 dry-run 해제, real canary, floor, scale-in real canary를 서로 자동 승인하지 않는다.
  - 사용자 승인 요청/승인 현황 표면화: `swing_model_floor` approval_id=`swing_runtime_approval:2026-05-15:swing_model_floor`, `swing_gatekeeper_reject_cooldown` approval_id=`swing_runtime_approval:2026-05-15:swing_gatekeeper_reject_cooldown`, `swing_one_share_real_canary_phase0` approval_id=`swing_one_share_real_canary:2026-05-15:phase0`는 사용자 승인 artifact 생성 완료 상태로 확인한다.
  - 다음 액션: 최종 보고에 `사용자 승인 필요/승인 완료` 섹션을 별도로 쓰고, 각 approval_id, artifact path, selected env, blocked reason을 `approval_artifact_present`, `approval_artifact_missing`, `blocked_by_policy` 중 하나로 닫는다.
  - 판정: `approval_artifact_present`.
  - 근거: `swing_runtime_approvals_2026-05-15.json`과 `swing_one_share_real_canary_2026-05-15.json`이 존재한다. preopen apply는 `swing_gatekeeper_reject_cooldown`, `swing_one_share_real_canary_phase0`를 selected env로 반영했고 `swing_model_floor`는 selected=`false`/`no_runtime_env_override`, scale-in real canary는 approval artifact 없음으로 차단했다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RuntimeEnvIntradayObserve0518] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-18`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-15.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.
  - 판정: `pass_current_runtime_env_provenance`.
  - 근거: 오늘 runtime env selected family는 `bad_entry_refined_canary`, `swing_one_share_real_canary_phase0`, `swing_gatekeeper_reject_cooldown`이며, `soft_stop_whipsaw_confirmation`은 현재 env owner가 아니다. threshold event stream에는 `bad_entry_refined_candidate` 8건과 rollback mention 0건이 확인됐다.

- [x] `[SimProbeIntradayCoverage0518] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-18`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-15.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.
  - 판정: `pass_sim_probe_split_preserved`.
  - 근거: pipeline events 기준 `actual_order_submitted=False` 1336건, threshold events 기준 `actual_order_submitted=False` 16건이 확인됐고, `decision_authority=source_quality_only`와 report-only/runtime_effect split이 유지됐다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[ThresholdDailyEVReport0518] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-05-18`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-15.json)
  - 판정 기준: real/sim/combined split, selected/blocked family, runtime_change, warning을 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[CodeImprovementWorkorderReview0518] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-05-18`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-15.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-15.md), [code_improvement_workorder_2026-05-15.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-15.json)
  - 판정 기준: selected_order_count=12와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0518] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-18`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-15.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `승인 artifact 필요`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: 최종 사용자 보고에 `승인 필요/승인 완료`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`을 별도 소제목으로 풀어 쓰고, approval request가 있으면 항목별 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 여부를 반드시 노출한다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[ShadowCanaryCohortReview0518] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-18`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 당일 변경/관찰 결과를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 상태 변동 여부를 닫는다.
  - 금지: shadow 금지, canary-only, baseline 승격 원칙을 코드/문서 상태와 분리하지 않는다.
  - 다음 액션: 변경이 있으면 기준문서와 checklist를 함께 갱신하고 cohort 잠금 필드를 남긴다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->


## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
