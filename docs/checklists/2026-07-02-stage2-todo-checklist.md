# 2026-07-02 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-07-01` postclose -> `2026-07-02`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0702] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-07-02`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-01.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 실행 결과: `applied_guard_passed_env`.
  - 근거: [threshold_apply_2026-07-02.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-02.json) status=`auto_bounded_live_ready`, apply_mode=`auto_bounded_live`, runtime_change=`true`, source_date=`2026-07-01`, generated_at=`2026-07-02T07:35:01+09:00`, blocked=`0`, warnings=`0`.
  - runtime env: [threshold_runtime_env_2026-07-02.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-02.json) selected_families=`22`, generated_at=`2026-07-02T07:35:01+09:00`; [threshold_runtime_env_2026-07-02.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-02.env) 생성 확인.
  - 검증: [threshold_runtime_env_verify_2026-07-02.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-02.json) status=`pass`, passed=`true`, missing_family_count=`0`, findings=`0`, pid_env_available=`false`, pid_passed=`true`.
  - Wrapper: [threshold_cycle_preopen_cron.log](/home/ubuntu/KORStockScan/logs/threshold_cycle_preopen_cron.log)에 `[DONE] threshold-cycle preopen target_date=2026-07-02 finished_at=2026-07-02T07:35:01+0900` 확인.
  - 운영 경계: blocked family/approval missing/same-stage conflict를 수동 env override로 우회하지 않았고, 장중 threshold mutation 또는 broker/order/provider/bot/cap 변경을 수행하지 않았다.

