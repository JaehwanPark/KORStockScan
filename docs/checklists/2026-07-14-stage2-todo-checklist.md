# 2026-07-14 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-07-13` postclose -> `2026-07-14`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0714] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-07-14`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-13.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 실행 결과 (`2026-07-14 08:54 KST`): 판정=`applied_guard_passed_env`. `threshold_apply_2026-07-14.json`은 status=`auto_bounded_live_ready`, apply_mode=`auto_bounded_live`, runtime_change=`true`, source_phase_auto_apply_blocked=`false`다. `threshold_runtime_env_2026-07-14.json`과 `threshold_runtime_env_verify_2026-07-14.json` 기준 selected family는 `25`개이고, verify는 status=`pass`, passed=`true`, missing_family_count=`0`, pid_passed=`true`, pid_missing/pid_mismatches=`[]`다. blocked family/approval gap/same-stage conflict를 수동 env override로 우회하지 않았다.

- [x] `[RisingMissedScoutRuntimePreopen0714] rising_missed_scout_workorder 구현분 다음 장전 runtime 반영 여부 확인` (`Due: 2026-07-14`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-07-13.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-07-13.json), [rising_missed_normal_buy_bridge_candidate_discovery_2026-07-13.json](/home/ubuntu/KORStockScan/data/report/rising_missed_normal_buy_bridge_candidate_discovery/rising_missed_normal_buy_bridge_candidate_discovery_2026-07-13.json), [code_improvement_workorder_2026-07-13.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-13.json), [threshold_apply_2026-07-14.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-14.json), [threshold_runtime_env_2026-07-14.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-14.json), [threshold_runtime_env_verify_2026-07-14.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-14.json)
  - 2026-07-14 user-approved supplement: scout/normal bridge 공통 `resolve_rising_missed_decision_input`과 date-bounded TP1 selector를 구현하고, `operator_runtime_overrides.env`에 `KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED=true`, `KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE=2026-07-14`를 추가했다. rollback은 selector `false`이며 sizing/cap/provider/TP/exit/hard safety는 변경하지 않는다. review gate와 graceful restart/PID env 검증 전에는 runtime 반영 완료로 판정하지 않는다.
  - 2026-07-14 08:46 KST 적용 판정: `$korstockscan-review-gate` post-fix 재리뷰와 targeted validation `797 passed`, compile, `git diff --check`, checklist parser 통과 후 `./restart.sh`로 PID `8378 -> 26504` graceful restart를 완료했다. `threshold_runtime_env_verify_2026-07-14.json`은 status=`pass`, selected_family_count=`25`, missing_family_count=`0`, pid_passed=`true`, pid_missing/pid_mismatches=`[]`였고 새 PID env에서 TP1 selector enabled/date, one-share entry, normal bridge가 모두 확인됐다. 다음 액션=`runtime_env_reflected_and_verified`.
  - 2026-07-14 09:42 KST 장중 보완: 09:00~09:20 관찰에서 확인된 WS nested orderbook spread 기본값, reversal current-delta/상관 micro 중복점수, reversal-up recheck 중복 enqueue, REST reserve 소진 cache 소비 문제를 보완했다. review/fix/re-review 후 관련 targeted pytest `722 passed`, compile, `git diff --check`, checklist parser를 통과했고 `./restart.sh`로 PID `26504 -> 45019` graceful restart를 완료했다. runtime env handoff는 selected family `25`, status=`pass`, missing family `0`, pid_passed=`true`, pid_missing/pid_mismatches=`[]`이며 새 PID env의 TP1 selector enabled/date, one-share entry, normal bridge를 재확인했다. 재기동 후 첫 TP1 평가에서 input=`ready`, source=`ws`, quote level basis=`normalized_ws_orderbook`, spread=`0.00906`이 기록되어 기존 spread 기본값 `1.0` 병목 제거를 확인했다.
  - 2026-07-14 09:53 KST 재리뷰 보완: normal bridge block/defer provenance 누락, TP1 marker 부분문자열 오탐과 source-family 과대계수, resolver effective-price/anchor provenance 누락, 20분 first-hit label의 후속 fee/tax 누락을 수정했다. 최종 재리뷰에서 selector가 submit 권한을 얻거나 기존 stale/tick-speed/reversal/broker/account/order/quantity/cooldown veto를 우회하는 문제는 없었다. 관련 targeted pytest `726 passed`, compile, `git diff --check`, checklist parser 통과 후 `./restart.sh`로 PID `45019 -> 48934` graceful restart를 완료했다. runtime env handoff는 selected family `25`, status=`pass`, missing family `0`, pid_passed=`true`, pid_missing/pid_mismatches=`[]`이며 새 프로세스의 계좌 동기화, WS 연결/로그인, 0B/0D 첫 수신, 스캐너 루프 진입을 확인했다.
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`4`, forced_scout_with_post_sell_count=`4`, profitable_forced_scout_count=`2`, loss_or_flat_forced_scout_count=`2`, current_missed_count=`66`)과 `rising_missed_normal_buy_bridge_candidate_discovery` 요약(status=`hold_no_candidate`, bridge_candidate_count=`0`, code_improvement_order_count=`0`, runtime_env_key=`KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED`)을 함께 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder`/bridge discovery 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0714] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-07-14`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-13.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, entry_split_order_plan, scale_in_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0714] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-07-14`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-07-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-13.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [x] `[RisingMissedTP1PostRestartMonitor0714] Rising Missed TP1/Freshness Envelope 재기동 후 가동현황 및 반전 가드 점검` (`Due: 2026-07-14`, `Slot: INTRADAY`, `TimeWindow: 09:53~10:05`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-07-14.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-14.jsonl), [rising_missed_intraday_feedback_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-14.json), [rising_missed_intraday_feedback_2026-07-14.md](/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-14.md)
  - 실행 결과 (`2026-07-14 10:05 KST`): PID `48934`는 정상 유지됐고 TP1 평가는 block=`44`, pass=`0`, defer=`0`, input ready=`44/44`, trusted WS micro 결측=`0/44`, REST budget defer=`0`, `ka10004` fetch ok=`44/44`였다. freshest-age 선택은 WS=`40`, REST=`4`이고 conflict=`0`, WS/REST gap max=`54.407bp`다. lane 적격은 8회/5종목이며 lane 미충족=`36`, micro 조건 실패=`3`, WAIT bid-imbalance 미충족=`5`다. 적격 8회 모두 spread `21.77~107.14bp`로 `20bp` 상한을 넘고 fresh tick acceleration/micro-VWAP support가 `0/8`이었다. 10:05까지 종목별 관측 MFE 최대는 `+0.2191%`로 gross `+1.30%` 과차단 증거는 없지만, 각 20분 horizon은 미완료라 edge 판정에는 사용하지 않는다.
  - 반전 가드 판정: selector pass가 없어 `rising_missed_reversal_pre_submit_guard` 평가/block은 `0/0`이고, 재기동 이후 `reversal_up_watch`와 `reversal_up_volatile_watch`도 각각 `0`이라 과도 차단/제출 적정성은 `hold_sample`이다. 주문·threshold·provider·cap 변경이나 추가 재기동 근거로 사용하지 않는다.
  - source-quality handoff: `001820`에서 `first_seen_price=10662` 대 실제 호가 약 `89,000`의 anchor 오염이 18회 반복됐고, TP1 평가 44회 모두 tick acceleration/micro-VWAP source가 `missing`이었다. 오늘 `CodeImprovementWorkorderReview0714`에서 producer fix와 회귀 테스트 대상으로 재확인한다.

- [ ] `[IntradaySourceQualityGateCheck0714] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-07-14`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-07-14.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-14.jsonl), [threshold_events_2026-07-14.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-14.jsonl), [observation_source_quality_audit_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-14.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-07-14 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0714] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-07-14`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-14.json), [threshold_cycle_ev_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-14.json), [code_improvement_workorder_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-14.json), [threshold_cycle_postclose_verification_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-14.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0714] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-07-14`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-13.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0714] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-07-14`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-13.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0714] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-07-14`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-07-13.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-13.md), [code_improvement_workorder_2026-07-13.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-13.json), [pipeline_events_2026-07-14.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-14.jsonl), [rising_missed_intraday_feedback_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-14.json)
  - 판정 기준: selected_order_count=117와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - Rising Missed 10:05 handoff: `first_seen_price`와 fresh quote의 비정상 배율을 fail-closed하는 symbol-local anchor contract, 그리고 trusted 0B/0D micro에서 TP1 tick acceleration 또는 micro-VWAP freshness를 공급하는 producer contract를 `instrumentation_gap`으로 검토한다. acceptance test는 cross-symbol/stale anchor가 lane/REST 평가를 만들지 않고, 정상 WS sample에서 momentum source가 `missing`이 아니며, 결측 시 기존 defer/block과 submit-safety가 유지되는 것이다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[NonImplementLongstandingRejudge0714] non-implement 장기 항목 재판정 및 처리방안 재확인` (`Due: 2026-07-14`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:35`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-07-13.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-13.json), [code_improvement_workorder_2026-07-13.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-13.md)
  - 판정 기준: `selected_terminal_non_implement_longstanding_order_ids`, `selected_longstanding_non_implement_disposition_counts`, `non_selected_longstanding_non_implement_disposition_counts`, `repeat_unresolved_escalation_count`, `needs_followup_workorder_count`를 산출물 기준으로 확인한다. `keep_visible_by_design`, `review_required`, `implemented_with_provenance`, `action_required`를 분리하고 action_required가 있으면 별도 구현 워크오더로 승격할지 판단한다.
  - 금지: `keep_visible_by_design` 또는 source-only visibility rollup을 `implement_now`로 임의 승격하지 않는다. runtime/order/provider/bot/threshold/cap 변경 근거로 사용하지 않는다.
  - 다음 액션: `no_action_required_keep_visible`, `review_required_defer_evidence`, `implemented_with_provenance`, `new_followup_workorder_required`, `repeat_unresolved_escalation_required` 중 하나로 닫는다.

- [ ] `[ExitOutcomeUnknownEvidenceReview0714] exit_outcome=outcome_unknown deferred evidence 처리방안 확인` (`Due: 2026-07-14`, `Slot: POSTCLOSE`, `TimeWindow: 21:35~21:45`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-07-13.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-13.json), [lifecycle_decision_matrix_2026-07-13.json](/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-07-13.json), [lifecycle_bucket_discovery_2026-07-13.json](/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-13.json)
  - 판정 기준: `order_lifecycle_exit_bucket_exit_outcome_outcome_unknown_40c2ecc3`가 계속 `defer_evidence`인지 확인하고, 파일 후보(`files_likely_touched`)와 실행 가능한 acceptance test가 생겼는지 확인한다. 둘 중 하나라도 없으면 evidence 대기로 닫고, 둘 다 있으면 별도 instrumentation workorder 후보로 분리한다.
  - 금지: exit outcome unknown만으로 exit threshold, TP/trailing, sell automation, provider, bot restart를 변경하지 않는다.
  - 다음 액션: `defer_evidence_no_code_action`, `candidate_ready_needs_workorder`, `covered_by_new_provenance`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[PerformanceParityHarnessScope0714] deferred performance review 항목 parity harness 범위 검토` (`Due: 2026-07-14`, `Slot: POSTCLOSE`, `TimeWindow: 21:45~21:55`, `Track: RuntimeStability`)
  - Source: [code_improvement_workorder_2026-07-13.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-13.json), [codebase_performance_workorder_2026-07-13.json](/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-07-13.json)
  - 판정 기준: `order_perf_kiwoom_orders_http_session_review`, `order_perf_config_cache_scope_review`, `order_perf_sentinel_event_cache_incremental_review`의 broker request lifecycle, runtime config reload semantics, incremental cache semantics를 분리해 parity harness 선행 필요 여부를 확인한다. 범위가 닫히지 않으면 deferred performance backlog로 유지한다.
  - 금지: parity harness 없이 broker request/session, runtime config cache, sentinel incremental cache 구현을 시작하지 않는다. provider/order/bot/threshold 변경과 묶지 않는다.
  - 다음 액션: `defer_until_parity_harness`, `parity_harness_workorder_required`, `reject_out_of_scope`, `covered_by_existing_test` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0714] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-07-14`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-07-13.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-13.json), [runtime_apply_gap_audit_2026-07-13.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-13.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`268`, rollup_required_count=`268`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 267}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0714] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-07-14`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-07-13.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-07-13.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`16`, run_count=`16`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, scalp_sim_ai_deferred_review, pattern_lab_currentness_audit`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:15, source_missing_or_unreadable:7, upstream_drift_signal:7, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
