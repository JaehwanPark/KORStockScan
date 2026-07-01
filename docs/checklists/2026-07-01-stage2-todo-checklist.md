# 2026-07-01 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-06-30` postclose -> `2026-07-01`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0701] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-07-01`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-30.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-30.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 실행 결과: `applied_guard_passed_env`
  - 근거: `threshold_runtime_env_2026-07-01.json/env` generated_at=`2026-07-01T07:35:01+09:00`, source_date=`2026-06-30`, selected_families=`22`, blocked=`0`, warnings=`0`.
  - 검증: `threshold_runtime_env_verify_2026-07-01.json` status=`pass`, missing_family_count=`0`, pid=`23558`, pid_env_available=`true`, pid_passed=`true`.
  - Wrapper: `logs/threshold_cycle_preopen_cron.log`에 `[DONE] threshold-cycle preopen target_date=2026-07-01 finished_at=2026-07-01T07:35:01+0900` 확인.
  - 운영 경계: blocked family/approval missing/same-stage conflict를 수동 env override로 우회하지 않았고, 장중 threshold mutation 또는 broker/order/provider/bot/cap 변경을 수행하지 않았다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RuntimeEnvIntradayObserve0701] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-07-01`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-30.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-30.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, lifecycle_decision_matrix_runtime, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, weak_context_late_entry_guard_runtime, persistent_operator_overrides_2026_06_26가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.
  - 실행 결과 (`2026-07-01 11:16 KST`): `provenance_partial_no_rollback_guard_breach`.
  - 근거: [threshold_runtime_env_verify_2026-07-01.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-01.json)은 `passed=true`, `missing_family_count=0`, `pid_passed=true`로 닫혔다. 장중 event log 기준 selected family 22개 중 `score65_74_recovery_probe`, `quote_consistency_normalization`, `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `real_pyramid_scale_in_quality_guard_runtime`, `sell_side_open_time_block_runtime`, `weak_context_late_entry_guard_runtime`, `scalp_sim_auto_approval`, `entry_cancel_wait_runtime`는 provenance가 관측됐다.
  - 기준 목록 보정: 원래 체크리스트 판정 기준의 `lifecycle_decision_matrix_runtime`은 current manifest selected list에는 없고, current manifest에는 `lifecycle_bucket_discovery_sim_auto_approval`, `swing_sim_auto_approval`, `entry_cancel_wait_runtime`가 포함된다. 따라서 판정은 체크리스트 문구가 아니라 [threshold_runtime_env_verify_2026-07-01.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-01.json)의 current selected list를 기준으로 닫았다.
  - 미관측 분리: `soft_stop_whipsaw_confirmation`, `scalping_scanner_real_source_guard_runtime`, `score65_74_recovery_probe_strong_micro_override_runtime`, `entry_price_gap_profile_runtime`, `profit_stagnation_exit_runtime`, `latency_spread_relief_real_operator_override`, `ai_watching_score_smoothing_report_only`, `weak_pullback_entry_block_runtime`, `early_accel_recheck_runtime`, `pre_submit_liquidity_relief_runtime`, `persistent_operator_overrides_2026_06_26`, `lifecycle_bucket_discovery_sim_auto_approval`, `swing_sim_auto_approval`는 11:16 기준 해당 family trigger가 event log에서 확인되지 않았다. 이는 runtime env 누락이 아니라 장중 무발화/dormant 관찰 상태로 분리하며, rollback guard breach는 확인되지 않았다.
  - 운영 경계: 장중 threshold/order/provider/bot/cap 변경은 수행하지 않았다.

