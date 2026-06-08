# 2026-06-08 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-06-05` postclose -> `2026-06-08`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[SwingPreFinalAutoAndFinalApprovalPreopen0608] 스윙 pre-final auto state 및 final approval artifact 확인` (`Due: 2026-06-08`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-06-05.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-06-05.json), [threshold_cycle_ev_2026-06-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-05.json)
  - 판정 기준: pre-final은 parsed AI Tier2 auto state가 있어야 하고, final-stage는 사용자 승인 artifact가 있어야 한다.
  - 금지: 스윙 full-live 전환, cap release, provider/bot 변경, hard-safety 완화를 pre-final auto state로 처리하지 않는다.
  - 다음 액션: `pre_final_auto_selected`, `final_approval_artifact_present`, `blocked_by_policy` 중 하나로 닫는다.
  - 처리 결과: `blocked_by_policy`.
  - 판정: 스윙 pre-final/final runtime 반영 대상 없음. full-live 전환, cap release, provider/bot 변경, hard-safety 완화는 열지 않는다.
  - 근거: `swing_runtime_approval_2026-06-05.json` summary가 `requested=0`, `approved=0`, `blocked=12`, `runtime_change=false`이고, `threshold_apply_2026-06-08.json`의 `swing_runtime_approval`도 `approval_artifact=null`, `requested=0`, `approved=0`, `selected=[]`, `dry_run_forced=false`다.
  - 다음 액션: 별도 사용자 승인 artifact가 생기기 전까지 final-stage는 차단 유지. 오늘은 `swing_sim_auto_approval` sim policy env만 관찰 대상으로 둔다.

