# 2026-06-09 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-04`, `clean_tuning_baseline_ts_kst=2026-06-04T14:29:09+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.
- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-06-08` postclose -> `2026-06-09`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[SwingPreFinalAutoAndFinalApprovalPreopen0609] 스윙 pre-final auto state 및 final approval artifact 확인` (`Due: 2026-06-09`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-08.json), [threshold_cycle_ev_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-08.json)
  - 판정 기준: pre-final은 parsed AI Tier2 auto state가 있어야 하고, final-stage는 사용자 승인 artifact가 있어야 한다.
  - 금지: 스윙 full-live 전환, cap release, provider/bot 변경, hard-safety 완화를 pre-final auto state로 처리하지 않는다.
  - 다음 액션: `pre_final_auto_selected`, `final_approval_artifact_present`, `blocked_by_policy` 중 하나로 닫는다.
  - 처리 결과: `blocked_by_policy`.
  - 판정: 스윙 pre-final auto 적용 대상과 final-stage 사용자 승인 artifact가 없어 runtime 반영을 열지 않는다.
  - 근거: `swing_runtime_approval_2026-06-08.json` summary는 `requested=0`, `approved=0`, `blocked=12`, `runtime_change=false`다. `threshold_apply_2026-06-09.json`의 `swing_runtime_approval`도 `approval_artifact=null`, `requested=0`, `approved=0`, `selected=[]`, `dry_run_forced=false`, `legacy_phase0_real_canary_ignored=false`다. `threshold_cycle_ev_2026-06-08.json`의 swing runtime approval 요약도 `requested=0`, `approved=0`, `selected_live_dry_run=0`이다.
  - 다음 액션: full-live 전환, cap release, provider/bot 변경, hard-safety 완화는 별도 final user approval artifact가 생기기 전까지 차단 유지. 오늘은 `swing_sim_auto_approval` sim policy env만 관찰 대상으로 둔다.

- [x] `[ThresholdEnvAutoApplyPreopen0609] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-06-09`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-08.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 처리 결과: `partial_apply_with_blocked_families`.
  - 판정: preopen wrapper와 runtime env 생성은 pass지만, bridge live-auto 후보는 계약/품질 차단으로 수동 우회하지 않는다.
  - 근거: `threshold_cycle_preopen_2026-06-09.status.json`은 `status=succeeded`, `exit_code=0`, `finished_at=2026-06-09T07:35:01+09:00`이고, `threshold_apply_2026-06-09.json`은 `status=auto_bounded_live_ready`, `apply_mode=auto_bounded_live`, `runtime_change=true`, `runtime_env_file=/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-09.env`, `warnings=[]`다. `threshold_runtime_env_2026-06-09.json` selected families는 `soft_stop_whipsaw_confirmation`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `lifecycle_decision_matrix_runtime`, `scalp_sim_auto_approval`, `swing_sim_auto_approval`다. `runtime_apply_bridge`는 `entry_wait6579_score66_69_recovery_gate_v1`이 `blocked_source_quality`/`auto_live_contract_missing`, `scale_in_bucket_runtime_policy_v1`이 `bootstrap_pending`/`auto_live_contract_missing`으로 selected 없음.
  - 다음 액션: 생성된 `threshold_runtime_env_2026-06-09.env`만 runtime source로 인정한다. bridge blocked family, approval artifact missing, same-stage owner conflict는 postclose source-quality/contract workorder로만 넘기고 장중 env override 금지.

운영 확인 메모: `[PreopenAutomationHealthCheck20260609]` 판정은 `warning`. `threshold_cycle_preopen_cron.log`에는 2026-06-09 `[DONE] threshold-cycle preopen` marker가 있고 status artifact도 `succeeded`다. `ensemble_scanner.log`에는 `final_ensemble_scanner target_date=2026-06-09` `[DONE]` marker가 있고 `data/daily_recommendations_v2.csv`는 2026-06-08 20:43 `update_kospi` chain 산출물로 2개 row를 보유한다. 봇 tmux 세션은 07:40 기동됐고 `bot_history.log`는 runtime/env 이후 정상거래일 엔진, WebSocket 연결/login, 조건식 등록, OpenAI route 초기화를 기록했다. 단, macro briefing은 Gemini `429 RESOURCE_EXHAUSTED` 후 cache fallback을 사용했으므로 장전 자동화 핵심 체인은 통과하되 provider/billing 운영 경고로 분리한다. `error_detection_2026-06-09.json`은 `summary_severity=pass`, process/artifact/resource/stale-lock 모두 pass다.