- [x] `[RisingMissedScoutRuntimePreopen0702] rising_missed_scout_workorder 구현분 다음 장전 runtime 반영 여부 확인` (`Due: 2026-07-02`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-07-01.json), [code_improvement_workorder_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-01.json), [threshold_apply_2026-07-02.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-02.json), [threshold_runtime_env_2026-07-02.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-02.json), [threshold_runtime_env_verify_2026-07-02.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-02.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`4`, forced_scout_with_post_sell_count=`23`, profitable_forced_scout_count=`17`, loss_or_flat_forced_scout_count=`6`, current_missed_count=`13`)과 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.
  - 실행 결과: `source_only_no_runtime_authority`.
  - 근거: [rising_missed_scout_workorder_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-07-01.json) summary는 code_improvement_order_count=`4`, forced_scout_with_post_sell_count=`23`, profitable_forced_scout_count=`17`, loss_or_flat_forced_scout_count=`6`, current_missed_count=`24`를 기록했다. mapped_family는 `rising_missed_scout_post_sell_bridge`, `rising_missed_scout_loss_filter`, `rising_missed_scout_scale_in_price_guard_split`, `rising_missed_scout_scale_in_qty_evidence_split` 4개다.
  - runtime 반영 판정: 4개 mapped_family 모두 [threshold_runtime_env_2026-07-02.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-02.json)의 selected_families 22개에 포함되지 않는다. 이는 verify 실패가 아니라 source-only workorder가 별도 runtime family/env mapping과 apply guard를 통과하지 않은 상태다.
  - workorder 대조: [code_improvement_workorder_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-01.json) summary는 rising_missed_scout_source_order_count=`4`, selected_implement_now_route_count=`0`, selected_unimplemented_runtime_effect_false_count=`0`로 닫혔다.
  - 검증: [threshold_runtime_env_verify_2026-07-02.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-02.json) status=`pass`, missing_family_count=`0`, findings=`0`.
  - 운영 경계: forced 1-share scout 손익을 normal BUY/submit/fill success 또는 real execution quality approval로 계산하지 않았고, stale submit bypass, broker/order guard 완화, provider/bot/cap/threshold 변경을 수행하지 않았다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RisingMissedInitialQualityFeedbackLoop0702] rising_missed 후 avg_down_count>=2 장중 피드백 루프 구성` (`Due: 2026-07-02`, `Slot: INTRADAY`, `TimeWindow: 08:00~19:55`, `Track: ScalpingLogic`)
  - Source: [rising_missed_intraday_feedback.py](/home/ubuntu/KORStockScan/src/engine/monitoring/rising_missed_intraday_feedback.py), [run_rising_missed_intraday_feedback.sh](/home/ubuntu/KORStockScan/deploy/run_rising_missed_intraday_feedback.sh), [install_stage2_ops_cron.sh](/home/ubuntu/KORStockScan/deploy/install_stage2_ops_cron.sh), [rising_missed_scout_workorder.py](/home/ubuntu/KORStockScan/src/engine/monitoring/rising_missed_scout_workorder.py)
  - 판정 기준: `rising_missed_one_share_entry` forced scout 이후 holding snapshot에서 `avg_down_count>=2`가 발생한 record를 `record_id`로 join해 `rising_missed_initial_quality_fail|rising_missed_initial_quality_fail_open|rising_missed_scale_in_rescue_warning|rising_missed_initial_quality_review`로 라벨링하고, postclose workorder에 source-only 후속 주문으로 전달한다.
  - 금지: 장중 feedback label만으로 runtime threshold mutation, broker/order/scale-in guard 완화, quantity/cap release, provider route, bot restart, forced scout success counting, real execution quality approval을 열지 않는다.
  - 실행 결과: `implemented_source_only_intraday_feedback_loop`.
  - 근거: `src.engine.monitoring.rising_missed_intraday_feedback --target-date YYYY-MM-DD --print-summary` producer와 5분 주기 wrapper `deploy/run_rising_missed_intraday_feedback.sh`를 추가했고, `deploy/install_stage2_ops_cron.sh`에 NXT 포함 `08:00~19:55` `RISING_MISSED_INTRADAY_FEEDBACK_5MIN` marker를 추가했다. `rising_missed_scout_workorder`는 `data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_YYYY-MM-DD.json` summary를 읽어 `rising_missed_initial_quality_feedback_loop` source-only order로 전달한다.
  - 검증: targeted pytest, py_compile, parser validation, wrapper dry-run, `git diff --check` 결과를 본 작업 종료 보고에 기록한다.

- [x] `[RuntimeEnvIntradayObserve0702] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-07-02`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-01.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, weak_context_late_entry_guard_runtime, persistent_operator_overrides_2026_06_26가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.
  - 실행 결과: `provenance_partially_present_no_rollback_breach`.
  - 근거: [threshold_runtime_env_2026-07-02.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-02.json) generated_at=`2026-07-02T07:35:01+09:00`, selected_families=`22`; [threshold_runtime_env_verify_2026-07-02.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-02.json) status=`pass`.
  - 이벤트 대조: [threshold_events_2026-07-02.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-02.jsonl) 및 [pipeline_events_2026-07-02.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-02.jsonl) 스트리밍 집계에서 `score65_74_recovery_probe` total=`324`, `scalp_sim_ai_budget_manager`=`470`, `lifecycle_decision_matrix_runtime`=`47`, `sell_side_open_time_block_runtime`=`414`, `weak_context_late_entry_guard_runtime`=`2`, `entry_cancel_wait_runtime`=`163` 확인. [observation_source_quality_audit_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-02.json)은 `scalping_scanner_real_source_guard_block`=`2111`도 관찰했다.
  - missing/natural no-match: 일부 selected family는 장중 자연 조건 미발생 또는 exact family tag 미기록으로 event count=`0`이었다. 이는 runtime env verify 실패나 rollback breach로 보지 않고 장후 post-apply attribution에서 재확인한다.
  - rollback guard: threshold event 텍스트 내 `safety_revert|rollback|severe_loss|order_provenance_breach|provenance_breach` keyword count=`0`. 장중 threshold mutation, provider/bot/cap/order guard 변경 없음.

- [x] `[SimProbeIntradayCoverage0702] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-07-02`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-07-01.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-01.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.
  - 실행 결과: `sim_probe_real_execution_separated_with_source_quality_warning`.
  - 근거: [threshold_events_2026-07-02.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-02.jsonl) sim/probe/counterfactual/virtual token 집계는 events=`4673`, actual_order_submitted=false=`4665`, true=`0`, missing=`8`; [pipeline_events_2026-07-02.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-02.jsonl) 대응 집계는 events=`5181`, false=`4783`, true=`0`, missing=`398`.
  - active 관찰축: `scalp_sim_ai_holding_live_call`=`453`, `scalp_sim_panic_scale_in_blocked`=`1027`, `scalp_sim_candidate_window_discarded`=`182`, `score65_74_recovery_probe_blocked`=`154`, `scalp_sim_partial_sell_order_assumed_filled`=`128` 등 sim/probe 이벤트가 real order와 분리되어 기록됐다.
  - source-quality split: [observation_source_quality_audit_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-02.json) status=`warning`, hard_blocking_contract_gap_count=`0`, raw_row_exclusion_applied=`true`; missing provenance rows는 장후 source-quality/workorder handoff에서 재확인한다.
  - 운영 경계: sim/probe EV를 broker execution 품질, 실주문 전환, threshold/provider/bot/cap 변경 근거로 사용하지 않았다.

- [x] `[IntradaySourceQualityGateCheck0702] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-07-02`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-07-02.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-02.jsonl), [threshold_events_2026-07-02.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-02.jsonl), [observation_source_quality_audit_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-02.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-07-02 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.
  - 실행 결과: `defective_rows_excluded`.
  - 실행 명령: `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-07-02 --write`.
  - 근거: [observation_source_quality_audit_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-02.json) generated_at=`2026-07-02T16:19:02+09:00`, status=`warning`, event_count=`105490`, stage_count=`159`, hard_blocking_contract_gap_count=`0`, hard_blocking_excluded_row_count=`0`, tuning_input_allowed=`true`, raw_row_exclusion_applied=`true`, unknown_token_stage_count=`1`, review_warning_count=`1`, review_warning_stages=`sell_order_sent`.
  - row exclusion: raw_row_exclusion excluded_row_count=`352`, stage_counts=`scalp_entry_action_decision_snapshot:342`, `scale_in_price_resolved:10`; manifest=[manifest.json](/home/ubuntu/KORStockScan/data/source_quality/raw_row_exclusion/2026-07-02_20260702T161736829795+0900/manifest.json).
  - 다음 장후 확인: unknown-token/review warning은 `PostcloseSourceQualityGateReview0702`와 `CodeImprovementWorkorderReview0702`에서 workorder handoff 누락 여부를 재확인한다. broker/order/provider/cap/bot/threshold 변경은 수행하지 않았다.

## 장후 체크리스트 (20:05~21:55)

- [x] `[PostcloseSourceQualityGateReview0702] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-07-02`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-02.json), [threshold_cycle_ev_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-02.json), [code_improvement_workorder_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-02.json), [threshold_cycle_postclose_verification_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-02.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 실행 결과: `source_quality_gate_pass`.
  - 근거: `status=pass`, `event_count=144149`, `hard_blocking_contract_gap_count=0`, `warning_stage_count=0`, `unknown_token_stage_count=0`, `review_warning_count=0`, `tuning_input_allowed=true`, `raw_row_exclusion_applied=false`.
  - 다음 액션: 결손 row/window 제외나 source-quality workorder 보강은 필요 없다.

- [x] `[ThresholdDailyEVReport0702] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-07-02`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-02.json), [runtime_approval_summary_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-07-02.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 실행 결과: `daily_ev_report_generated_report_only_no_live_bucket`.
  - 근거: EV summary `status=warning`, `source_quality_status=pass`, `source_quality_tuning_input_allowed=true`, `real_sample=19`, `sim_sample=159`, `live_auto_ready_count=0`, `primary_verdict=sim_evidence_present_no_live_bucket`, `runtime_effect=false`, `decision_authority=threshold_cycle_ev_summary_report_only`.
  - 다음 액션: 오늘 EV는 다음 장전 실거래 전환 입력이 아니라 sim/report-only 관찰 증거로 유지한다.

- [x] `[HumanInterventionSummary0702] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-07-02`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-07-02.json), [code_improvement_workorder_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-02.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 실행 결과: `observe_only_no_operator_action_required`.
  - 근거: runtime approval `approval_requests_count=0`, `operator_required=0`, panic approval requested `0`, swing requested `0`, swing approved `0`; workorder `selected_longstanding_non_implement_action_required_order_ids=[]`.
  - 다음 액션: Project/Calendar 동기화는 문서 수정 후 표준 수동 명령만 남긴다.

- [x] `[CodeImprovementWorkorderReview0702] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-07-02`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-07-02.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-02.md), [code_improvement_workorder_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-02.json)
  - 판정 기준: selected_order_count=106와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 실행 결과: `already_implemented_or_no_new_implement_now`.
  - 근거: `source_order_count=165`, `selected_order_count=106`, `selected_implement_now_route_count=0`, `selected_unimplemented_runtime_effect_false_count=0`, `needs_followup_workorder_count=0`, `repeat_unresolved_escalation_count=0`, `selected_terminal_non_implement_longstanding_count=6`, disposition `keep_visible_by_design=4`, `review_required=2`, action required IDs `[]`.
  - 다음 액션: 오늘 신규 Codex 구현 대상은 없고, 장기 non-implement는 workorder에 계속 노출한다.

- [x] `[LifecycleQuietGapReview0702] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-07-02`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-02.json), [runtime_apply_gap_audit_2026-07-02.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-02.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count, quiet_gap_rollup_count, positive edge/source-quality pass, Codex directive count, retry queue를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 실행 결과: `rollup_only`.
  - 근거: runtime apply gap audit `status=pass`, `quiet_gap_count=397`, `quiet_gap_rollup_count=397`, `quiet_gap_codex_directive_count=0`, `retry_queue_count=0`, `critical_failure_count=0`, `positive_edge_source_quality_pass_count=52`, `runtime_effect=false`.
  - 다음 액션: quiet gap은 rollup/source-only 관찰로 유지하고, runtime threshold/env/provider/order/bot 변경은 하지 않는다.

- [x] `[AutomationTriggerDecisionSummary0702] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-07-02`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-07-02.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps, run_count, skip_count, source_missing_count, force_override_count를 확인하고 wrapper 로그 marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 실행 결과: `trigger_contract_pass`.
  - 근거: `total_steps=16`, `run_count=16`, `skip_count=0`, `source_missing_count=7`, `force_override_count=0`, decision counts `run=16`, `runtime_effect=false`, `allowed_runtime_apply=false`.
  - 다음 액션: source-missing은 run-required 경로로 관찰하고, PREOPEN apply나 broker/order/provider/cap/bot/threshold 변경에는 사용하지 않는다.

- [x] `[PostcloseEarlyShutdownSchedule0702] 장후 병렬화 및 EOD 조기 종료 스케줄 확인` (`Due: 2026-07-02`, `Slot: POSTCLOSE`, `TimeWindow: 20:05~21:55`, `Track: RuntimeStability`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [install_postclose_done_controller_cron.sh](/home/ubuntu/KORStockScan/deploy/install_postclose_done_controller_cron.sh), [install_eod_data_chain_cron.sh](/home/ubuntu/KORStockScan/deploy/install_eod_data_chain_cron.sh), [install_error_detection_cron.sh](/home/ubuntu/KORStockScan/deploy/install_error_detection_cron.sh), [postclose_done_controller_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/postclose_done_controller/postclose_done_controller_2026-07-02.json), [threshold_cycle_postclose_verification_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-02.json)
  - 판정 기준: `update_kospi` 20:05, `THRESHOLD_CYCLE_POSTCLOSE` 20:10, `POSTCLOSE_DONE_CONTROLLER` 20:10 병렬 기동, dashboard archive 20:50, log rotation cleanup 21:00, error detector 07:00~21:55 주기를 crontab과 detector registry에서 대조한다.
  - 금지: 조기 종료 스케줄 조정을 runtime threshold/order/provider/cap/bot/hard-safety 변경 근거로 사용하지 않는다.
  - 실행 결과: `postclose_done_controller_done`.
  - 근거: done controller `status=done`, `generated_at=2026-07-02T20:36:10+09:00`; postclose verification `status=warning`, `generated_at=2026-07-02T20:47:44+09:00`, `predecessor_integrity=pass`, `wait_count=0`, `timeout_count=0`, `log_issues=0`, warning list empty.
  - 다음 액션: verifier warning은 컨트롤러 실패가 아니므로 산출물 생성 완료로 닫고, 다음 영업일에는 warning 원인이 노출되는지 postclose verifier schema를 재확인한다.

### Runbook 운영 확인 기록

- [x] `[PostcloseAutomationHealthCheck20260702] 장후 자동화체인 상태 확인` (`Due: 2026-07-02`, `Slot: POSTCLOSE`, `TimeWindow: 20:05~21:55`, `Track: RunbookOps`)
  - 판정: `warning`.
  - Tuning Chain Control State: `YELLOW`.
  - blocked_stage: `feedback_closure`.
  - 영향: postclose source-quality gate와 DONE controller는 정상 종료됐고 workorder/action-required 누락은 없지만, final verifier status가 `warning`으로 남아 있어 다음 영업일 postclose verifier schema 원인 노출 여부를 재확인한다.
  - 근거: [postclose_done_controller_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/postclose_done_controller/postclose_done_controller_2026-07-02.json) `status=done`, [threshold_cycle_postclose_verification_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-02.json) `status=warning`, `predecessor_integrity=pass`, `wait_count=0`, `timeout_count=0`, `log_issues=0`; [observation_source_quality_audit_2026-07-02.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-02.json) `status=pass`, `tuning_input_allowed=true`, `hard_blocking_contract_gap_count=0`.
  - 다음 액션: runtime threshold/order/provider/cap/bot/hard-safety 변경 없이 다음 PREOPEN/POSTCLOSE 산출물에서 verifier warning taxonomy를 확인한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-07-02 15:46:04`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-07-02.md`
- `Trade Review`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
