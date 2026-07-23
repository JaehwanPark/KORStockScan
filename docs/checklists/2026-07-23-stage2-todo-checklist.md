# 2026-07-23 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-07-22` postclose -> `2026-07-23`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0723] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-07-23`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-22.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 08:40 조기 관측: PID `10557`은 07:55:01 KST 시작 후 생존했고 PREOPEN runtime env verify는 pass였다. 관측 종료 전 표본은 모두 `PREMARKET_KRX_LIKE`여서 KRX 정규장 EV·threshold 판단에는 사용하지 않았으며, 이 시점에는 원래 TimeWindow 항목을 미완료로 유지했다.
  - 최종 판정: `applied_guard_passed_env`. 08:47:39 KST 재기동 후 PID `41693` 기준 verify `passed=true`, `pid_passed=true`, missing/mismatch 0건을 확인했다.

- [x] `[RisingMissedScoutRuntimePreopen0723] rising_missed_scout_workorder 구현분 다음 장전 runtime 반영 여부 확인` (`Due: 2026-07-23`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-07-22.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-07-22.json), [rising_missed_normal_buy_bridge_candidate_discovery_2026-07-22.json](/home/ubuntu/KORStockScan/data/report/rising_missed_normal_buy_bridge_candidate_discovery/rising_missed_normal_buy_bridge_candidate_discovery_2026-07-22.json), [code_improvement_workorder_2026-07-22.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-22.json), [threshold_apply_2026-07-23.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-23.json), [threshold_runtime_env_2026-07-23.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-23.json), [threshold_runtime_env_verify_2026-07-23.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-23.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`4`, forced_scout_with_post_sell_count=`16`, profitable_forced_scout_count=`7`, loss_or_flat_forced_scout_count=`9`, current_missed_count=`0`)과 `rising_missed_normal_buy_bridge_candidate_discovery` 요약(status=`source_missing`, bridge_candidate_count=`0`, code_improvement_order_count=`0`, runtime_env_key=`KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED`)을 함께 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder`/bridge discovery 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.
  - 08:40 조기 관측: KRX-like 실주문에서 중앙 5단계 배분, 1주 probe-first, residual multi-leg/reprice, 최초 tier 재사용을 확인했다. 08:47:39 KST 사용자 승인 graceful restart 후 source provenance 및 reversal recheck dedup 보완이 PID `41693`에 반영됐고, runtime env PID verify는 pass(누락·불일치 0건)였다. 로드 provenance는 commit `7c4928a7c499559f4930e1b5461853711083af3f`, `source_dirty=true`다.
  - 최종 판정: `runtime_env_reflected_and_verified`. 새 supervisor까지 재기동해 수정된 `run_bot.sh` 함수 정의와 Python source를 함께 반영했다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0723] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-07-23`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-22.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, entry_split_order_plan, scale_in_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0723] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-07-23`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-07-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-22.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0723] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-07-23`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-07-23.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-23.jsonl), [threshold_events_2026-07-23.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-23.jsonl), [observation_source_quality_audit_2026-07-23.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-23.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-07-23 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0723] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-07-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-07-23.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-23.json), [threshold_cycle_ev_2026-07-23.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-23.json), [code_improvement_workorder_2026-07-23.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-23.json), [threshold_cycle_postclose_verification_2026-07-23.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-23.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0723] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-07-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-07-22.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-07-22.json), [threshold_cycle_ev_2026-07-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-22.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0723] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-07-23`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-22.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0723] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-07-23`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-07-22.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-22.md), [code_improvement_workorder_2026-07-22.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-22.json)
  - 판정 기준: selected_order_count=175와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0723] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-07-23`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-07-22.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-22.json), [runtime_apply_gap_audit_2026-07-22.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-22.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`223`, rollup_required_count=`223`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 222}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0723] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-07-23`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-07-22.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-07-22.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`16`, run_count=`16`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, scalp_sim_ai_deferred_review, pattern_lab_currentness_audit`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:15, source_missing_or_unreadable:7, upstream_drift_signal:7, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

- [x] `[GeumhoEntryTrailingDefectHotfix0723] 금호건설 진입·probe 확대·트레일링 청산 결함 보완 및 장중 재기동` (`Due: 2026-07-23`, `Slot: INTRADAY`, `TimeWindow: 09:50~15:20`, `Track: ScalpingLogic`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [exit_safety_monitor.py](/home/ubuntu/KORStockScan/src/engine/scalping/exit_safety_monitor.py), [operator_runtime_overrides_2026-07-23.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/operator_runtime_overrides_2026-07-23.env)
  - 판정 기준: fresh DROP BUY 제출 0회, fresh WAIT 1주 probe 후 250ms 간격 2회 강확인에서만 첫 잔량 leg 허용, BUY probe 기존 확대 유지, fast exit 단일 token 및 `decision_to_order_sent_ms<=500`, 부분익절 정책 불변, review gate 지적 0건과 표적 테스트 통과 후 graceful restart 및 새 PID env 확인.
  - 금지: BUY 코호트 NEUTRAL 확대 차단, trailing/hard/protect/emergency 수치 변경, stale/broker/account/order/quantity/cooldown guard 우회, 부분익절 0.35/+0.55%/210초 변경.
  - Rollback: entry와 holding/exit 일자축을 각각 false로 전환하고 review gate 후 graceful restart한다.
  - 완료 결과: `$korstockscan-review-gate` 미해결 지적 0건, 관련 회귀 988건과 추가 수동관리 제외 표적 46건, compile/shell/location/parser/diff 검증을 통과했다. 최초 PID `127918`에서 monitor가 수동관리 제외 보유분을 stale REST 재검증하는 권한 누수를 첫 이벤트로 발견해 매도 없이 즉시 보완했고, corrective graceful restart 후 PID `130148`에서 entry/exit 축과 기존 부분익절 KRX/NXT policy를 재확인했다.
  - 재기동 후 첫 monitor 이벤트: `manual_control_fast_exit_monitor_blocked`(950160) 1회이며 이후 stale REST 반복, 중복/초과 주문, monitor 예외, fast-exit SELL은 0건이다. 자연 발생 DROP/WAIT/probe/trailing 표본은 장후 귀속 항목에서 계속 확인한다.
  - 11:04 venue 보완: `PREMARKET_KRX_LIKE`를 관측 cohort, `NXT`를 실제 broker route로 분리하고 fast-exit IOC에 `dmst_stex_tp`를 명시 전달한다. KRX-only 종목, entry cohort/route 충돌, 실제 NXT 0D 또는 NXT suffix REST provenance 결손은 exit token 선점 전에 차단한다. 단, 같은 position cycle이 `HOLDING + buy_qty>0 + entry_execution_broker_route=NXT`로 확인되면 stale DB `is_nxt=false`보다 실제 진입 route를 우선하여 청산 불능을 방지한다.
  - venue 보완 적용 상태: source 및 회귀 검증 대상이며 PID `130148`에는 아직 재반영하지 않았다. 본 요청 범위에는 추가 재기동이 포함되지 않으므로 review gate가 닫혀도 bot state는 유지한다.
  - venue 보완 review gate: NXT route 미명시, 확인된 NXT 체결 포지션의 stale DB 오차, 250ms monitor의 불필요한 DB 조회, legacy 3-인자 exit callback 호환성 지적을 모두 보완했다. 최종 관련 회귀 985건, compile, checklist parser, `git diff --check` 통과 후 미해결 지적 0건으로 닫는다.
  - 11:11 사용자 지시 재기동: 표준 `./restart.sh` graceful 경로로 PID `130148 -> 147049` 교체, `restart.flag` 소모, runtime env verify `passed=true`, `pid_passed=true`, missing/mismatch 0건을 확인했다. 새 PID env에는 fresh DROP/WAIT action guard, 250ms fast-exit guard와 기존 KRX/NXT 부분익절 policy가 동일하게 로드됐고, 재기동 후 첫 monitor 이벤트는 수동관리 제외 종목 `950160`의 `manual_control_fast_exit_monitor_blocked`로 주문 없이 닫혔다.

- [x] `[NormalWinnerExpansionAttribution0723] probe-only 정상 승자 확대 후보 및 제출 병목 순증분 EV 관측 보완` (`Due: 2026-07-23`, `Slot: INTRADAY`, `TimeWindow: 13:20~14:25`, `Track: ScalpingLogic`)
  - Source: [scalping_pyramid_intraday_feedback.py](/home/ubuntu/KORStockScan/src/engine/monitoring/scalping_pyramid_intraday_feedback.py), [scalping_pyramid_quality_calibration.py](/home/ubuntu/KORStockScan/src/engine/monitoring/scalping_pyramid_quality_calibration.py), [buy_funnel_sentinel.py](/home/ubuntu/KORStockScan/src/engine/buy_funnel_sentinel.py), [sniper_missed_entry_counterfactual.py](/home/ubuntu/KORStockScan/src/engine/sniper_missed_entry_counterfactual.py)
  - 판정 기준: 1주 probe 뒤 잔량 미체결 경로에서 최초 양수 PYRAMID 평가 시점을 확대 후보 기준으로 고정하고, 이후 SELL까지 거래비용 0.23% 차감 순증분 MFE/MAE/최종손익, 미체결 잔량 기준 후보 notional, probe 확인 연속성, AI/pressure/tick/micro/blocker를 함께 귀속한다. KRX/NXT와 market session은 explicit conflict-free provenance로 분리하며 rolling closed valid 표본 20건 전에는 실주문 권한을 만들지 않는다.
  - 완료 결과: 당일 KRX closed valid 후보 3건 중 순증분 승자 1건(LG전자), 정상 미확대·반전 2건으로 분리됐다. 거래비용 차감 `notional_weighted_ev_pct=-0.4995%`, `diagnostic_win_rate=0.3333`이므로 현 시점의 광범위 잔량 확대는 부적합하다. 다만 LG전자의 순증분 최종손익 `+0.0989%` 경로를 최초로 독립 표면화했고, 모든 당일 후보가 probe 단계에서 negative group을 경험했다는 확인 서명까지 남겼다.
  - 권한/금지: 신규 관측은 `runtime_effect=false`, `allowed_runtime_apply=false`, `decision_authority=source_only_*`이며 source-quality·provenance 결손 행은 rolling 입력에서 제외한다. 일일 feature bucket이나 공통 venue EV만으로 잔량 제출, threshold/env 변경, cap/quantity 완화, broker/order guard 우회를 열지 않는다.
  - Rollback: schema v2 소비를 중단하고 기존 `one_share_pyramid_opportunity_rows` 기반 calibration으로 되돌린다. 주문·threshold·provider·bot 상태에는 직접 변경이 없어 runtime rollback은 없다.
  - 14:27 사용자 지시 재기동: 표준 `./restart.sh` graceful 경로로 PID `253705 -> 292381` 교체, `restart.flag` 소모, runtime env verify `passed=true`, `pid_passed=true`, missing/mismatch 0건을 확인했다. 새 PID에는 fresh DROP/WAIT action guard, 250ms fast-exit guard와 KRX/NXT 조기 부분익절 policy가 로드됐으며 양 policy의 `partial_ratio=0.35`, `target_net_profit_pct=0.55`, `ttl_sec=210`이 유지됐다.

- [ ] `[GeumhoEntryTrailingPostcloseAttribution0723] 진입 veto·WAIT probe·fast-exit 장후 귀속 및 다음 PREOPEN 영구화 판단` (`Due: 2026-07-23`, `Slot: POSTCLOSE`, `TimeWindow: 16:35~16:50`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-07-23.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-23.jsonl), [threshold_events_2026-07-23.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-23.jsonl)
  - 판정 기준: fresh DROP 차단 수, WAIT probe 확대/폐기, BUY probe 기존 확대, 중복·초과 주문, `decision_to_order_sent_ms`, 실제 체결 손익과 source quality를 분리 귀속하고 다음 PREOPEN 영구 활성화 또는 rollback 후보를 기록한다.
  - 금지: 당일 단일 표본만으로 threshold/provider/cap/broker guard를 변경하거나 부분익절 정책의 효과를 합산하지 않는다.


## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
