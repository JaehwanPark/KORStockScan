# 2026-08-13 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime 변경은 사용자 명시 지시가 있을 때만 기존 `bounded_tunable` 단일 축에 한해 허용한다. fresh/conflict-free source, 유효 effective price, 단일 blocker 인과, same-stage owner 비충돌, before/after·PID/env provenance·rollback·즉시 attribution을 모두 남긴다. hard safety, stale/conflict, price freshness, broker/account/order/quantity/cooldown, provider, bot, cap, 요청수량은 변경하거나 우회하지 않는다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-05`, `clean_tuning_baseline_ts_kst=2026-06-05T00:00:00+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.
- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-08-12` postclose -> `2026-08-13`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0813] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-08-13`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-12.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0813] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-08-13`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-08-12.json), [code_improvement_workorder_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-12.json), [threshold_apply_2026-08-13.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-13.json), [threshold_runtime_env_2026-08-13.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-13.json), [threshold_runtime_env_verify_2026-08-13.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-08-13.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`1`, forced_scout_with_post_sell_count=`0`, post_sell_join_coverage_pct=`0`, outcome_coverage_state=`no_closed_outcome`, profitable_forced_scout_count=`0`, loss_or_flat_forced_scout_count=`0`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[EmbeddedHypothesisCleanBaselineGate0813] embedded 가설 관측계획 clean-baseline 소비 가드 구현·리뷰` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 08:00~15:20`, `Track: RuntimeStability`)
  - Source: [source_quality_clean_baseline.py](/home/ubuntu/KORStockScan/src/engine/automation/source_quality_clean_baseline.py), [scalp_sim_auto_approval_control_tower.py](/home/ubuntu/KORStockScan/src/engine/scalping/scalp_sim_auto_approval_control_tower.py), [sim_auto_approval_control_tower.py](/home/ubuntu/KORStockScan/src/engine/swing/sim_auto_approval_control_tower.py), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py)
  - 구현 결과: scalp/swing sim policy catalog는 target date 이하의 가설 관측계획을 최신순으로 탐색하되 `source_report_date>=2026-06-05`인 첫 artifact만 포함한다. runtime policy loader와 PREOPEN manifest/handoff 검증은 pre-baseline·누락·비정상 embedded evidence를 소비하지 않으며 provenance gate를 보존한다.
  - 권한 경계: source-quality/sim policy 소비 가드이며 실주문·수량·provider·threshold 권한을 추가하지 않는다. `runtime_effect=false`인 hypothesis evidence만 대상으로 하고, invalid embedded plan은 archive-only 또는 runtime-policy unusable로 fail-closed한다.

- [x] `[SamsungWidgetWebSocketPriceComparison0813] 삼성 위젯 기존가·WS 0B 현재가 2초 비교 관측 구현·리뷰` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 08:00~15:20`, `Track: RuntimeStability`)
  - Source: [samsung_price_widget.py](/home/ubuntu/KORStockScan/tools/windows/samsung_price_widget.py), [samsung_price_widget_routes.py](/home/ubuntu/KORStockScan/src/web/samsung_price_widget_routes.py), [kiwoom_websocket.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py), [키움 API 데이터 계약](/home/ubuntu/KORStockScan/docs/kiwoom-api-data-contract.md)
  - 구현 결과: 기존 10초 collector/REST 표시가와 공유 Kiwoom WebSocket `0B` 체결 현재가를 분리해 `WS/KRX|NXT|SOR`, 가격차, 수신 경과시간을 2초 Windows 주기로 표시한다. WS dashboard bridge는 1초 상한이며 5초 stale, source/item/timestamp/authority 불일치는 `WS: 수신 대기`로 fail-closed한다.
  - 권한 경계: `widget_ws_price_comparison_only`, `runtime_effect=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`, `used_for_manual_order=false`이며 큰 표시가·수동주문 가격검증·수량·제출은 기존 collector snapshot만 사용한다. 비교전용 삼성 SOR item `005930_AL` 하나만 거래 WS item budget에서 제외하여 기존 거래 구독을 대체하지 않고, 비활성 target prune/REMOVE에서 유지한다. 같은 종목의 KRX/NXT 등 비고정 route는 정상 예산·REMOVE 대상이다.
  - Official reference gate: upstream `Kiwoom-Securities/Kiwoom-REST-API` SHA `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`, retrieval `2026-08-13T08:00:25+09:00`; `kiwoom_docs/실시간시세.md`, `kiwoom/realtime/packets.py`, `kiwoom/realtime/{events,decoders,schemas,stream}.py`, `kiwoom/core/ws_client.py`, Postman의 `REG/REMOVE`, `refresh=1`, `0B` FID 10/20, KRX/NXT/SOR suffix를 검증했다.
  - 반영 상태 (`2026-08-13 08:10~08:11 KST`): 사용자의 명시적 승인 후 Gunicorn master `635`를 유지하고 worker `935/977 -> 31103/31105`를 HUP 교체했다. 표준 `restart.flag` 경로로 main bot PID `22015 -> 31454`를 graceful 재기동했고 flag 소비, tmux `bot` active, PREOPEN runtime env verify `status=pass`, `pid_passed=true`, finding/runtime-policy/dated-override/unverified family=`0`-을 확인했다. 신규 PID는 `005930_AL` REG source=`sniper_boot_priority_and_widget_observation_ws_budget`로 고정 구독했고 1초 dashboard에 fresh `0B` tick을 남겼다. 인증 API 실관측은 primary `266,500원`, WS/SOR `266,000원`, delta `-500원`, age `882ms`, `runtime_effect=false`, `used_for_manual_order=false`였다. 독립 삼성 morning/add-on 기계와 widget auto trader service는 모두 active를 유지했으며 주문·threshold·provider는 변경하지 않았다. Windows 2초 UI는 신규 파일 재설치 후 표시된다.

