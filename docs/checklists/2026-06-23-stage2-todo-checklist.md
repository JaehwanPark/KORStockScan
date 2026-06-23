# 2026-06-23 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-06-22` postclose -> `2026-06-23`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0623] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-06-23`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-22.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 판정: `applied_guard_passed_env`
  - 근거: `threshold_cycle_preopen_2026-06-23.status.json`이 `status=succeeded`, `apply_plan_exists=true`, `runtime_env_exists=true`, `runtime_env_manifest_exists=true`로 닫혔다. `threshold_apply_2026-06-23.json`은 `source_date=2026-06-22`, `runtime_change=true`, `runtime_env_handoff_verification.status=pass`, `missing_family_count=0`이며 selected family 21개(`soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe`, `lifecycle_decision_matrix_runtime`, `scalp_sim_auto_approval`, `swing_sim_auto_approval`, `entry_cancel_wait_runtime` 포함)가 runtime env manifest에 반영됐다. `threshold_cycle_ev_2026-06-22.json`의 source-quality preflight는 `tuning_input_allowed=true`, `hard_blocking_contract_gap_count=0`, `review_warning_count=0`이다. 사용자 개입 요구는 `approval_requests=[]`, `swing_runtime_approval.requested=0`, `runtime_apply_bridge.selected=[]`로 없었고, bridge는 `scale_in_bucket_runtime_policy_v1` contract gap 때문에 정상 차단됐다.
  - 다음 액션: 장중 [RuntimeEnvIntradayObserve0623](/home/ubuntu/KORStockScan/docs/checklists/2026-06-23-stage2-todo-checklist.md:36)에서 selected family provenance와 rollback guard breach 여부만 재확인한다. blocked bridge family는 수동 env override 없이 장후 `HumanInterventionSummary0623`에서 `blocked_by_policy`로 재분류한다.

