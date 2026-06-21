# 2026-06-22 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-06-19` postclose -> `2026-06-22`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0622] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-06-22`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-19.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 2026-06-22 확인 결과: 판정=`pass`, 다음 액션=`applied_guard_passed_env`. 근거: [threshold_cycle_preopen_2026-06-22.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-06-22.status.json) `status=succeeded`, [threshold_apply_2026-06-22.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-22.json) `status=auto_bounded_live_ready`, [threshold_runtime_env_2026-06-22.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-22.json) `selected_families=21`, `/proc/2280/environ`에서 `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`, `KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_FILE=.../scalp_sim_policy_catalog_2026-06-19.json`, `KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_POLICY_FILE=.../lifecycle_decision_matrix_2026-06-19.json` 로드 확인.

- [x] `[ActiveSeedLineageHandoff0622] active seed parent id 전파 및 PREOPEN handoff 확인` (`Due: 2026-06-22`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [key_lineage_ledger_2026-06-19.json](/home/ubuntu/KORStockScan/data/report/key_lineage_ledger/key_lineage_ledger_2026-06-19.json), [conversion_lane_2026-06-19.json](/home/ubuntu/KORStockScan/data/report/conversion_lane/conversion_lane_2026-06-19.json), [threshold_cycle_postclose_verification_2026-06-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-19.json), [threshold_apply_2026-06-22.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-22.json)
  - 판정 기준: 2026-06-19 postclose active seed catalog의 active seed ids가 2026-06-22 PREOPEN apply/runtime env manifest의 `active_sim_priority_seed_ids`로 소비됐는지 확인하고, 신규 intraday follow-up 이벤트에서 `active_seed_id`/`source_parent_bucket_id`가 유지되는지 확인한다.
  - 금지: active seed lineage 보완을 실주문, provider, cap, threshold, bot 변경 근거로 쓰지 않는다. 2026-06-19 raw event의 `unmatched 405`를 수동 소급 보정하지 않는다.
  - 다음 액션: `handoff_pass_lineage_preserved`, `handoff_pending_no_preopen_artifact`, `handoff_missing_fail`, `followup_parent_seed_missing_workorder`, `new_entry_taxonomy_or_natural_no_match_keep_collecting` 중 하나로 닫는다.
  - 2026-06-22 확인 결과: 판정=`warning`, 다음 액션=`new_entry_taxonomy_or_natural_no_match_keep_collecting`. 근거: [threshold_apply_2026-06-22.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-22.json) `scalp_sim_auto_approval.approved_request.active_sim_priority_seed_ids`에 10개 active seed가 handoff됐고, [scalp_sim_policy_catalog_2026-06-19.json](/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-06-19.json)에서 같은 seed들의 `source_parent_bucket_id`를 확인했다. 다만 [pipeline_events_2026-06-22.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-22.jsonl)와 [threshold_events_2026-06-22.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-06-22.jsonl)에는 아직 eligible `new_entry/followup` active-seed 이벤트가 없어서 runtime preservation은 미관측 상태다.

- [x] `[PreopenAutomationHealthCheck20260622] 장전 자동화체인 상태 확인` (`Due: 2026-06-22`, `Slot: PREOPEN`, `TimeWindow: 08:00~09:00`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [threshold_cycle_preopen_2026-06-22.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-06-22.status.json), [threshold_apply_2026-06-22.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-22.json), [threshold_runtime_env_2026-06-22.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-22.json), [logs/ensemble_scanner.log](/home/ubuntu/KORStockScan/logs/ensemble_scanner.log)
  - 판정 기준: runbook 장전 확인 절차의 preopen apply marker/status, swing recommendation freshness, selected family/runtime env, bot 기동 시각과 env handoff를 함께 확인한다.
  - 2026-06-22 확인 결과: 판정=`warning`, 다음 액션=`scanner_output_freshness_followup_required`. 근거: preopen apply와 bot 재기동은 정상이다. `threshold_cycle_preopen_2026-06-22.status.json` `status=succeeded`, preopen env 생성 시각 `07:35:01`, bot 기동 시각 [bot_history.log](/home/ubuntu/KORStockScan/logs/bot_history.log) `07:40:02`로 `pre_env_boot_gap` 징후는 없다. 반면 [ensemble_scanner.log](/home/ubuntu/KORStockScan/logs/ensemble_scanner.log)에는 `[DONE] final_ensemble_scanner target_date=2026-06-22 finished_at=2026-06-22T07:21:03`가 남았지만 [daily_recommendations_v2_diagnostics.json](/home/ubuntu/KORStockScan/data/daily_recommendations_v2_diagnostics.json) `latest_date=2026-06-19`, [daily_recommendations_v2.csv](/home/ubuntu/KORStockScan/data/daily_recommendations_v2.csv) 첫 행 `date=2026-06-18`로 freshness mismatch가 있다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0622] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-06-22`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-19.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, lifecycle_decision_matrix_runtime, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, weak_context_late_entry_guard_runtime가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0622] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-06-22`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-06-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-19.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0622] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-06-22`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-06-22.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-22.jsonl), [threshold_events_2026-06-22.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-06-22.jsonl), [observation_source_quality_audit_2026-06-22.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-22.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-06-22 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[PostcloseSourceQualityGateReview0622] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-06-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-06-22.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-22.json), [threshold_cycle_ev_2026-06-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-22.json), [code_improvement_workorder_2026-06-22.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-22.json), [threshold_cycle_postclose_verification_2026-06-22.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-22.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0622] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-06-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-19.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[EnsembleScannerOutputFreshnessGap0622] final_ensemble_scanner 완료 marker 대비 swing recommendation 산출물 freshness mismatch 원인 확인` (`Due: 2026-06-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:30`, `Track: RunbookOps`)
  - Source: [ensemble_scanner.log](/home/ubuntu/KORStockScan/logs/ensemble_scanner.log), [daily_recommendations_v2.csv](/home/ubuntu/KORStockScan/data/daily_recommendations_v2.csv), [daily_recommendations_v2_diagnostics.json](/home/ubuntu/KORStockScan/data/daily_recommendations_v2_diagnostics.json), [final_ensemble_scanner.py](/home/ubuntu/KORStockScan/src/scanners/final_ensemble_scanner.py), [recommend_daily_v2.py](/home/ubuntu/KORStockScan/src/model/recommend_daily_v2.py)
  - 판정 기준: `2026-06-22 07:21:03` DONE marker 이후에도 CSV/diagnostics가 `latest_date=2026-06-19`, CSV row date=`2026-06-18`로 남은 이유가 거래일 기준 정상인지, 산출물 write 누락인지, 후속 overwrite 누락인지 분리한다.
  - 금지: 원인 미분리 상태에서 stale recommendation 산출물을 정상 장전 입력으로 간주하지 않는다.
  - 다음 액션: `expected_trading_day_lag`, `artifact_write_missing_bug`, `post_write_overwrite_bug`, `consumer_contract_mismatch` 중 하나로 닫고, 필요 시 Codex 구현 지시 또는 runbook follow-up을 연결한다.
  - 추적 메모 (`2026-06-22 08:08 KST`): `latest_date=2026-06-19` 자체는 `src/model/common_v2.py:get_latest_quote_date()`와 `data/runtime/update_kospi_status/update_kospi_2026-06-19.json` 기준 정상 trading-day lag다. 실제 이슈는 `data/daily_recommendations_v2.csv`만 `2026-06-19 20:41:17 KST`에 `date=2026-06-18` 내용으로 단독 갱신된 점이다. `recommend_daily_v2.py`는 recommendation CSV와 diagnostics CSV/JSON을 같은 save path에서 함께 쓰므로 정상 성공 경로라면 이 불일치가 생길 수 없다. `final_ensemble_scanner.py`는 해당 CSV consumer일 뿐 writer가 아니다. `crontab -l`, `/var/log/syslog.1` `2026-06-19 20:35~20:42`, `deploy/` wrapper search 기준 같은 시각 repo 내 정상 writer/restore cron은 확인되지 않았고, `20:35~20:41`에는 `daily_recommendations_v2.csv`와 일부 postclose markdown만 `ubuntu:ubuntu` 소유로 갱신됐다. 현재 판정 후보는 `post_write_overwrite_bug`이며, repo 밖 out-of-band overwrite 또는 별도 백그라운드 프로세스 개입 가능성이 높다.

