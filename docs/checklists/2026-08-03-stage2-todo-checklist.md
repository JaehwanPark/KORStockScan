# 2026-08-03 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-07-31` postclose -> `2026-08-03`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0803] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-08-03`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-31.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다. 고효용 entry 보강은 clean baseline cumulative evidence를 담은 `single_cumulative_quality_update` 계약과 `max_runtime_apply_count=1`을 충족하는 `entry_opportunity_recheck_runtime` 최대 1건만 신규 runtime 품질갱신으로 인정한다. 해당 runtime은 canonical `EDGE/WAIT/recovery_required/eligible_wait_probe`와 fresh strong micro가 일치할 때만 1주 probe를 허용하고, probe-first active date·qty=1·post-probe resolver 의존성이 없으면 적용하지 않는다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict, cumulative 계약 누락/불일치, 복수 entry 품질갱신 후보를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0803] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-08-03`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-07-31.json), [code_improvement_workorder_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-31.json), [threshold_apply_2026-08-03.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-03.json), [threshold_runtime_env_2026-08-03.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-03.json), [threshold_runtime_env_verify_2026-08-03.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-08-03.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder`의 forced scout 대비 post-sell outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0803] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-08-03`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-31.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, entry_split_order_plan, scale_in_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26가 runtime event provenance에 찍히는지 확인한다.
  - 누적 품질 갱신 기준: PYRAMID/AVG_DOWN 고효용 calibration은 clean-baseline `single_cumulative_quality_update` 중 최대 1건만 선택하고, `scale_in_split_order_plan`과 후단 real-pyramid 보호장치는 유지하며 post-apply attribution이 없는 후보는 fail-closed한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0803] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-08-03`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-31.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다. one-share source는 미적격 skip을 intent로 세지 않고 actual submit/probe-first/split bundle·variant/post-sell join을 분리하며, probe-first submit 이후 `residual_submitted` 이벤트와 `residual_not_submitted` terminal outcome을 record lineage로 결합해 누적 및 `target_date_probe_to_residual` 각각의 `observed|no_natural_sample|instrumentation_gap`, resolution coverage, submitted/blocked/not-submitted/unresolved 건수를 확인한다. terminal outcome 도입 전 artifact는 `residual_blocked + phase=aborted + residual_submitted 미관측`인 경우만 `legacy_aborted_phase_fallback`으로 복원하고 source count를 분리한다. 과거 instrumentation gap을 당일 표본 결함으로 간주하지 않는다. Entry ADM은 평가 원천 underproduction과 join-contract gap을 분리하고, overnight는 `observed|no_natural_sample|instrumentation_gap`을 gzip artifact까지 포함해 판정한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0803] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-08-03`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-03.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-03.jsonl), [threshold_events_2026-08-03.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-03.jsonl), [observation_source_quality_audit_2026-08-03.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-03.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-08-03 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[EntryAiGateCumulativeSourceJoin0803] entry AI 누적 품질갱신 source join 및 손상일 provenance 보완` (`Due: 2026-08-03`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~20:25`, `Track: ScalpingLogic`)
  - Source: [entry_ai_gate_backtest_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/entry_ai_gate_backtest/entry_ai_gate_backtest_2026-07-31.json), [entry_ai_gate_backtest.py](/home/ubuntu/KORStockScan/src/engine/scalping/entry_ai_gate_backtest.py), [missed_entry_counterfactual_2026-07-27.json.gz](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/missed_entry_counterfactual_2026-07-27.json.gz)
  - 판정 기준: clean baseline 누적 replay에서 missed-entry counterfactual을 동일 `record_id`/candidate lineage의 entry decision snapshot과 결합해 canonical AI action, fresh tick/micro-VWAP, source-quality provenance를 복원한다. producer별 실제 소비일과 의도한 trading-day window를 분리하고, JSON 손상·artifact missing 날짜는 누적 source count에서 제외 사유와 함께 표면화한다. Entry ADM의 `entry_price_skip_followup_cumulative`은 exact same-symbol lineage로 결합된 finite 90초 MFE/MAE가 20건 이상일 때만 offline counterfactual 재검토 준비로 판정하며, 해당 상태만으로 runtime apply나 실현 EV를 승인하지 않는다. 결합 가능한 원천이 없으면 0표본을 전략 부재가 아니라 `source_contract_not_evaluable`로 닫는다.
  - 금지: score-only diagnostic EV, action/micro provenance가 없는 counterfactual, 손상 artifact를 `entry_opportunity_recheck_runtime` 적용 근거로 사용하지 않는다. hard safety, stale/quote, broker/account/order/quantity/cooldown, provider, bot, cap을 변경하거나 우회하지 않는다.
  - 다음 액션: `joined_replay_apply_candidate_0_or_1`, `source_contract_not_evaluable`, `corrupt_date_excluded_with_provenance`, `source_quality_blocked`, `needs_producer_patch` 중 하나로 닫는다.