- [x] `[ThresholdEnvAutoApplyPreopen0608] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-06-08`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-05.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 처리 결과: `partial_apply_with_blocked_families`.
  - 판정: preopen wrapper와 runtime env 생성은 pass지만, bridge live-auto 후보는 계약/품질 차단으로 수동 우회하지 않는다.
  - 근거: `threshold_cycle_preopen_2026-06-08.status.json`은 `status=succeeded`, `exit_code=0`, `finished_at=2026-06-08T07:35:01+09:00`이고, `threshold_apply_2026-06-08.json`은 `status=auto_bounded_live_ready`, `apply_mode=auto_bounded_live`, `runtime_change=true`, `warnings=[]`다. `threshold_runtime_env_2026-06-08.json` selected families는 `soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `lifecycle_decision_matrix_runtime`, `scalp_sim_auto_approval`, `swing_sim_auto_approval`다. `runtime_apply_bridge`는 `entry_wait6579_score66_69_recovery_gate_v1`이 `blocked_source_quality`/`auto_live_contract_missing`, `scale_in_bucket_runtime_policy_v1`이 `bootstrap_pending`/`auto_live_contract_missing`으로 selected 없음.
  - 다음 액션: 생성된 `threshold_runtime_env_2026-06-08.env`만 runtime source로 인정한다. bridge blocked family, approval artifact missing, same-stage owner conflict는 postclose source-quality/contract workorder로만 넘기고 장중 env override 금지.

운영 확인 메모: `[PreopenAutomationHealthCheck20260608]` 판정은 `pass_with_note`. `threshold_cycle_preopen_cron.log`에는 2026-06-08 `[DONE]` marker가 있고 status artifact도 succeeded다. `ensemble_scanner.log`에는 `final_ensemble_scanner target_date=2026-06-08` `[DONE]` marker가 있으며, `final_ensemble_scanner`는 `data/daily_recommendations_v2.csv` 생성자가 아니라 기존 CSV consumer다. `data/daily_recommendations_v2.csv`와 diagnostics는 2026-06-05 21:00 `update_kospi` chain의 `recommend_daily_v2`가 생성한 전 거래일 postclose 산출물이며, 월요일 2026-06-08 장전 기준으로 latest quote date 2026-06-05를 쓰는 것은 정상이다. 봇은 2026-06-08 07:40 이후 기동되어 env 생성 07:35보다 늦다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RuntimeEnvIntradayObserve0608] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-06-08`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-08.json), [runtime_apply_bridge_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-06-08.json), [threshold_apply_2026-06-08.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-08.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.
  - 처리 결과: `provenance_present`.
  - 판정: 장중 runtime event append와 selected family provenance가 확인됐고 rollback guard breach는 없다. 장중 threshold/env mutation은 수행하지 않는다.
  - 근거: `pipeline_events_2026-06-08.jsonl`은 09:42 KST 기준 30,629 events, 108 stages, first=`2026-06-08T07:40:21.384844`, last=`2026-06-08T09:42:38.592571`로 append 중이다. `soft_stop_whipsaw_confirmation` mention/event는 13건이며, `error_detection full`은 `summary_severity=pass`, process/thread/resource/artifact freshness 모두 pass다.
  - 다음 액션: 장후 `threshold_cycle_ev_2026-06-08`와 post-apply attribution에서 selected family의 실제 효과를 확인한다. 장중 결과로 runtime threshold mutation은 금지 유지.

- [x] `[SimProbeIntradayCoverage0608] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-06-08`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-06-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-05.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.
  - 처리 결과: `source_quality_split_observed`.
  - 판정: sim/probe event는 실주문과 분리되어 관측 중이며 real execution 품질이나 실주문 전환 근거로 쓰지 않는다.
  - 근거: `actual_order_submitted` 필드는 9,220건 모두 `False`이며, `broker_order_forbidden=True` 7,337건/`False` 1,862건으로 provenance가 분리된다. 주요 sim/probe event는 `scalp_sim_panic_scale_in_blocked=733`, `scalp_sim_duplicate_buy_signal=575`, `scalp_sim_ai_holding_live_call=298`, `scalp_sim_buy_order_assumed_filled=96`, `swing_probe_discarded=259`, `swing_probe_state_restored=12`, `swing_probe_entry_candidate=10`, `swing_probe_holding_started=10`이다.
  - 다음 액션: 장후 `key_lineage_ledger_2026-06-08`와 `conversion_lane_2026-06-08`에서 active priority same-key observation과 sim/probe source-quality split을 최종 확인한다.

- [x] `[IntradaySourceQualityGateCheck0608] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-06-08`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-06-08.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-08.jsonl), [threshold_events_2026-06-08.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-06-08.jsonl), [observation_source_quality_audit_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-08.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-06-08 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.
  - 처리 결과: `defective_rows_excluded`.
  - 판정: 장중 source-quality audit은 `warning`이나 hard block은 없다. 결손 row/window는 raw-row exclusion으로 제외됐고 tuning input은 허용된다.
  - 근거: `observation_source_quality_audit --target-date 2026-06-08 --write` 실행 결과 `status=warning`, `event_count=30449`, `stage_count=107`, `hard_blocking_contract_gap_count=0`, `hard_blocking_excluded_row_count=0`, `tuning_input_allowed=true`, `raw_row_exclusion_applied=true`, `unknown_token_stage_count=3`, `review_warning_count=3`이다. raw-row exclusion manifest는 `data/source_quality/raw_row_exclusion/2026-06-08_20260608T094156148660+0900/manifest.json`이며 500 rows of `blocked_strength_momentum` zero `intraday_range_pct` rows가 제외됐다.
  - 보강: 09:03:42 서킷브레이커, 20분 매매정지, 10분 단일가 접수 구간과 500 rows 집중 시간이 겹친다. 09:35 이후 대량 zero context는 정상 유입으로 회복됐고, 09:59 `아진엑스텍(059120)` 단일 종목 6건은 신규 관측 `insufficient_history`로 분리한다. 확정 window는 tracked `data/source_quality/market_halt_windows/windows/2026-06-08.json` artifact로 기록하고, WebSocket `0s` 장운영구분은 ignored `data/source_quality/market_halt_windows/session_events/` raw session event로 중복 skip 저장한다. source-quality audit/workorder/verifier에는 artifact 기반 `market_halt_or_circuit_window_overlap` review-only provenance를 추가해 producer-fix implement_now로 과잉 라우팅하지 않도록 보강했다.
  - 다음 액션: 장후 `PostcloseSourceQualityGateReview0608`에서 warning stages `scale_in_qty_block`, `swing_scale_in_micro_context_observed`, `swing_probe_sell_order_assumed_filled`와 exclusion manifest가 EV/report 소비에서 유지되는지 확인한다.

- [x] `[IntradayAutomationHealthCheck20260608] 장중 자동화체인 상태 확인` (`Due: 2026-06-08`, `Slot: INTRADAY`, `TimeWindow: 09:05~15:30`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: Runbook 장중 확인 절차의 sentinel/log/event append/panic/error detection 상태를 확인하고 `pass`, `warning`, `fail`, `not_yet_due` 중 하나로 닫는다.
  - 금지: sentinel/panic/source-quality 관찰 결과를 장중 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 처리 결과: `pass`.
  - 판정: 장중 자동화체인은 정상 동작 중이다. 일부 sentinel은 위험/드라우트 상태를 보고하지만 report-only/관찰 지표이며 장중 runtime 변경 근거가 아니다.
  - 근거: buy funnel sentinel은 09:40 DONE 및 `SUBMIT_DROUGHT_CRITICAL`, holding/exit sentinel은 09:40 DONE 및 `HOLD_DEFER_DANGER`, panic sell defense는 `RECOVERY_WATCH`/`report_only_no_mutation`, panic buying은 `NORMAL`/`report_only_no_mutation`이다. `pipeline_events`와 `threshold_events`는 09:42 기준 fresh이며, `error_detection full`은 cron/process/artifact/resource/stale-lock 모두 `pass`다.
  - 다음 액션: 장후 postclose 산출물에서 sentinel warning과 source-quality warning이 code-improvement/workorder handoff 또는 report-only 관찰로 올바르게 분리됐는지 확인한다.

## 장후 체크리스트 (16:30~18:55)

- [x] `[PostcloseSourceQualityGateReview0608] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-06-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-08.json), [threshold_cycle_ev_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-08.json), [code_improvement_workorder_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-08.json), [threshold_cycle_postclose_verification_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-08.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.
  - 처리 결과: `source_quality_gate_pass`.
  - 판정: 장후 source-quality gate는 pass이며 2026-06-08 튜닝 입력은 허용된다.
  - 근거: `observation_source_quality_audit_2026-06-08.json`은 `status=pass`, `tuning_input_allowed=true`, `hard_blocking_contract_gap_count=0`, `hard_blocking_excluded_row_count=0`, `unknown_token_stage_count=0`, `review_warning_count=0`이다. `threshold_cycle_ev_2026-06-08.json`의 `source_quality_preflight_gate`도 `status=pass`, `clean_baseline_enforced=true`, `allowed_runtime_apply=true`로 동일하다. `threshold_cycle_postclose_verification_2026-06-08.json`의 `source_quality_hard_block.status=pass`, `raw_row_exclusion_handoff.status=pass`로 downstream handoff도 닫혔다.
  - 다음 액션: source-quality hard block은 없음. verifier의 warning은 conversion KPI warning으로 별도 항목에서 처리하고, 결손 row/window 제외나 source-quality blocked 전환은 열지 않는다.

- [x] `[ThresholdDailyEVReport0608] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-06-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-05.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.
  - 처리 결과: `sim_auto_observe_and_live_auto_blocked`.
  - 판정: daily EV는 source-quality pass 상태로 생성됐지만, 2026-06-08 postclose 기준 live-auto 반영 대상은 없다. sim/combined EV는 다음 PREOPEN sim 관찰과 후보 유지 입력으로만 사용한다.
  - 근거: `threshold_cycle_ev_2026-06-08.json`은 `source_quality_preflight_gate.status=pass`이고, runtime apply는 당일 PREOPEN 산출물 `threshold_apply_2026-06-08.json` 기준 `auto_bounded_live_ready`였다. `runtime_apply_bridge`는 `candidate_count=2`, `approved=0`, `selected_count=0`이며 `entry_wait6579_score66_69_recovery_gate_v1`은 `blocked_source_quality/auto_live_contract_missing`, `scale_in_bucket_runtime_policy_v1`은 `bootstrap_pending/auto_live_contract_missing`으로 차단됐다. `runtime_apply_bridge_2026-06-08.json`도 `live_auto_apply_ready_count=0`, `greenfield_real_env_ready_count=0`, `human_approval_required=false`다.
  - 다음 액션: 다음 장전 apply는 postclose 산출물의 sim-auto/observe-only 후보와 sample-floor 상태를 확인한다. broker execution 품질, full-live 전환, cap/provider/bot/threshold 변경은 열지 않는다.

- [x] `[HoldingFlowDeferCostConclusion0608] HOLD_DEFER_DANGER 반복 신호의 자동화체인 판정 및 장후 결론 확인` (`Due: 2026-06-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~16:55`, `Track: ScalpingLogic`)
  - Source: [holding_exit_sentinel_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/holding_exit_sentinel/holding_exit_sentinel_2026-06-08.json), [threshold_cycle_ev_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-08.json), [threshold_cycle_ai_review_2026-06-08_postclose.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_2026-06-08_postclose.json), [threshold_apply_2026-06-09.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-09.json)
  - 판정 기준: `holding_exit_sentinel.primary=HOLD_DEFER_DANGER`가 `holding_flow_defer_cost_review`로 라우팅됐는지 확인하고, `threshold_cycle_ev`의 `holding_flow_ofi_smoothing` source metrics(`holding_flow_override_defer_exit`, `holding_flow_override_force_exit`, `holding_flow_override_exit_confirmed`, `max_defer_worsen_pct`, `source_sample_count/sample_floor`)와 calibration/apply 결과(`adjust_down|hold|hold_sample|freeze`, `runtime_change`, `selected`)를 대조해 최종 결론을 기록한다.
  - 금지: sentinel 경고만으로 장중 자동매도, holding threshold mutation, provider/order/bot/cap 변경을 하지 않는다. 반대로 반복 `HOLD_DEFER_DANGER`를 단순 관찰로만 방치하지 않고, 자동화체인에서 `hold`로 닫힌 경우 반드시 guard reason과 부족한 evidence를 남긴다.
  - 다음 액션: `adjust_down_selected_for_next_preopen`, `hold_with_cost_effect_not_confirmed`, `hold_sample_or_freeze_evidence_gap`, `workorder_required_for_defer_cost_attribution_gap`, `postclose_artifact_missing`, `forbidden_runtime_change_detected` 중 하나로 닫는다.
  - 처리 결과: `hold_with_cost_effect_not_confirmed`.
  - 판정: `HOLD_DEFER_DANGER`는 자동화체인에 반영됐지만, 다음 PREOPEN holding threshold/자동매도 조정으로 선택되지 않았다.
  - 근거: `holding_exit_sentinel_2026-06-08.json`은 `classification.primary=HOLD_DEFER_DANGER`, `live_runtime_effect=false`, forbidden automation에 `auto_sell`, `holding_threshold_relaxation`, `holding_flow_override_mutation`, `bot_restart`가 명시돼 있다. `threshold_cycle_ev_2026-06-08.json`의 `holding_flow_ofi_smoothing` source metrics는 `holding_flow_override_defer_exit=1459`, `force_exit=217`, `exit_confirmed=24`, `holding_flow_ofi_smoothing_applied=689`, `max_defer_worsen_pct=0.8`, `sample_floor_status=ready`로 집계됐다. postclose apply plan `threshold_apply_2026-06-09.json`은 아직 생성되지 않아 다음 PREOPEN 반영 확정 근거는 없다.
  - 다음 액션: 다음 PREOPEN apply 산출물이 생성되면 holding flow selected 여부만 재확인한다. sentinel 경고만으로 실시간 자동매도, provider/order/bot/cap, 장중 threshold mutation은 하지 않는다.

- [x] `[EntryPriceDynamicDecisionConclusion0608] 매수가격 동적결정 1틱 고정 수렴 여부 및 체결/EV 영향 확인` (`Due: 2026-06-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:55~17:05`, `Track: ScalpingLogic`)
  - Source: [threshold_events_2026-06-08.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-06-08.jsonl), [pipeline_events_2026-06-08.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-08.jsonl), [threshold_cycle_ev_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-08.json), [threshold_cycle_ai_review_2026-06-08_postclose.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_2026-06-08_postclose.json), [threshold_apply_2026-06-09.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-09.json)
  - 판정 기준: real `order_bundle_submitted`/`order_leg_request`와 related `scalp_entry_action_decision_snapshot`에서 `entry_price_resolver_enabled`, `ai_entry_price_canary_applied`, `ai_entry_price_canary_action`, `entry_price_defensive_ticks`, `price_resolution_reason`, `resolution_reason`, `best_bid_at_submit`, `best_ask_at_submit`, `submitted_order_price`, `counterfactual_order_price_1tick`, `orderbook_micro_state`, spread/quote/stale context를 집계한다. `entry_price_defensive_ticks=1` 또는 `USE_DEFENSIVE`가 시장상황과 무관하게 대부분을 차지하면 `pre_submit_price_guard`/`dynamic_entry_price_resolver_p1`의 cost/effect 결론을 장후 EV와 대조한다.
  - 금지: 체감상 1틱 고정이라는 이유만으로 장중 주문가, slippage, provider, bot, cap, broker/order guard를 변경하지 않는다. 반대로 `normal_defensive` 1틱 수렴이 반복되면 단순 방어적 가격으로 해석하지 말고, 무지성 1틱 고정 가능성, 미체결/늦은체결/추격실패/불리체결 회피 효과를 분리해 결론을 남긴다.
  - 다음 액션: `dynamic_price_decision_validated`, `one_tick_fixed_convergence_needs_workorder`, `deeper_price_policy_candidate_for_next_preopen`, `hold_with_fill_ev_not_worse`, `postclose_artifact_missing`, `forbidden_runtime_change_detected` 중 하나로 닫는다.
  - 처리 결과: `hold_with_fill_ev_not_worse`.
  - 판정: entry price 동적결정은 instrumentation이 구현돼 있고 reason breakdown은 준비됐지만, 2026-06-08 postclose EV에서는 가격 정책 변경이나 1틱 고정 해소 workorder를 바로 열 근거가 부족하다.
  - 근거: `threshold_cycle_ev_2026-06-08.json`의 `pre_submit_price_guard` calibration은 `sample_floor_status=hold_sample`, `instrumentation_status=implemented`, `coverage_status=reason_breakdown_ready`다. 같은 EV report에는 `scalp_simulator.entry_ai_price_skip_order=0`, `entry_submit_revalidation_warning=282`가 남아 가격/submit 재검증 관찰은 있으나, 다음 PREOPEN `threshold_apply_2026-06-09.json`은 아직 생성되지 않았다.
  - 다음 액션: 다음 PREOPEN apply와 real submit/fill attribution이 생성된 뒤 `dynamic_price_decision_validated` 또는 `one_tick_fixed_convergence_needs_workorder`로 재판정한다. 장중 주문가, slippage, provider, bot, cap, broker/order guard는 변경하지 않는다.

- [x] `[CodeImprovementWorkorderReview0608] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-06-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-06-08.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-08.md), [code_improvement_workorder_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-08.json), [scalp_entry_action_decision_matrix_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-06-08.json), [scalp_entry_action_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/scalp_entry_action_decision_matrix.py), [build_code_improvement_workorder.py](/home/ubuntu/KORStockScan/src/engine/build_code_improvement_workorder.py)
  - 판정 기준: 2026-06-08 code improvement workorder의 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다. `scalp_entry_action_decision_matrix.summary.warnings`에 `unknown_bucket_source_quality_gap`가 있고 `unknown_bucket_summary.recommended_route=source_quality_workorder`이면, workorder가 해당 gap을 source-quality/instrumentation order로 생성했는지 반드시 대조한다. 누락 시 `handoff_missing_fix_automation_first`로 닫고 `build_code_improvement_workorder` routing 보강을 우선한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now_ready`, `design_or_attach_deferred`, `reject`, `already_implemented`, `handoff_missing_fix_automation_first`, `postclose_artifact_missing` 중 하나로 닫는다.
  - 처리 결과: `already_implemented`.
  - 판정: 2026-06-08 code-improvement workorder는 새 Codex 구현 지시 대상이 아니라 기존 구현/기존 family handoff 확인 대상으로 닫는다.
  - 근거: `code_improvement_workorder_2026-06-08.json` summary는 `selected_order_count=106`, `selected_decision_counts={'attach_existing_family': 105, 'defer_evidence': 1}`, `selected_implement_now_route_count=0`, `selected_runtime_effect_false_count=106`, `repeat_unresolved_escalation_count=0`이다. `unknown_bucket_source_quality_gap` 관련 order는 6건 모두 `attach_existing_family`, `implementation_status=implemented`, `runtime_effect=false`, `allowed_runtime_apply=false`로 포함돼 handoff 누락은 없다. Markdown snapshot lineage도 `new_order_ids=[]`, `removed_order_ids=[]`, `decision_changed_order_ids=[]`다.
  - 다음 액션: 사용자가 별도로 Codex 구현을 지시하지 않는 한 repo 수정은 열지 않는다. 남은 1건 `defer_evidence`는 다음 postclose evidence 누적으로 재검토한다.

- [x] `[HumanInterventionSummary0608] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-06-08`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [runtime_apply_bridge_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-06-08.json), [conversion_lane_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/conversion_lane/conversion_lane_2026-06-08.json), [runtime_approval_summary_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-06-08.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.
  - 처리 결과: `observe_only`.
  - 판정: 2026-06-08 postclose 기준 사용자 승인 artifact가 필요한 runtime 변경 요청은 생성되지 않았다. 필요한 사용자 액션은 Project/Calendar 수동 동기화와 다음 PREOPEN 산출물 확인이다.
  - 근거: `runtime_apply_bridge_2026-06-08.json`은 `ready_for_approval_count=0`, `approval_required_count=0`, `human_approval_required=false`, `runtime_mutation_performed=false`다. `conversion_lane_2026-06-08.json`은 `real_conversion_queue_count=0`, `bounded_real_canary_requestable_count=0`이며, `runtime_approval_summary_2026-06-08.json`은 `panic_approval_requested=0`, swing blocked는 12건으로 final approval 없음이다. `code_improvement_workorder_2026-06-08.json`도 `selected_implement_now_route_count=0`이다.
  - 다음 액션: 표준 Project/Calendar 동기화 명령은 사용자가 실행한다. 다음 PREOPEN `threshold_apply_2026-06-09` 생성 후 approval/runtime/env 반영 여부만 확인한다.

- [x] `[LifecycleQuietGapReview0608] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-06-08`, `Slot: POSTCLOSE`, `TimeWindow: 17:30~17:45`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-08.json), [runtime_apply_gap_audit_2026-06-08.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-08.md), [threshold_cycle_postclose_verification_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-08.json)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`199`, rollup_required_count=`199`, sim_live_connected_quiet_gap_count=`7`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'exclusion_dimension_candidate': 7, 'parent_conflict_child': 25, 'positive_source_only_keep_collecting': 191}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.
  - 처리 결과: `rollup_only`.
  - 판정: lifecycle quiet gap은 자동 rollup으로 표면화됐고, 즉시 구현이나 runtime 변경 없이 source-only 수집/parent policy 검토로 닫는다.
  - 근거: `runtime_apply_gap_audit_2026-06-08.json`은 `status=pass`, `quiet_gap_count=255`, `quiet_gap_rollup_count=255`, `quiet_gap_codex_directive_count=0`, `critical_failure_count=0`, `retry_queue_count=0`, `ai_review_status=parsed`다. category는 `source_quality_blocker=496`, `sim_auto_approved=82`, `runtime_blocked_contract_gap=24`, `source_only_keep_collecting=20`, `code_patch_required=5`로 분리됐다. `threshold_cycle_postclose_verification_2026-06-08.json`도 `runtime_apply_gap_audit.status=pass`다.
  - 다음 액션: quiet gap은 threshold/env/provider/order/bot 변경 근거로 쓰지 않는다. sample-floor와 source-quality blocker는 다음 rolling/MTD window와 code-improvement workorder handoff에서 재확인한다.

- [x] `[ActiveSimPrioritySameKeyObservation0608] active sim priority same-key runtime observation 최종 확인` (`Due: 2026-06-08`, `Slot: POSTCLOSE`, `TimeWindow: 17:45~18:00`, `Track: ScalpingLogic`)
  - Source: [key_lineage_ledger_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/key_lineage_ledger/key_lineage_ledger_2026-06-08.json), [conversion_lane_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/conversion_lane/conversion_lane_2026-06-08.json), [tuning_performance_control_tower_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-06-08.json), [threshold_cycle_postclose_verification_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-08.json)
  - 판정 기준: PREOPEN catalog/apply에 들어간 active priority key가 장중 runtime/sim event와 postclose `key_lineage_ledger`에서 같은 key로 닫히는지 확인한다. 중간점검에서 관측된 `sim_record_id` present but `source_stage/source_record_id` missing, `lifecycle_bucket_match_status=no_match`, `scalp_sim_auto_policy_active_seed_count=0` 패턴이 postclose lineage reconstruction에서 정상 bridge됐는지 별도 확인한다. `same_key_continuity_pass`, `positive_ev_runtime_observed`, `natural_match_0`, `catalog_missing`, `preopen_missing`, `not_instrumented`를 분리 기록한다.
  - 금지: natural match 0을 전략 실패로 단정하지 않는다. catalog/PREOPEN handoff가 intact면 warning으로 닫고, key/schema/contract mismatch, unknown key, inactive key consumption, forbidden authority leak만 fail로 닫는다. sim-only priority를 실주문, threshold, provider, bot, cap 변경 근거로 사용하지 않는다.
  - 다음 액션: `same_key_runtime_observed`, `natural_match_0_warning`, `catalog_or_preopen_missing`, `runtime_observation_not_instrumented`, `key_contract_mismatch_fail`, `postclose_artifact_missing` 중 하나로 닫는다.
  - 처리 결과: `same_key_runtime_observed`.
  - 판정: active sim priority는 same-key runtime observation이 일부 확인됐고, key/schema/contract mismatch fail은 없다. 다만 next-PREOPEN 대상 후보는 `preopen_missing` warning으로 분리한다.
  - 근거: `key_lineage_ledger_2026-06-08.json`은 `same_key_continuity_pass_count=9`, `bucket_same_key_continuity_pass_count=4`, `positive_ev_runtime_observed_count=4`, `key_mismatch_count=0`, `catalog_missing_count=0`, `not_instrumented_count=0`, `natural_match_0_count=181`, `preopen_missing_count=23`이다. 1.3GB 이벤트 파일은 streaming IO guard로 `lines_read=303744`, `oversized_line_skipped_count=0`, truncation 0으로 재생성됐다. 중간점검 패턴은 `active_sim_policy_zero_count_event_count=10829`, `positive_count=9249`, `panic_scale_in_no_match_event_count=5506`, `no_match_unique_sim_record_count=121`, `source_stage_counts={'first_ai_wait': 2343, 'blocked_ai_score': 898, 'scale_in': 2265}`로 postclose lineage에 반영됐다.
  - 다음 액션: next-PREOPEN 정책 미도래 후보 23건은 다음 apply에서 확인한다. natural match 0은 전략 실패가 아니라 관찰 warning으로 유지하고, sim-only priority를 실주문/threshold/provider/bot/cap 변경 근거로 쓰지 않는다.

- [x] `[AutomationTriggerDecisionSummary0608] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-06-08`, `Slot: POSTCLOSE`, `TimeWindow: 18:10~18:25`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-06-08.json), [threshold_cycle_postclose_verification_2026-06-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-08.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`15`, run_count=`13`, skip_count=`2`, source_missing_count=`0`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`scalp_sim_ai_deferred_review, codebase_performance_workorder`, top_reasons=`upstream_drift_signal:13, fresh_outputs_no_trigger:2, output_missing_or_unreadable:2, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.
  - 처리 결과: `trigger_contract_pass`.
  - 판정: 자동화체인 trigger decision은 run/skip 계약대로 동작했고 source missing 또는 force override는 없다.
  - 근거: `automation_chain_trigger_decision_2026-06-08.json` summary는 `total_steps=15`, `run_count=13`, `skip_count=2`, `source_missing_count=0`, `force_override_count=0`이다. skip step은 `scalp_sim_ai_deferred_review`, `codebase_performance_workorder`이고 둘 다 `fresh_outputs_no_trigger` 사유와 기존 output available 상태다. `threshold_cycle_postclose_verification_2026-06-08.json`은 latest `[START]`와 `[DONE]` marker를 모두 보유하고, DONE은 `recovery_action=tail_repair_done_reconciliation`, `full_wrapper_rerun=false`로 닫혔다.
  - 다음 액션: trigger decision은 runtime/apply/broker/provider/cap/bot/threshold 경계 변경 근거로 쓰지 않는다. 다음 postclose에서도 source missing 또는 force override가 생기면 별도 patch 대상으로 분리한다.

- [x] `[PostcloseAutomationHealthCheck20260608] 장후 자동화체인 상태 확인` (`Due: 2026-06-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~20:45`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: Runbook 장후 확인 절차의 postclose wrapper, DONE controller, final verifier, conversion KPI, source-quality, workorder/disposition 상태를 확인하고 `pass`, `warning`, `fail`, `not_yet_due` 중 하나로 닫는다.
  - 처리 결과: `warning`.
  - 판정: 장후 자동화체인은 완료됐으나 conversion KPI warning이 남아 `Tuning Chain Control State=YELLOW`로 닫는다.
  - 근거: `postclose_done_controller_2026-06-08.json`은 `status=done`, `allowed_runtime_apply=false`이고, `threshold_cycle_postclose_verification_2026-06-08.json`은 `[START]`/`[DONE]` marker를 모두 확인했으나 `status=warning`이다. `source_quality_hard_block.status=pass`, `runtime_apply_gap_audit.status=pass`, `entry/submit/holding/exit/scale_in/overnight/lifecycle_flow handoff`는 pass지만 `conversion_kpi.status=warning`, `active_sim_priority_handoff.status=warning`, `key_lineage_blocker_count=23`이 남았다. `blocked_stage=runtime_uptake`, `impact=sim-only active priority 일부 next-PREOPEN 미도래/preopen_missing; real order/provider/bot/cap/threshold 영향 없음`.
  - 다음 액션: 다음 PREOPEN apply에서 `preopen_missing_count=23` 후보의 catalog/apply 반영 여부와 `natural_match_0` 관찰을 재확인한다. Project/Calendar 동기화는 표준 수동 명령으로 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-06-08 15:48:57`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-06-08.md`
- `Trade Review`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