- [ ] `[NegativeEVRegimeAttribution0622] 전일 음수 EV의 market regime/bucket/policy 원인 분해` (`Due: 2026-06-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~16:55`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-06-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-19.json), [lifecycle_decision_matrix_2026-06-19.json](/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-19.json), [lifecycle_bucket_discovery_2026-06-19_mtd.json](/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-19_mtd.json), [tuning_performance_control_tower_2026-06-19.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-06-19.json)
  - 판정 기준: 전일 음수 EV를 `broad_market_regime`, `specific_parent_bucket`, `submit_drought`, `holding_exit_policy`, `source_quality_or_sample_floor` 중 어디에 귀속할지 rolling/MTD parent bucket 기준으로 분해한다.
  - 금지: 하락장 전체 sim EV만 보고 live-auto 차단, threshold 완화/강화, broker/order/provider/cap/bot 변경을 결정하지 않는다. daily-only child bucket 또는 thin sample을 live authority로 쓰지 않는다.
  - 다음 액션: `broad_market_primary_hold_sample`, `specific_bucket_blocker_review`, `submit_drought_followup`, `holding_exit_policy_review`, `sample_floor_or_source_quality_keep_collecting` 중 하나로 닫고, 필요 시 다음 checklist/workorder로 분리한다.

- [ ] `[CodeImprovementWorkorderReview0622] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-06-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:55~17:10`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-06-19.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-06-19.md), [code_improvement_workorder_2026-06-19.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-19.json)
  - 판정 기준: selected_order_count=125와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0622] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-06-22`, `Slot: POSTCLOSE`, `TimeWindow: 17:10~17:25`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-06-19.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-19.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[RuntimeApplyGapDirectiveReview0622] runtime apply gap Codex 작업지시 표면화 및 구현 여부 확인` (`Due: 2026-06-22`, `Slot: POSTCLOSE`, `TimeWindow: 17:25~17:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-06-19.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-19.json), [runtime_apply_gap_audit_2026-06-19.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-19.md), [runtime-apply-gap-audit-user-guide.md](/home/ubuntu/KORStockScan/docs/runtime-apply-gap-audit-user-guide.md)
  - 판정 기준: runtime apply gap audit의 Codex 작업지시 `IMPLEMENT_SCALE_IN_POLICY_CONTRACT`:scale_in_bucket_runtime_policy_v1:2026-06-19(block=env_mapping_contract)를 구현 필요, 이미 해결, 설계 보류, reject로 분류한다.
  - 금지: 작업지시를 approval artifact나 즉시 runtime env 수정으로 해석하지 않는다. broker/order/provider/cap guard 우회와 장중 threshold mutation은 금지한다.
  - 다음 액션: `implement_now`, `already_implemented`, `defer_design`, `reject`, `needs_new_workorder` 중 하나로 닫고, 구현 시 테스트와 postclose verifier handoff를 같이 확인한다.

- [ ] `[AutomationTriggerDecisionSummary0622] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-06-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:10~18:25`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-06-19.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-06-19.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`16`, run_count=`15`, skip_count=`1`, source_missing_count=`0`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`scalp_sim_ai_deferred_review`, top_reasons=`upstream_drift_signal:14, upstream_artifact_newer:8, fresh_outputs_no_trigger:1, output_missing_or_unreadable:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->


## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