- [ ] `[PostcloseSourceQualityGateReview0803] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-08-03`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-08-03.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-03.json), [threshold_cycle_ev_2026-08-03.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-03.json), [code_improvement_workorder_2026-08-03.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-03.json), [threshold_cycle_postclose_verification_2026-08-03.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-03.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0803] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-08-03`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-31.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다. wrapper에서 OFF인 swing/deep-audit source는 `warning_contract.disabled_not_applicable`로 분리되고, active warning은 중복 제거된 required-missing/quality warning만 남는지 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0803] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-08-03`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-31.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0803] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-08-03`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-07-31.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-31.md), [code_improvement_workorder_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-31.json)
  - 판정 기준: 최신 재생성 산출물의 selected order와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, `duplicate_order_warnings=[]`이며 모든 `handoff_closed_root_cause_open` order에 non-null `root_cause_followup_contract.root_cause_signal`, `acceptance_test`, `next_repair_action`, `implementation_only_closure_allowed=false`가 있는지 검증한다. `threshold_cycle_postclose_verification.code_improvement_workorder_contract.status=pass`, `contract_state=declared_and_verified`, required/complete count 일치도 함께 확인한다. 비-implement 반복 항목은 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0803] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-08-03`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-31.json), [runtime_apply_gap_audit_2026-07-31.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-31.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`245`, rollup_required_count=`245`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 244}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0803] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-08-03`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-07-31.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-07-31.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`16`, run_count=`15`, skip_count=`1`, source_missing_count=`7`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`scalp_sim_ai_deferred_review`, top_reasons=`output_missing_or_unreadable:11, source_missing_or_unreadable:7, upstream_drift_signal:7, upstream_artifact_newer:4, fresh_outputs_no_trigger:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 2026-08-01 코드 정리: 위 수치는 2026-07-31 산출물의 역사적 실행 결과다. 소비자가 없던 `scalp_sim_ai_deferred_review` step과 actionable 후속 소비자가 없던 standalone `quote_consistency_report`는 producer/wrapper/verifier에서 제거됐으므로 다음 postclose부터 total step, skip sample, DONE marker 및 verifier artifact status에서 제외한다. sim AI budget-manager의 deferred runtime event와 실주문 안전용 `quote_consistency_normalization`은 유지한다. 기존 quote-consistency report 산출물은 archive evidence로만 취급한다.
  - 2026-08-01 후속 정리: source-only `limit_down_watch` runtime observer가 기본 OFF인 동안 report만 기본 ON으로 실행돼 빈 `source_blocked` 산출물을 만들던 불일치를 제거했다. 다음 postclose부터 report 기본값은 상속된 `KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED=ON` 또는 대상일 candidate-source 파일 존재를 따르고, `THRESHOLD_CYCLE_RUN_LIMIT_DOWN_WATCH_REPORT` 명시값이 자동 판정보다 우선한다. 이로써 postclose cron이 PREOPEN env를 상속하지 않는 경우에도 실제 observer 표본을 누락하지 않는다. observer/report가 모두 OFF이고 source도 없는 경우 DONE marker의 `limit_down_watch_report=false`와 verifier disabled 상태를 정상으로 판정한다.
  - 2026-08-01 성능 보완: 2026-07-31 raw 4.37GB 중 고빈도 diagnostic event가 약 90%를 차지하고 raw-derived parity summary가 322MB까지 증가한 병목을 분리했다. `producer_parity` 산출물은 `counts_only_v1`로 축소하고, 대형 Entry ADM/lifecycle bucket/latency CLI의 postclose stdout은 compact summary만 남긴다. 수정 코드로 2026-07-31 실데이터를 재생성한 결과 49,655 bucket과 364,634 원천 event count는 보존됐고 산출물은 337,590,650 bytes에서 35,499,217 bytes(33.85MiB)로 89.48% 감소했다. 상태는 기존과 같은 `v2_shadow_partial_coverage`, `suppress_eligibility=false`, `raw_suppression_enabled=false`다. `pipeline_event_verbosity`는 raw/producer/code input보다 검증된 JSON/Markdown이 새로울 때만 recovery rerun에서 skip한다. raw suppression은 2영업일 이상 parity 승인 전까지 OFF이며 실주문·threshold·provider·bot 권한 변화는 없다. 다음 postclose 판정은 wrapper log 단일행 크기와 pipeline report `[SKIP]` marker 또는 재생성 사유를 추가 확인한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