- [x] `[PreopenAutomationHealthCheck20260623] 장전 자동화체인 상태 확인` (`Due: 2026-06-23`, `Slot: PREOPEN`, `TimeWindow: 08:00~09:00`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md:299), [threshold_cycle_preopen_2026-06-23.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-06-23.status.json), [threshold_apply_2026-06-23.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-23.json), [threshold_runtime_env_2026-06-23.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-23.json), [threshold_runtime_env_verify_2026-06-23.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-06-23.json), [threshold_cycle_preopen_cron.log](/home/ubuntu/KORStockScan/logs/threshold_cycle_preopen_cron.log), [bot_history.log](/home/ubuntu/KORStockScan/logs/bot_history.log:1)
  - 판정: `warning`
  - 근거: `logs/threshold_cycle_preopen_cron.log`에 `[DONE] threshold-cycle preopen target_date=2026-06-23 finished_at=2026-06-23T07:35:02+0900` marker가 있고, status artifact도 `updated_at=2026-06-23T07:35:02+09:00`, `reason=completed`로 성공했다. runtime env manifest와 verify artifact는 `selected_families` 21개, `passed=true`, `findings=[]`다. `logs/bot_history.log`는 봇 기동 시각이 `2026-06-23 07:40:03`으로 env 생성 이후이며, `logs/kiwoom_sniper_v2_info.log`와 `logs/bot_history.log`에는 08:22~08:30 실시간 감시/heartbeat가 이어져 PREOPEN 이후 런타임이 실제 동작했다. 다만 `run_bot.sh`의 env source 자체를 직접 남긴 별도 `run_bot.log` 또는 `threshold_runtime_env_2026-06-23.env` source line은 현재 로그 인벤토리에서 확인되지 않았다.
  - 다음 액션: 같은 날짜 RunbookOps backlog는 다시 열지 않는다. 장중 [RuntimeEnvIntradayObserve0623](/home/ubuntu/KORStockScan/docs/checklists/2026-06-23-stage2-todo-checklist.md:42)에서 `/proc/<pid>/environ` 또는 runtime provenance로 env source를 보강 확인하고, 장후 `HumanInterventionSummary0623`에는 사용자 승인 필요 없음과 bridge 차단 사유만 남긴다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RuntimeEnvIntradayObserve0623] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-06-23`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-22.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, lifecycle_decision_matrix_runtime, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, weak_context_late_entry_guard_runtime가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.
  - 판정: `warning_provenance_partial_natural_match`
  - 근거: 현재 bot PID `241149`의 `/proc/241149/environ`에는 `KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE=2026-06-23`, `KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_ENABLED=true`, `KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_ENABLED=true`, `KORSTOCKSCAN_SCALP_SIM_AI_BUDGET_ENABLED=true`, `KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED=true`, `KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_ENABLED=true`가 로드돼 있어 당일 runtime env source handoff는 유지된다. `pipeline_events_2026-06-23.jsonl`에서는 family 문자열 또는 owner-stage 기준으로 `soft_stop_whipsaw_confirmation=36`, `score65_74_recovery_probe=464`, `scalping_scanner_real_source_guard_block=4498`, `score65_74_recovery_probe_blocked=402`, `scalp_sim_ai_holding_live_call=1051`, `real_weak_pullback_entry_block=3`, `early_accel_strong_bundle_recheck_corrected=5`, `scale_in_price_guard_block=14`, `pre_submit_liquidity_relief_evaluated/skipped/guard_block=18`, `swing_probe_entry_candidate/holding_started/exit_signal=각 12`가 확인됐다. 반면 `entry_price_gap_profile_runtime`, `profit_stagnation_exit_runtime`, `latency_spread_relief_real_operator_override`, `ai_watching_score_smoothing_report_only`, `weak_context_late_entry_guard_runtime`, `lifecycle_bucket_discovery_sim_auto_approval`은 15:27 KST 기준 자연 발생 provenance가 아직 없다. `pipeline_events` 전수 스캔에서 `safety_revert_required`, `rollback_guard_breach`, `severe_loss`, `provenance_breach` marker는 `0건`이다.
  - 다음 액션: 장후에는 미발생 family를 `runtime env 미적용`이 아니라 `natural_match_not_observed_yet`로 분리해 본다. 추가 장중 runtime mutation은 하지 않고, postclose `ThresholdDailyEVReport0623`와 `HumanInterventionSummary0623`에서 today natural match와 blocked-by-policy를 나눠 기록한다.

- [x] `[SimProbeIntradayCoverage0623] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-06-23`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-06-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-22.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.
  - 판정: `pass_sim_probe_split_intact`
  - 근거: `pipeline_events_2026-06-23.jsonl` 전수 집계에서 `fields.actual_order_submitted=False`는 `72,275건`, `True`는 `9건`이며, sim/probe 대표 stage는 `swing_probe_discarded=2410`, `scalp_sim_panic_scale_in_blocked=1755`, `swing_entry_micro_context_observed=1682`, `blocked_swing_score_vpw=1626`, `scalp_sim_ai_holding_live_call=1051`, `scalp_sim_buy_order_assumed_filled=207`, `scalp_sim_sell_order_assumed_filled=157`로 이어졌다. 샘플 event `swing_probe_entry_candidate`, `swing_probe_discarded`, `scalp_sim_buy_order_assumed_filled`는 모두 `simulated_order=True`, `actual_order_submitted=False`, `broker_order_forbidden=True`, `decision_authority=swing_sim_exploration_only|sim_observation_only`를 유지한다. `bot_history.log`의 15:25:43 heartbeat도 `scalp_sim: 2 / probe: 10 / 보유: 0`으로 source split과 active state를 별도로 보고한다.
  - 다음 액션: sim/probe 표본은 postclose EV/source-quality 입력으로만 넘기고 실주문 전환 근거로 쓰지 않는다. 장후에는 `PostcloseSourceQualityGateReview0623`에서 sim/probe row가 결손 없이 source-quality gate를 통과했는지만 확인한다.

- [x] `[IntradaySourceQualityGateCheck0623] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-06-23`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-06-23.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-23.jsonl), [threshold_events_2026-06-23.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-06-23.jsonl), [observation_source_quality_audit_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-23.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-06-23 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.
  - 판정: `unknown_warning_workorder_required`
  - 근거: 장중 재감사로 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-06-23 --write`를 실행했고, 생성된 [observation_source_quality_audit_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-23.json)은 `generated_at=2026-06-23T15:26:46+09:00`, `status=warning`, `event_count=101382`, `stage_count=155`, `hard_blocking_contract_gap_count=0`, `hard_blocking_excluded_row_count=0`, `tuning_input_allowed=true`, `raw_row_exclusion_applied=false`로 장중 튜닝 입력을 허용한다. 다만 `unknown_token_stage_count=2`, `review_warning_count=2`가 남았고 stage는 `scalp_entry_action_decision_snapshot`, `ai_confirmed`다. unknown token 예시는 `entry_adm_price_resolution_bucket=price_unknown`, `entry_adm_bucket_token=...|price_unknown|...` 1건씩으로 둘 다 `routing=source_quality_blocker_or_provenance_backfill`이다.
  - 다음 액션: 장후 `PostcloseSourceQualityGateReview0623`와 `CodeImprovementWorkorderReview0623`에서 같은 unknown-token finding이 EV/workorder handoff에 반영됐는지 재확인한다. 오늘 장중에는 hard block이 아니므로 runtime/order/provider/cap/bot 변경 없이 warning provenance만 유지한다.