- [ ] `[RuntimeEnvIntradayObserve0813] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-12.json)
  - 전일 postclose candidate_selected_families=entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0813] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-12.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0813] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-13.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-13.jsonl), [threshold_events_2026-08-13.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-13.jsonl), [observation_source_quality_audit_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-13.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-08-13 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0813] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-08-13`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-13.json), [threshold_cycle_ev_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-13.json), [code_improvement_workorder_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-13.json), [threshold_cycle_postclose_verification_2026-08-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-13.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0813] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-08-13`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-08-12.json), [threshold_cycle_ev_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-12.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0813] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-08-13`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-12.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0813] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-08-13`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-08-12.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-08-12.md), [code_improvement_workorder_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-12.json)
  - 판정 기준: selected_order_count=55와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0813] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-08-13`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-12.json), [runtime_apply_gap_audit_2026-08-12.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-12.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`254`, rollup_required_count=`254`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 253}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0813] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-08-13`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-08-12.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-08-12.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`9`, skip_count=`0`, source_missing_count=`4`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:8, disabled_by_runtime_policy:5, upstream_drift_signal:5, source_missing_or_unreadable:4, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->



## 독립시간대 매매기계

- [ ] `[SamsungMorningManualAddon1000813] 삼성전자 morning 오늘 한정 100주 수동매도용 추가 BUY 실행·귀속 확인` (`Due: 2026-08-13`, `Slot: PREOPEN`, `TimeWindow: 07:57~09:35`, `Track: RuntimeStability`)
  - Source: [manual_addon.py](/home/ubuntu/KORStockScan/src/trading/samsung_morning_one_share/manual_addon.py), [exact-date timer](/home/ubuntu/KORStockScan/deploy/systemd/korstockscan-samsung-morning-manual-addon-20260813.timer), [Kiwoom contract](/home/ubuntu/KORStockScan/docs/kiwoom-api-data-contract.md)
  - 실행: 사용자 명시 지시에 따라 `2026-08-13`에만 기존 morning BUY leg의 route·가격을 따라 50주씩 2개, 최대 100주를 별도 원장으로 주문한다. 기존 1주×2 episode 주문과 자동 +2호가 목표는 변경하지 않는다.
  - 판정: normal morning source order가 broker 접수되고 source episode/leg가 아직 active인 경우에만 mirror하며, terminal/completed source의 지연 추종은 금지한다. add-on exact-order fill/remainder와 NXT 취소 후 SOR 잔량 이동을 대사한다. 체결수량은 `manual_sell_required_quantity`로 기록하고 기계 SELL은 금지한다.
  - 금지: add-on target/stop/강제청산, 자동매도, 100주 초과, 기존 episode/widget/main-bot 주문 취소·매도, 다른 날짜 재실행, source order 이전 선행 주문을 허용하지 않는다.

- [ ] `[EpisodeMachineExpandedProfileFirstPreflight0813] 13-profile 첫 PREOPEN 실기동 검증` (`Due: 2026-08-13`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:15`, `Track: RuntimeStability`)
  - Source: [tracked evidence projection](/home/ubuntu/KORStockScan/data/config/low_price_two_leg_expanded_profile_evidence_2026-08-12.json), [installer](/home/ubuntu/KORStockScan/deploy/install_low_price_two_leg_systemd.sh), [runbook](/home/ubuntu/KORStockScan/docs/low-price-two-leg-machines.md)
  - 선행 실행 완료 (`2026-08-12 22:30 KST`): 사용자 지시에 따라 reviewed installer로 13-profile 26개 timer와 2개 template unit을 설치·활성화했다. 설치본은 tracked source와 일치하고 active profile service는 `0`이라 소급 실주문이 없으며, 카카오·한국전력 owner는 `manual_operator`로 분리됐다. 다음 session dry-run은 13-profile candidate hash `aa066f3c84db7abad3421ee35bae6a26a792e140cc098a441601c4496ab3cd30`을 통과했고 exact-date applied artifact는 첫 09:05 preflight가 생성하도록 유지했다. main bot은 crontab 기준 07:55 기동되어 첫 preflight보다 앞선다.
  - 판정: 신규 여섯 preflight의 frozen evidence·shared token·main bot active·manual owner·exact applied hash가 모두 통과하고, 각 service가 자기 profile/state/authority/order ledger만 읽는 경우에만 예약 기동을 인정한다. 설치 전이거나 blocker가 있으면 실주문 없이 `not_installed_or_fail_closed`로 남긴다.
  - 금지: 리뷰 미종료 상태의 설치, 장전 window를 지난 소급 기동, report 원본 누락 우회, widget/다른 episode 원장 사용, 손절·target timeout·강제청산, 수량·provider·bot·cap·broker guard 변경을 허용하지 않는다.


## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