- [x] `[SimProbeIntradayCoverage0701] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-07-01`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-06-30.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-30.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.
  - 실행 결과 (`2026-07-01 11:16 KST`): `sim_probe_real_execution_separated`.
  - 근거: [pipeline_events_2026-07-01.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-01.jsonl) 및 [threshold_events_2026-07-01.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-01.jsonl) 스트리밍 확인 결과 sim/probe marker row 59,276건 중 `actual_order_submitted=true`는 0건이다. family hit는 `scalp_sim_auto_approval` 1,474건, `scalp_sim_candidate_window_expansion` 573건, `scalp_sim_ai_budget_manager` 202건, `score65_74_recovery_probe` 123건이다.
  - source-quality split: [intraday_entry_blocker_diagnostics_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-01.json) 기준 rising missed class는 `intended_guard_preserved=8`, `source_quality_excluded=5`, `runtime_backpressure_observation=3`, `strategy_reject_missed=1`로 분리됐다. stale/delayed low-AI-or-pressure eval은 569건이며 `diagnostic_quote_age_stale=466`, `pre_ai_stale_or_history_gap=103`으로 분류됐다.
  - flow 확인: [intraday_entry_flow_2026-07-01_current.md](/home/ubuntu/KORStockScan/data/report/intraday_entry_flow/intraday_entry_flow_2026-07-01_current.md)는 `rising_missed_residual_excluding_forced_scout_symbol_count=2`, `rising_missed_forced_scout_residual_symbol_count=12`, `real_submit_symbol_count_in_latest_diagnostic=1`로 forced scout residual과 일반 residual을 분리했다.
  - 운영 경계: sim/probe EV를 broker execution 품질 또는 실주문 전환 근거로 사용하지 않았고, 장중 threshold/order/provider/bot/cap 변경은 수행하지 않았다.

- [x] `[LowProfitStagnationHardExitCandidate0701] 실보유 스캘핑 조정수익권 장기횡보 하드청산 실전후보 적용` (`Due: 2026-07-01`, `Slot: INTRADAY`, `TimeWindow: 15:50~16:05`, `Track: ScalpingLogic`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [test_sniper_scale_in.py](/home/ubuntu/KORStockScan/src/tests/test_sniper_scale_in.py)
  - 판정 기준: real SCALPING 보유 포지션만 대상으로 `adjusted_profit_pct=profit_rate_pct-assumed_exit_slippage_bps/100`이 `0.20~1.00%`이고 보유시간이 `1800s` 이상이면 AI/고점/호가 조건 없이 `scalp_low_profit_stagnation_hard_exit`를 낸다.
  - 실행 결과: `implemented_and_target_validated`.
  - 검증: `.venv/bin/python -m compileall src/utils/constants.py src/engine/sniper_state_handlers.py src/engine/threshold_cycle_preopen_apply.py`, `.venv/bin/python -m pytest src/tests/test_constants.py::test_trading_rules_profit_stagnation_exit_env_override` plus the four `test_scalp_low_profit_stagnation_hard_exit_*` tests and two `test_profit_stagnation_*low_profit_hard_exit_candidate` preopen tests, `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500`, `git diff --check`.
  - 운영 경계: sim/probe는 제외하고, 장중 threshold mutation/provider/order/cap 변경 및 bot 재기동은 수행하지 않았다.

- [x] `[SmoothingAxisDisposition0701] smoothing 3축 적용/보완/폐기 판정 마무리` (`Due: 2026-07-01`, `Slot: INTRADAY`, `TimeWindow: 16:05~16:20`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-06-30.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-30.json), [threshold_apply_2026-07-01.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-01.json), [threshold_events_2026-07-01.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-01.jsonl), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py)
  - 판정: `protect_trailing_smoothing=env_mapping_fixed_next_preopen_apply_candidate`, `holding_flow_ofi_smoothing=keep_existing_internal_smoothing_monitor_until_value_delta`, `ai_watching_score_smoothing_report_only=freshness_root_fix_implemented_keep_report_only_next_session_recheck`.
  - 근거: `protect_trailing_smoothing`은 `sample_count=50`, `sample_floor_status=ready`, `calibration_state=adjust_down`였지만 PREOPEN decision이 `no_runtime_env_override`라 `SCALP_PROTECT_TRAILING_SMOOTH_*` mapping을 보완했다. `holding_flow_ofi_smoothing`은 오늘 `holding_flow_ofi_smoothing_applied=57`, `force_exit=725`로 관측이 유의미하지만 전일 추천값이 현행값과 같아 신규 runtime 값을 열지 않는다. `ai_watching_score_smoothing_report_only`는 오늘 `ai_confirmed` 표본에서 `stale_context_or_quote`가 115건이고 그중 quote-only 3초 이내 회복 가능 표본이 29건 확인되어 root cause를 먼저 보완했다. 원인은 AI 입력 feature packet과 AI freshness recompute가 pre-AI freshness 기준보다 과도하게 짧은 stale 기준을 쓰고, `ai_confirmed` 로그에 `pre_ai_ws_snapshot_refresh_*` provenance가 빠져 원인 분리가 불가능했던 것이다.
  - 보완: [scalping_feature_packet.py](/home/ubuntu/KORStockScan/src/engine/scalping_feature_packet.py)는 quote stale 기준을 pre-AI 3초 창으로 정렬했고, [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)는 AI quote freshness recompute도 pre-AI 기준을 쓰며 `ai_confirmed` 로그에 `pre_ai_ws_snapshot_refresh_*` provenance를 보존한다. Broker submit revalidation 2초 stale guard는 변경하지 않았다.
  - 검증: `.venv/bin/python -m compileall src/engine/scalping_feature_packet.py src/engine/sniper_state_handlers.py src/engine/threshold_cycle_preopen_apply.py`, `.venv/bin/python -m pytest src/tests/test_scalping_feature_packet.py src/tests/test_watching_score_smoothing.py::test_ai_confirmed_optional_provenance_keeps_existing_score_contract src/tests/test_watching_score_smoothing.py::test_ai_confirmed_log_fields_preserve_pre_ai_refresh_provenance src/tests/test_state_handler_fast_signatures.py::test_update_ai_quote_freshness_fields_overwrites_stale_provenance src/tests/test_state_handler_fast_signatures.py::test_update_ai_quote_freshness_fields_uses_pre_ai_window src/tests/test_state_handler_fast_signatures.py::test_update_ai_quote_freshness_fields_marks_stale_after_pre_ai_window`, dry check `_env_overrides_for_candidate(protect_trailing_smoothing)` -> `KORSTOCKSCAN_SCALP_PROTECT_TRAILING_SMOOTH_WINDOW_SEC`, `KORSTOCKSCAN_SCALP_PROTECT_TRAILING_SMOOTH_MIN_SPAN_SEC` 생성 확인.
  - 운영 경계: 장중 runtime threshold mutation, bot 재기동, provider/order/cap 변경은 수행하지 않았다. 적용은 다음 PREOPEN `auto_bounded_live` 후보로만 허용한다.