Runbook 운영 확인 기록:

- `[IntradayAutomationHealthCheck20260623] 장중 자동화체인 상태 확인` 처리 결과 (2026-06-23 15:27 KST): 판정=`warning`, `Tuning Chain Control State=YELLOW`, blocked_stage=`input_health`, impact=`bot_main PID/env handoff, cron completion, artifact freshness, resource/lock, panic report-only 경계는 모두 정상이나 source-quality unknown-token warning 2건과 sentinel의 submit/holding 경보가 남아 장후 후속 확인이 필요`, next_action=`PostcloseSourceQualityGateReview0623`와 `CodeImprovementWorkorderReview0623`에서 unknown-token provenance backfill/workorder 반영 여부를 확인하고, `ThresholdDailyEVReport0623`에서는 submit drought를 실주문 전환 근거가 아니라 report/workorder source로만 유지한다`. 근거: `bash deploy/run_error_detection.sh full` 재실행 결과 [error_detection_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/error_detection/error_detection_2026-06-23.json)은 `summary_severity=pass`이고 `process_health`, `cron_completion`, `log_scanner`, `kiwoom_auth_8005_restart`, `artifact_freshness`, `resource_usage`, `stale_lock`가 모두 `pass`다. 같은 시각 `process_health`는 `main_loop_pid=241149`, `bot_expected_window=07:40~20:10`, `thread_status=ok`를 보고했고 `artifact_freshness`는 `pipeline_events_age_sec=0.8`, `threshold_events_age_sec=0.8`, `buy_funnel_sentinel_report_status=pass`, `holding_exit_sentinel_report_status=pass`, `panic_sell_defense_report_status=pass`, `panic_buying_report_status=pass`를 기록했다. 반면 [buy_funnel_sentinel_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-06-23.json)은 `classification.primary=SUBMIT_DROUGHT_CRITICAL`, [holding_exit_sentinel_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/holding_exit_sentinel/holding_exit_sentinel_2026-06-23.json)은 `classification.primary=HOLD_DEFER_DANGER`, [panic_sell_defense_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/panic_sell_defense/panic_sell_defense_2026-06-23.json)은 `panic_state=RECOVERY_WATCH`, [panic_buying_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/panic_buying/panic_buying_2026-06-23.json)은 `panic_buy_state=NORMAL`이면서 모두 `runtime_effect=report_only_no_mutation`이다. 장중 runtime threshold mutation, broker/order/provider/cap/bot 변경은 수행하지 않았다.

## 장후 체크리스트 (21:40~23:05)

- [ ] `[PostcloseSourceQualityGateReview0623] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-06-23`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:50`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-23.json), [threshold_cycle_ev_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-23.json), [code_improvement_workorder_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-23.json), [threshold_cycle_postclose_verification_2026-06-23.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-23.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0623] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-06-23`, `Slot: POSTCLOSE`, `TimeWindow: 21:50~22:05`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-22.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[CodeImprovementWorkorderReview0623] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-06-23`, `Slot: POSTCLOSE`, `TimeWindow: 22:05~22:20`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-06-22.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-22.md), [code_improvement_workorder_2026-06-22.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-22.json)
  - 판정 기준: selected_order_count=128와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0623] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-06-23`, `Slot: POSTCLOSE`, `TimeWindow: 22:20~22:35`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-22.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[LifecycleQuietGapReview0623] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-06-23`, `Slot: POSTCLOSE`, `TimeWindow: 22:35~22:50`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-06-22.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-22.json), [runtime_apply_gap_audit_2026-06-22.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-22.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`411`, rollup_required_count=`411`, sim_live_connected_quiet_gap_count=`3`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'absorbed_into_parent_policy': 8, 'ai_review_parsed_low_coverage': 1, 'exclusion_dimension_candidate': 23, 'parent_conflict_child': 58, 'positive_source_only_keep_collecting': 382}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0623] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-06-23`, `Slot: POSTCLOSE`, `TimeWindow: 22:50~23:05`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-06-22.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-06-22.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`16`, run_count=`16`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, scalp_sim_ai_deferred_review, pattern_lab_currentness_audit`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:15, source_missing_or_unreadable:7, upstream_drift_signal:7, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