운영자 장전 override 메모: `[OperatorPreopenEntryPriceDefensiveTicks0609]` 판정은 `applied_operator_runtime_override`. 2026-06-09 08:29 KST 사용자 지시로 실제 SCALPING 진입 제출가만 더 보수적으로 적용했다. `src.engine.sniper_entry_latency`에 `KORSTOCKSCAN_SCALPING_NORMAL_DEFENSIVE_TICKS` env support를 추가했고, 오늘 runtime env `threshold_runtime_env_2026-06-09.env/json`에 `KORSTOCKSCAN_SCALPING_NORMAL_DEFENSIVE_TICKS=3`, source=`operator_preopen_override_2026-06-09`를 기록했다. 10,000원 smoke 기준 `order_price=9,970`, `entry_price_defensive_ticks=3`, `counterfactual_order_price_1tick=9,990`을 확인했다. 08:31 KST 봇 tmux 세션을 재기동했고 `/proc/<bot_main>/environ`에서 해당 env가 로드된 것을 확인했다. 변경 범위는 실제 SCALPING order price defensive tick뿐이며 broker/stale/account/order/quantity/cooldown guard, provider route, BUY threshold, cap은 변경하지 않는다. rollback env는 `KORSTOCKSCAN_SCALPING_NORMAL_DEFENSIVE_TICKS=1`.

동적 진입가격 튜닝 점검 메모: `[DynamicEntryPriceTuningCheck0609]` 판정은 `hard_gate_like_hold_sample`. `threshold_apply_2026-06-09.json`에서 `pre_submit_price_guard`는 `threshold_version=pre_submit_price_guard:observe_only:hold_sample`, `calibration_state=hold_sample`, `apply_mode=report_only_calibration`, `runtime_change=false`이고 calibration reason은 `latency_classifier runtime semantics 기준 후보가 없어 pre_submit_price_guard는 현행 유지`다. `strength_momentum_soft_gate_p1`, `overbought_pullback_guard_p1`, `liquidity_pre_submit_guard_p1`도 `report_only_calibration`이며 `allowed_runtime_apply=false`로 approval artifact 전 자동 runtime apply 금지다. 현재 동적 진입가격은 AI canary와 pre-submit guard가 stale/품질 불량을 block하거나 reference target을 bps guard 안에서만 적용하는 구조라, 실시간 가격을 유연하게 튜닝하는 family라기보다 hard quality gate에 가깝다. 다음 액션은 장후 `ThresholdDailyEVReport0609`/`CodeImprovementWorkorderReview0609`에서 `pre_submit_price_guard`의 submitted/fill/cancel/late-fill 비용과 dynamic resolver workorder 필요 여부를 분리 확인한다.

동적 진입가격 튜닝 분리 구현 메모: `[DynamicEntryPriceResolverSplit0609]` 판정은 `implemented_report_contract`. `pre_submit_price_guard`는 broker 제출 직전 safety/source-quality report 전용으로 축소하고 `allowed_runtime_apply=false`로 닫았다. `dynamic_entry_price_resolver`는 `bid-1`, `bid-2`, `bid-3`, `best_bid`, `AI_candidate`, `reference_target`, `timeout_15s`, `timeout_30s` 후보별 `fill_rate`, `full_fill_rate`, `partial_fill_rate`, `cancel_rate`, `late_fill_rate`, `missed_upside`, `source_quality_adjusted_ev_pct`를 요구하는 다음 PREOPEN bounded 후보 owner로 분리했다. `entry_price_execution_quality`는 real-only 제출/체결/취소/late-fill audit이며 sim EV와 섞지 않는다. 이 구현은 장중 threshold mutation, provider route, broker/order/quantity/cooldown guard, bot restart를 변경하지 않는다. 다음 액션은 장후 산출물에서 dynamic resolver 필수 지표 결손과 swing micro source-quality gap을 workorder로 닫는지 확인한다.