- [x] `[HoldingFlowOfiAssistLayerClarification0701] holding_flow_ofi_smoothing 보조층 명확화 구현` (`Due: 2026-07-01`, `Slot: INTRADAY`, `TimeWindow: 16:20~16:35`, `Track: ScalpingLogic`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [test_holding_flow_override.py](/home/ubuntu/KORStockScan/src/tests/test_holding_flow_override.py), [test_daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/tests/test_daily_threshold_cycle_report.py)
  - 판정: `implemented_as_holding_flow_override_assist_layer`.
  - 근거: `OFI_STABLE_BULLISH + EXIT` 디바운스는 기본 2회 상한과 source-quality/never-green guard를 통과할 때만 허용하고, `DEBOUNCE_EXIT`, `CONFIRM_EXIT`, `NO_CHANGE`, `force_exit` phase를 분리 기록하도록 보강했다. `force_exit`은 스무딩 실패가 아니라 기존 청산/안전 우선순위 이벤트로 유지한다.
  - 검증: targeted compile/pytest/review-gate 결과를 본 작업 결과 보고에 기록한다.
  - 운영 경계: intraday runtime threshold mutation, bot 재기동, provider/order/cap 변경은 수행하지 않았고, existing `holding_flow_override` 내부 보조층 정리만 수행했다.

- [ ] `[IntradaySourceQualityGateCheck0701] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-07-01`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-07-01.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-01.jsonl), [threshold_events_2026-07-01.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-01.jsonl), [observation_source_quality_audit_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-01.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-07-01 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:40~23:05)

