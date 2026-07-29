# 2026-07-29 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime 변경은 사용자 명시 지시가 있을 때만 기존 `bounded_tunable` 단일 축에 한해 허용한다. fresh/conflict-free source, 유효 effective price, 단일 blocker 인과, same-stage owner 비충돌, before/after·PID/env provenance·rollback·즉시 attribution을 모두 남긴다. hard safety, stale/conflict, price freshness, broker/account/order/quantity/cooldown, provider, bot, cap, 요청수량은 변경하거나 우회하지 않는다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-04`, `clean_tuning_baseline_ts_kst=2026-06-04T14:29:09+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.
- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-07-28` postclose -> `2026-07-29`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0729] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-07-29`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-28.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0729] rising_missed_scout_workorder 구현분 다음 장전 runtime 반영 여부 확인` (`Due: 2026-07-29`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-07-28.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-07-28.json), [rising_missed_normal_buy_bridge_candidate_discovery_2026-07-28.json](/home/ubuntu/KORStockScan/data/report/rising_missed_normal_buy_bridge_candidate_discovery/rising_missed_normal_buy_bridge_candidate_discovery_2026-07-28.json), [code_improvement_workorder_2026-07-28.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-28.json), [threshold_apply_2026-07-29.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-29.json), [threshold_runtime_env_2026-07-29.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-29.json), [threshold_runtime_env_verify_2026-07-29.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-29.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`4`, forced_scout_with_post_sell_count=`12`, profitable_forced_scout_count=`7`, loss_or_flat_forced_scout_count=`5`, current_missed_count=`0`)과 `rising_missed_normal_buy_bridge_candidate_discovery` 요약(status=`source_missing`, bridge_candidate_count=`0`, code_improvement_order_count=`0`, runtime_env_key=`KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED`)을 함께 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder`/bridge discovery 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0729] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-07-29`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-28.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, scale_in_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0729] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-07-29`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-07-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-28.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0729] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-07-29`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-07-29.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-29.jsonl), [threshold_events_2026-07-29.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-29.jsonl), [observation_source_quality_audit_2026-07-29.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-29.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-07-29 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [x] `[AIDecisionQualityPromptV2Followup0729] exact_v2 Prompt V2 paired replay 품질보완 및 stage 표본 재확인` (`Due: 2026-07-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:35~17:00`, `Track: ScalpingLogic`)
  - Source: [ai_prompt_paired_replay_2026-07-29.json](/home/ubuntu/KORStockScan/data/report/ai_prompt_paired_replay/ai_prompt_paired_replay_2026-07-29.json), [ai_prompt_recovery_trigger_2026-07-29.json](/home/ubuntu/KORStockScan/data/report/ai_prompt_recovery_trigger/ai_prompt_recovery_trigger_2026-07-29.json), [ai_decision_quality_baseline_2026-07-29.json](/home/ubuntu/KORStockScan/data/report/ai_decision_quality_baseline/ai_decision_quality_baseline_2026-07-29.json), [ai_decision_quality.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_decision_quality.py)
  - 구현 결과: offline-only Prompt `decision_quality_v2_5`에 trusted aggressor tape와 liquidity를 분리하는 source precedence, structural floor·1/3분 recovery·trusted supportive tape 결합 trigger, 단계별 semantic correction, venue별 Candidate 노출 sample floor와 `false_drop`·`false_wait`·`false_buy` taxonomy를 추가했다. live prompt consumer는 연결하지 않았고 `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`를 유지했다.
  - 실제 replay 결과: 자연 exact_v2 `198/198`쌍(KRX `49`, NXT `149`)이 모두 comparable이며 schema reject/provider fail/missing result/provider none은 각각 `0`건이다. Control action은 `BUY 8/WAIT 123/DROP 67`, Candidate는 `BUY 8/WAIT 12/DROP 178`, Candidate edge state는 `EDGE 125/NO_EDGE 73`이다.
  - 품질 판정: Control source-quality-adjusted EV `-0.027478%`, Candidate EV `-0.011734%`, delta `+0.015745%p`, missed-upside reduction `4`, new missed-upside `1`, adverse-first exposure `0→0`이다. EV 개선과 missed-upside 감소는 확인했지만 Candidate EV 양수, new missed-upside 비증가, Candidate 노출 sample floor를 충족하지 못했다. Candidate 노출은 전체 `8건/3종목`, KRX `1건/1종목`, NXT `7건/3종목`이고 taxonomy는 `false_drop 12`, `false_wait 4`, `false_buy 3`이므로 최종 상태는 `paired_replay_complete_candidate_quality_rejected`다.
  - venue 판정: KRX Candidate EV `-0.025797%`(Control 대비 `+0.025299%p`), NXT Candidate EV `-0.007109%`(Control 대비 `+0.012602%p`)로 두 venue 모두 개선됐지만 양수 전환과 venue별 독립 노출 최소 `10건/3종목`을 통과하지 못했다. 반복된 단일 종목 유리 사례를 이용해 spread/risk 경계를 결과 맞춤식으로 고정하지 않는다.
  - Official Kiwoom Reference Gate: `2026-07-29T16:30:17+09:00`, upstream `1504d45fa145eb11fdd662a08aa9d873eee55849`; `kiwoom_docs/차트.md`, `examples/국내주식/차트/get_domestic_stock_minute_chart.py`, `postman/kiwoom-openapi.postman_collection.json`, local `src/utils/kiwoom_utils.py`를 대조했다. `ka10080 open_pric`이 공식 분봉 시가이며 로컬 `시가` 정규화 경로와 일치하고, recovery 성과는 회복 확인봉 종가가 아니라 바로 다음 동일 route 분봉의 `open_pric`만 사용한다. 다음 봉 시가가 없거나 90초를 초과하면 비교 불가로 닫는다.
  - 다음 판정 기준: Prompt V2.5를 version-fixed offline 후보로 유지하고 신규 natural exact_v2 cohort에서 venue별 독립 BUY 노출 `10건/3종목` 이상을 먼저 확보한다. 이후 전체 eligible cohort로 EV 양수·Control 대비 EV 개선·missed-upside 감소·new missed-upside 및 negative/adverse exposure 비증가를 동시에 재확인하며, 통과 전에는 별도 PREOPEN live-prompt apply review를 열지 않는다.
  - 표본 보류: `entry_price 3건/3종목`, `holding 2건/1종목`은 `sample_floor_keep_collecting`으로 유지하고 인위 호출·과거 payload 승격·합성 문맥으로 채우지 않는다.
  - 금지: Candidate runtime 승격, live prompt 변경, provider/model/threshold/가격/수량/주문/bot 변경을 수행하지 않는다.
  - 다음 액션: `prompt_candidate_quality_rejected_refine`로 닫고, risk calibration은 venue별 독립 노출 표본이 성숙한 뒤에만 재개한다.

- [ ] `[AIPromptV2DailyReplay0730] Prompt V2.5 신규 자연표본·outcome 누적 replay` (`Due: 2026-07-30`, `Slot: POSTCLOSE`, `TimeWindow: 16:35~17:10`, `Track: ScalpingLogic`)
  - Source: [ai_prompt_paired_replay_2026-07-29.json](/home/ubuntu/KORStockScan/data/report/ai_prompt_paired_replay/ai_prompt_paired_replay_2026-07-29.json), [ai_prompt_recovery_trigger_2026-07-29.json](/home/ubuntu/KORStockScan/data/report/ai_prompt_recovery_trigger/ai_prompt_recovery_trigger_2026-07-29.json), [ai_decision_quality.py](/home/ubuntu/KORStockScan/src/engine/scalping/ai_decision_quality.py)
  - 판정 기준: 2026-07-30 자연 exact_v2 호출의 10분 outcome 성숙 후 동일 Prompt V2.5/model/provider·전체 eligible cohort로 paired replay를 재생성한다. KRX/NXT별 Candidate BUY 노출 `10건/3종목` 이상, candidate EV 양수, Control 대비 EV 개선, missed-upside 감소, new missed-upside 및 negative/adverse exposure 비증가, provider/schema/missing `0`을 모두 확인한다.
  - 현재 적용 상태: 2026-07-29 Prompt V2.5는 호출·semantic 계약은 통과했지만 판단 품질과 venue별 노출 floor가 reject이므로 2026-07-30 PREOPEN live prompt 적용은 `blocked_keep_current_hot_v1`이다.
  - 금지: replay 결과를 live prompt에 매일 자동 덮어쓰기, 유리 사례 선별, 과거 payload 재구성, provider/model/threshold/가격/수량/주문/bot 변경을 수행하지 않는다.
  - 다음 액션: `keep_collecting_version_fixed`, `candidate_quality_pass_prepare_separate_preopen_apply_review`, `source_quality_blocked`, `provider_or_schema_fix_required` 중 하나로 닫는다.

- [ ] `[PostcloseSourceQualityGateReview0729] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-07-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-07-29.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-29.json), [threshold_cycle_ev_2026-07-29.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-29.json), [code_improvement_workorder_2026-07-29.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-29.json), [threshold_cycle_postclose_verification_2026-07-29.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-29.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0729] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-07-29`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-28.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0729] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-07-29`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-28.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-28.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0729] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-07-29`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-07-28.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-28.md), [code_improvement_workorder_2026-07-28.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-28.json)
  - 판정 기준: selected_order_count=169와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0729] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-07-29`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-07-28.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-28.json), [runtime_apply_gap_audit_2026-07-28.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-28.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`87`, rollup_required_count=`87`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 86}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0729] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-07-29`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-07-28.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-07-28.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`16`, run_count=`15`, skip_count=`1`, source_missing_count=`5`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`scalp_sim_ai_deferred_review`, top_reasons=`output_missing_or_unreadable:9, upstream_drift_signal:9, source_missing_or_unreadable:5, fresh_outputs_no_trigger:1, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