운영자 장전 override 보강 메모: `[OperatorPreopenConditionalOneTickReal0609]` 판정은 `applied_real_only_conditional_override`. 2026-06-09 08:40 KST 사용자 지시로 실제 SCALPING 제출가 경로에 한정해 `spread_tick=1`이고 매수 체결/OFI 또는 bid depth가 강한 경우만 1틱 제출가를 허용하는 예외를 추가했다. 기본 runtime override는 `KORSTOCKSCAN_SCALPING_NORMAL_DEFENSIVE_TICKS=3`을 유지한다. 예외가 적용되면 `entry_price_guard=conditional_1tick_real_micro_override`, `entry_price_defensive_ticks=1`, `conditional_1tick_real_override_applied=true`와 context를 남긴다. SCALPING 외 전략, latency DANGER override, 조건 미충족 표본은 기존 3틱 보수 제출을 유지한다. 이 변경은 operator real override이며 sim/threshold-cycle 자동 튜닝 진행 또는 live-auto promotion 근거가 아니다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RuntimeEnvIntradayObserve0609] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-06-09`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-08.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.
  - 처리 결과: `provenance_present_with_missing_score65_runtime_match`.
  - 판정: PREOPEN runtime env selected family는 장중 raw event에서 부분 확인됐고 rollback guard breach는 없다. `score65_74_recovery_probe`는 오늘 selected env family가 아니므로 장중 runtime provenance 필수 누락으로 보지 않는다.
  - 근거: `threshold_runtime_env_2026-06-09.json` selected families는 `soft_stop_whipsaw_confirmation`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `lifecycle_decision_matrix_runtime`, `scalp_sim_auto_approval`, `swing_sim_auto_approval`, `operator_preopen_entry_price_defensive_ticks`다. `pipeline_events_2026-06-09.jsonl` 재집계 기준 `soft_stop_whipsaw_confirmation=60`, `soft_stop_whipsaw_confirmation_expired=13`, `lifecycle_decision_matrix_runtime_policy=5`, `scalp_sim_buy_order_virtual_pending=190`, `scalp_sim_ai_holding_live_call=1171`, `swing_sim_buy_order_assumed_filled=3`가 확인됐다. `threshold_apply_2026-06-09.json`은 `apply_mode=auto_bounded_live`, `runtime_change=true`, `warnings=[]`이고 장중 env override는 수행하지 않았다.
  - 다음 액션: 오늘 장후 `ThresholdDailyEVReport0609`에서 selected family의 post-apply attribution과 natural-match 여부를 확인한다. 장중 결과로 threshold/env/provider/order/bot 변경은 하지 않는다.

- [x] `[SimProbeIntradayCoverage0609] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-06-09`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-08.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.
  - 처리 결과: `source_quality_split_warning`.
  - 판정: sim/probe 주문 관찰축은 real execution과 분리되어 있고 `actual_order_submitted=false` 권한은 유지된다. 다만 주문 단계가 아닌 `swing_sim_holding_started` 3건은 `broker_order_forbidden` 필드가 비어 있어 postclose source-quality 관찰 대상으로 남긴다.
  - 근거: `pipeline_events_2026-06-09.jsonl` 재집계 기준 `scalp_sim_buy_order_virtual_pending=190`, `scalp_sim_buy_order_assumed_filled=190`, `scalp_sim_holding_started=190`, `scalp_sim_sell_order_assumed_filled=173`, `swing_sim_buy_order_assumed_filled=3`, `swing_probe_entry_candidate=11`, `swing_probe_holding_started=11`, `swing_probe_discarded=1537`, `swing_probe_state_restored=34`다. sim order stage의 authority violation은 0건이고, `swing_sim_holding_started` 3건은 `actual_order_submitted=false`이나 holding 시작 stage라 broker submit 증거로 사용하지 않는다. `observation_source_quality_audit_2026-06-09.json`은 `status=pass`, `hard_blocking_contract_gap_count=0`, `unknown_token_stage_count=0`이다.
  - 다음 액션: 장후 `PostcloseSourceQualityGateReview0609`에서 `swing_sim_holding_started` broker provenance가 report contract warning으로 승격되는지 확인한다. sim/probe EV는 broker execution 품질이나 실주문 전환 근거로 쓰지 않는다.

- [x] `[IntradaySourceQualityGateCheck0609] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-06-09`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-06-09.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-09.jsonl), [threshold_events_2026-06-09.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-06-09.jsonl), [observation_source_quality_audit_2026-06-09.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-09.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-06-09 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.
  - 처리 결과: `source_quality_clean_intraday`.
  - 판정: 장중 raw source-quality는 pass이며 hard block, row exclusion, unknown-token workorder handoff 대상이 없다.
  - 근거: `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-06-09 --write`를 실행해 `observation_source_quality_audit_2026-06-09.json`을 `generated_at=2026-06-09T10:56:59+09:00`로 갱신했다. 요약은 `event_count=63894`, `stage_count=107`, `hard_blocking_contract_gap_count=0`, `hard_blocking_excluded_row_count=0`, `tuning_input_allowed=true`, `raw_row_exclusion_applied=false`, `unknown_token_stage_count=0`, `review_warning_count=0`, `reviewed_unknown_token_stage_count=6`이다. raw 파일은 `pipeline_events_2026-06-09.jsonl` 63,894건 이상, `threshold_events_2026-06-09.jsonl` 36,627건 이상으로 append가 유지됐다.
  - 다음 액션: 장후 `PostcloseSourceQualityGateReview0609`에서 postclose EV/report 소비 후에도 hard block과 unknown warning이 없는지 재확인한다. 장중 감사 결과로 runtime threshold/order/provider/cap/bot 변경은 하지 않는다.

운영 확인 메모: `[IntradayAutomationHealthCheck20260609]` 판정은 `pass`. `buy_funnel_sentinel`, `holding_exit_sentinel`, `panic_sell_defense`, `panic_buying` cron log는 모두 2026-06-09 10:55~10:57 KST `[DONE]` marker를 남겼고 각 JSON/Markdown artifact가 생성됐다. `error_detection_2026-06-09.json`은 `summary_severity=pass`, detector 7개 모두 pass이며 process/thread, cron, error log, Kiwoom auth, critical artifact, resource, lock 상태가 정상이다. `pipeline_events_2026-06-09.jsonl`와 `threshold_events_2026-06-09.jsonl`은 10:58 KST까지 append가 유지됐다. 장중 runbook 확인은 운영 상태 점검이며 threshold/env/provider/order/bot 변경 권한이 없다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[PostcloseSourceQualityGateReview0609] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-06-09`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-06-09.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-09.json), [threshold_cycle_ev_2026-06-09.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-09.json), [code_improvement_workorder_2026-06-09.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-09.json), [threshold_cycle_postclose_verification_2026-06-09.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-09.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0609] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-06-09`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-08.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[CodeImprovementWorkorderReview0609] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-06-09`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-06-08.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-08.md), [code_improvement_workorder_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-08.json)
  - 판정 기준: selected_order_count=107와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0609] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-06-09`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-08.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[LifecycleQuietGapReview0609] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-06-09`, `Slot: POSTCLOSE`, `TimeWindow: 17:30~17:45`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-08.json), [runtime_apply_gap_audit_2026-06-08.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-08.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`255`, rollup_required_count=`255`, sim_live_connected_quiet_gap_count=`4`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'absorbed_into_parent_policy': 15, 'ai_review_parsed_low_coverage': 1, 'exclusion_dimension_candidate': 16, 'parent_conflict_child': 47, 'positive_source_only_keep_collecting': 239}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0609] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-06-09`, `Slot: POSTCLOSE`, `TimeWindow: 18:10~18:25`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-06-08.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`15`, run_count=`13`, skip_count=`2`, source_missing_count=`0`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`scalp_sim_ai_deferred_review, codebase_performance_workorder`, top_reasons=`upstream_drift_signal:13, fresh_outputs_no_trigger:2, upstream_artifact_newer:2, output_missing_or_unreadable:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->





## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