- [x] `[PostcloseSourceQualityGateReview0701] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-07-01`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-01.json), [threshold_cycle_ev_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-01.json), [code_improvement_workorder_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-01.json), [threshold_cycle_postclose_verification_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-01.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 실행 결과: `source_quality_gate_pass`.
  - 근거: [observation_source_quality_audit_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-01.json) generated_at=`2026-07-01T20:30:04+09:00`, status=`pass`, event_count=`156472`, stage_count=`159`, tuning_input_allowed=`true`, hard_blocking_contract_gap_count=`0`, hard_blocking_excluded_row_count=`0`, unknown_token_stage_count=`0`, review_warning_count=`0`, raw_row_exclusion_applied=`false`.
  - 검증 결과: [threshold_cycle_ev_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-01.json) summary source_quality_status=`pass`, source_quality_tuning_input_allowed=`true`; [threshold_cycle_postclose_verification_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-01.json) stale_downstream_links=`[]`, missing_downstream_links=`[]`.
  - 운영 경계: source-quality 결과를 threshold/order/provider/bot/cap 변경 근거로 사용하지 않았다.

- [x] `[ThresholdDailyEVReport0701] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-07-01`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-01.json), [runtime_approval_summary_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-07-01.json), [lifecycle_bucket_discovery_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-01.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 실행 결과: `daily_ev_sim_evidence_present_no_live_bucket`.
  - 근거: [threshold_cycle_ev_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-01.json) summary status=`warning`, real_sample=`24`, sim_sample=`207`, primary_verdict=`sim_evidence_present_no_live_bucket`, live_auto_ready_count=`0`, runtime_effect=`false`, decision_authority=`threshold_cycle_ev_summary_report_only`.
  - 다음 PREOPEN 입력 분리: lifecycle_bucket_discovery sim_auto_approved_count=`2`, swing_lifecycle_bucket_discovery sim_auto_approved_count=`26`; live_auto_apply_ready_count=`0`이라 실주문/live 전환 후보는 없다. calibration_outcome은 `adjust_up` 2개(`bad_entry_refined_canary`, `lifecycle_decision_matrix_runtime`), `hold_sample` 6개, `freeze` 1개(`trailing_continuation`), 나머지는 hold/hold_no_edge로 분리한다.
  - 운영 경계: sim/combined EV를 broker execution 품질 또는 live 전환 확정 근거로 사용하지 않았고, threshold/order/provider/bot/cap 변경을 수행하지 않았다.

- [x] `[HumanInterventionSummary0701] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-07-01`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-07-01.json), [threshold_cycle_ev_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-01.json), [code_improvement_workorder_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-01.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 실행 결과: `observe_only_with_manual_sync_required`.
  - 승인/개입 분류: runtime_mutation_allowed=`false`, lifecycle_bucket_discovery human_intervention_required=`false`, panic_approval_requested=`0`, swing_requested=`0`, swing_approved=`0`. panic approval artifacts는 `panic_entry_freeze_guard_2026-07-01.json`, `panic_buy_runner_tp_canary_2026-07-01.json` 모두 contract_missing/live_ready=`false`라 승인 대기 후보가 아니다. entry_bucket_2 `liquidity_high`는 approval_required=`true`지만 next_route=`threshold_cycle_runtime_approval_request_after_rolling_confirmation`, allowed_runtime_apply=`false`라 관찰/후속 rolling 확인으로 분류한다.
  - Codex 구현 필요: [code_improvement_workorder_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-01.json) selected_implement_now_route_count=`0`, selected_unimplemented_runtime_effect_false_count=`0`, selected_longstanding_non_implement_action_required_order_ids=`[]`; 금일 추가 구현 지시 대상 없음.
  - 수동 동기화 필요: checklist/doc 변경 후 Project/Calendar sync는 사용자가 표준 명령으로 수행한다.
  - 운영 경계: approval request만으로 env 파일을 직접 수정하지 않았고, provider/order/bot/cap/threshold 변경을 수행하지 않았다.

- [x] `[CodeImprovementWorkorderReview0701] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-07-01`, `Slot: POSTCLOSE`, `TimeWindow: 22:05~22:20`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-07-01.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-01.md), [code_improvement_workorder_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-01.json), [threshold_cycle_postclose_verification_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-01.json), [postclose_done_controller_2026-07-01.md](/home/ubuntu/KORStockScan/data/report/postclose_done_controller/postclose_done_controller_2026-07-01.md)
  - 판정 기준: selected_order_count=`99`와 `implement_now`, `attach_existing_family`, `defer_evidence` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 실행 결과: `implement_now_2pass_completed_no_remaining_implement_now`; final generation_id=`2026-07-01-28321bb6a113`, source_hash=`28321bb6a11328cade3f87c9b75f15559b690ddd30d41a88ca08b5405c226cc0`, selected_order_count=`99`, selected_decision_counts=`{'attach_existing_family': 96, 'defer_evidence': 3}`.
  - 2-pass diff: new_order_ids=`[]`, removed_order_ids=`['order_swing_pattern_lab_deepseek_selection_low_candidate_count', 'order_swing_scale_in_avg_down_pyramid_observation']`, decision_changed_order_ids=`[]`.
  - 구현 분리: 기존 구현/연결=`attach_existing_family 96`, 신규 source-only provenance 보완=`scanner_strength_history`, `bounded_rising_freshness_recheck`, `scanner_runtime_attach_identity`, `forced_scout_post_sell/scale_in/loss_filter`, `swing_scale_in_candidate_path_source_only_diagnostic`, `swing_selection_top_k_floor_source_only_review`; runtime/order/provider/bot/threshold/cap 변경=`none`.
  - 비-implement 재판정: selected_longstanding_non_implement=`6`, disposition_counts=`{'keep_visible_by_design': 4, 'review_required': 2}`, action_required_order_ids=`[]`; non_selected action_required_order_ids=`[]`.
  - 장기 미해결 처리방안 재확인: `keep_visible_by_design` 4개는 lifecycle quiet/source-dimension rollup과 exit stage-only child evidence로 계속 노출하되 즉시 코드수리 대상이 아니다. 남은 `review_required` 2개는 euphoria/panic exit unknown outcome stage-only child evidence로 parent lifecycle flow 증거를 계속 수집하고 stage-only live promotion은 금지한다. `swing_scale_in_avg_down_pyramid_observation`은 `swing_scale_in_candidate_path_diagnostic_v1` source-only 계약으로 후보 경로 진단을 구현했고, `swing_pattern_lab_deepseek_selection_low_candidate_count`는 `swing_pattern_lab_selection_low_candidate_source_metric_v1` source-only 계약으로 top_k/floor 검토 근거를 구현해 action_required에서 제거했다.
  - non-selected 재판정: review_required 6개는 selected 한도 밖이므로 금일 implement 대상에서 제외한다. `overbought_gate_miss_ev_recovery`는 20일 block_ratio=`98.2%`로 다음 후보군에서 우선순위 상승 가능성이 있으나 별도 구현 지시 전까지 runtime_effect=`false`; Kiwoom HTTP session/config cache 후보는 parity 계약이 커서 deferred evidence로 유지한다.
  - 검증 결과: postclose verifier=`warning` with stale_downstream_links=`[]`, missing_downstream_links=`[]`; postclose DONE controller=`done`; wrapper DONE provider markers remain `openai`, not `none`.
  - 다음 액션: `longstanding_non_implement_action_required_cleared`; 남은 selected long-standing 6개는 keep-visible/stage-only evidence 수집 상태로 유지하고 별도 사용자 승인 전까지 runtime_effect=`false`로 둔다.

- [x] `[LifecycleJoinProvenanceWorkorder0701] lifecycle join/provenance 본수리 1차 pass 실행` (`Due: 2026-07-01`, `Slot: POSTCLOSE`, `TimeWindow: 22:20~22:35`, `Track: ScalpingLogic`)
  - Source: [lifecycle_bucket_discovery_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-01.json), [threshold_cycle_ev_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-01.json), [threshold_cycle_postclose_verification_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-01.json), [lifecycle_bucket_discovery.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_bucket_discovery.py), [threshold_cycle_ev_report.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_ev_report.py)
  - 판정 기준: 2026-06-30에 추가된 `positive_ev_stage_sampling_plan`, `child_conflict_stratified_targets`, `stage_counterfactual_variant_plan_v1` 수집 계약을 기준으로 `missing_holding`, `missing_exit`, child conflict, complete-flow 부족이 어느 producer/consumer join에서 생기는지 분해하고, lifecycle event identity join key와 entry/submit/holding/exit/scale_in provenance 연결 결함을 우선 보완한다.
  - 금지: posterior field(`exit_outcome_parent`, `major_holding_parent`, `scale_in_parent`)를 runtime match 조건으로 쓰지 않는다. sim/probe observation을 실주문 전환, provider/bot/cap/order/threshold 변경, broker guard 우회 근거로 사용하지 않는다.
  - 실행 결과: `defer_until_more_sample`.
  - 근거: [lifecycle_bucket_discovery_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-01.json) status=`pass`, selected_parent_level=`L2_default`, parent_granularity_status=`target_pass`, automation_handoff_gap_count=`0`, code_patch_required_count=`0`, active_sim_priority_active_seed_count=`6`, positive_parent_count=`4`, positive_parent_sample_ready_count=`1`, active_sim_priority_complete_flow_need_count=`3`.
  - join/provenance 판정: active seed의 `positive_ev_stage_sampling_plan`은 runtime_match_fields를 entry/submit observable prefix로 제한하고 runtime_match_forbidden_fields=`['exit_outcome_parent', 'major_holding_parent', 'scale_in_parent']`를 보존한다. complete_flow_count 부족은 producer/consumer join 결함이 아니라 holding/exit/scale-in post-observation sample 부족으로 분리한다.
  - 운영 경계: 코드 변경은 수행하지 않았고, posterior field를 runtime match 조건으로 쓰지 않았으며, 실주문/provider/bot/cap/order/threshold 변경 근거로 사용하지 않았다.

- [x] `[LifecycleQuietGapReview0701] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-07-01`, `Slot: POSTCLOSE`, `TimeWindow: 22:35~22:50`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-01.json), [runtime_apply_gap_audit_2026-07-01.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-01.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`388`, rollup_required_count=`388`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'absorbed_into_parent_policy': 2, 'ai_review_parsed_low_coverage': 1, 'exclusion_dimension_candidate': 1, 'parent_conflict_child': 3, 'positive_source_only_keep_collecting': 387}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 실행 결과: `rollup_only`.
  - 근거: [runtime_apply_gap_audit_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-01.json) status=`pass`, quiet_gap_count=`389`, quiet_gap_rollup_count=`389`, sim_live_connected_quiet_gap_count=`1`, positive_source_only_keep_collecting_count=`385`, parent_conflict_child_count=`7`, exclusion_dimension_candidate_count=`2`, absorbed_into_parent_policy_count=`3`, ai_review_parsed_low_coverage_count=`1`, ai_review_status=`parsed`, codex_directive_count=`0`, quiet_gap_codex_directive_count=`0`.
  - 처리방안: parent conflict/exclusion은 source-only blocker/parent policy rollup으로 보존하고, positive source-only 385건은 sample floor까지 계속 수집한다. sim_live_connected 1건은 다음 PREOPEN lifecycle flow sim-probe policy input 후보일 뿐 live authority가 아니다.
  - 운영 경계: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않았다.

- [x] `[AutomationTriggerDecisionSummary0701] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-07-01`, `Slot: POSTCLOSE`, `TimeWindow: 22:50~23:05`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-07-01.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [threshold_cycle_postclose_cron.log](/home/ubuntu/KORStockScan/logs/threshold_cycle_postclose_cron.log)
  - 판정 기준: trigger decision summary의 total_steps=`16`, run_count=`16`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, scalp_sim_ai_deferred_review, pattern_lab_currentness_audit`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:15, source_missing_or_unreadable:7, upstream_drift_signal:7, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 실행 결과: `trigger_contract_pass`.
  - 근거: [automation_chain_trigger_decision_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-07-01.json) total_steps=`16`, run_count=`16`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`; run_steps=`['lifecycle_window_rolling5d', 'lifecycle_window_rolling10d', 'lifecycle_window_mtd', 'scalp_sim_ai_deferred_review', 'pattern_lab_currentness_audit', 'pattern_lab_ai_review', 'observation_source_quality_audit', 'observation_source_quality_backfill_audit', 'ai_watching_score_smoothing_diagnostic', 'codebase_performance_workorder', 'producer_gap_discovery', 'stage_hook_workorder_discovery', 'stage_hook_runtime_scaffold', 'pattern_lab_propagation_audit', 'runtime_apply_gap_audit', 'workorder_branch']`; top_reasons=`output_missing_or_unreadable:14`, `source_missing_or_unreadable:7`, `upstream_drift_signal:7`, `upstream_artifact_newer:1`.
  - wrapper 대조: [threshold_cycle_postclose_cron.log](/home/ubuntu/KORStockScan/logs/threshold_cycle_postclose_cron.log)는 `[DONE] threshold-cycle postclose target_date=2026-07-01 ... finished_at=2026-07-01T20:35:16+0900`를 남겼고, trigger_decision skip marker는 없다. 관측된 `[SKIP] threshold_cycle_ev_final_consumer_refresh reason=duplicate_refresh_fresh`는 trigger decision skip이 아니라 중복 final refresh 생략으로 분리한다.
  - 운영 경계: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality 경계 변경 근거로 사용하지 않았다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-07-01 15:46:15`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-07-01.md`
- `Trade Review`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
