# 2026-07-15 Stage2 To-Do Checklist

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
## 자동 생성 체크리스트 (`2026-07-14` postclose -> `2026-07-15`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0715] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-07-15`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-14.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 실행 기록 (2026-07-15 08:02 KST): 판정=`applied_guard_passed_env`. 최초 07:35 산출물은 [threshold_runtime_env_verify_2026-07-15.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-15.json)이 `status=fail`, `fail_reason=runtime_env_handoff_missing`였고, 원인은 2026-07-14 date-bounded `entry_split_market_first_leg`/`entry_split_order_policy` override가 다음 날까지 남아 `policy_inactive_date`, `market_first_inactive_date`를 만든 것이다. [operator_runtime_overrides.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/operator_runtime_overrides.env)에서 해당 expired override를 명시적으로 OFF 처리한 뒤 표준 preopen wrapper를 재실행했다. 재생성된 [threshold_cycle_preopen_2026-07-15.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-07-15.status.json)은 status=`succeeded`, reason=`completed`, exit_code=`0`, runtime_effect=`preopen_runtime_env_apply_only`, updated_at=`2026-07-15T08:02:04+09:00`이고 [threshold_apply_2026-07-15.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-15.json)은 status=`auto_bounded_live_ready`, apply_mode=`auto_bounded_live`, runtime_change=`true`, source_date=`2026-07-14`, auto_apply_selected_count=`21`이다. 최종 [threshold_runtime_env_verify_2026-07-15.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-15.json)은 status=`pass`, passed=`true`, missing_family_count=`0`, runtime_policy_fail_count=`0`, findings=`[]`이다. `entry_split_order_plan` override는 disabled로 닫혔고 `scale_in_split_order_plan` 정책 audit는 pass다. 장중 threshold mutation 없이 PREOPEN runtime env만 source로 인정한다.

- [x] `[RisingMissedScoutRuntimePreopen0715] rising_missed_scout_workorder 구현분 다음 장전 runtime 반영 여부 확인` (`Due: 2026-07-15`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-07-14.json), [rising_missed_normal_buy_bridge_candidate_discovery_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/rising_missed_normal_buy_bridge_candidate_discovery/rising_missed_normal_buy_bridge_candidate_discovery_2026-07-14.json), [code_improvement_workorder_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-14.json), [threshold_apply_2026-07-15.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-15.json), [threshold_runtime_env_2026-07-15.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-15.json), [threshold_runtime_env_verify_2026-07-15.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-15.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`3`, forced_scout_with_post_sell_count=`2`, profitable_forced_scout_count=`2`, loss_or_flat_forced_scout_count=`0`, current_missed_count=`0`)과 `rising_missed_normal_buy_bridge_candidate_discovery` 요약(status=`source_missing`, bridge_candidate_count=`0`, code_improvement_order_count=`0`, runtime_env_key=`KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED`)을 함께 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder`/bridge discovery 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.
  - 실행 기록 (2026-07-15 08:02 KST): 판정=`runtime_env_reflected_and_verified`. [rising_missed_scout_workorder_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-07-14.json)은 code_improvement_order_count=`3`, forced_scout_with_post_sell_count=`2`, profitable_forced_scout_count=`2`, loss_or_flat_forced_scout_count=`0`, current_missed_count=`0`, forced_initial_entry_equal_weight_avg_profit_pct=`0.565`를 기록했다. [rising_missed_normal_buy_bridge_candidate_discovery_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/rising_missed_normal_buy_bridge_candidate_discovery/rising_missed_normal_buy_bridge_candidate_discovery_2026-07-14.json)은 status=`source_missing`, bridge_candidate_count=`0`, code_improvement_order_count=`0`, missing_required_sources=`intraday_entry_blocker_diagnostics`, runtime_env_key=`KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED`다. 당일 [threshold_runtime_env_2026-07-15.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-15.json)은 selected_families에 `rising_missed_normal_buy_bridge`를 포함하고 `KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED=true`를 기록했으며, 최종 verify는 pass다. 단, bridge discovery 자체는 source_missing이고 신규 bridge_candidate_count=`0`이므로 이 확인은 기존 mapped runtime family 반영 확인이며, forced scout 손익만으로 추가 threshold/order/provider/bot/cap 변경 권한을 열지 않는다.

- [x] `[Runbook 운영 확인] 장전 자동화체인 상태 확인` (`Due: 2026-07-15`, `Slot: PREOPEN`, `TimeWindow: 08:00~09:00`, `Track: RunbookOps`)
  - Source: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [threshold_cycle_preopen_2026-07-15.status.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-07-15.status.json), [threshold_runtime_env_verify_2026-07-15.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-15.json), [ensemble_scanner.log](/home/ubuntu/KORStockScan/logs/ensemble_scanner.log), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 실행 기록 (2026-07-15 08:06 KST): 판정=`pass_after_graceful_restart`. `logs/threshold_cycle_preopen_cron.log`와 재실행 wrapper는 `[DONE] threshold-cycle preopen target_date=2026-07-15`를 남겼고 preopen status는 status=`succeeded`, exit_code=`0`, apply/runtime env artifact exists=`true`다. [ensemble_scanner.log](/home/ubuntu/KORStockScan/logs/ensemble_scanner.log)는 `[DONE] final_ensemble_scanner target_date=2026-07-15 finished_at=2026-07-15T07:20:12`를 남겼고 [daily_recommendations_v2_diagnostics.json](/home/ubuntu/KORStockScan/data/daily_recommendations_v2_diagnostics.json)은 latest_date=`2026-07-14`, selected_count=`2`, fallback_written_to_recommendations=`false`다. 봇은 07:55에 먼저 기동되어 최초 PID에 expired entry split override가 남았으므로 `restart.flag` 표준 handoff로 graceful restart를 수행했다. 새 `bot_main.py` PID는 `KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE=2026-07-15`, `KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED=true`, `KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED=true`, `KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED=false`, `KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ENABLED=false`, `KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws`를 로드했다. `swing_runtime_approval`은 requested=`0`, approved=`0`, selected=`[]`이고 `runtime_apply_bridge` approved=`0`, selected=`[]`, blocked reason은 contract/source-quality/AI parsed gap으로 정상 차단이다. 이 확인은 runtime env source 정합성 보정이며 threshold/order/provider/cap/hard-safety 변경으로 확장하지 않는다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[LowProfitStagnationConfirmation0715] 저수익 장기보유 즉시청산을 실제 횡보확인 청산으로 보완하고 당일 적용` (`Due: 2026-07-15`, `Slot: INTRADAY`, `TimeWindow: 08:08~09:00`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-07-15.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-15.jsonl), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py), [test_sniper_scale_in.py](/home/ubuntu/KORStockScan/src/tests/test_sniper_scale_in.py)
  - 판정 기준: 마녀공장(439090) `LOW_PROFIT_STAGNATION` 체결 당시 hold=`55953s`, signal profit=`+0.38%`, fill=`16,490원` 이후 08:10:55 WS 관측가=`16,855원`으로 체결가 대비 `+2.21%` 상승한 counterfactual을 기준으로, 저수익 청산이 보유 벽시계 시간만으로 즉시 발동하지 않고 기존 PREOPEN-selected stagnation 기준(min_sec=`180`, max_profit_move=`0.15%p`, max_peak_improve=`0.10%p`)의 독립 confirmation anchor를 통과해야 한다. 가격/고점 개선 시 anchor를 재설정하고, 확인된 청산도 기존 holding-flow override와 broker sell guard를 유지해야 한다.
  - 금지: hard/protect/emergency/trailing exit 우선순위 변경, 신규 장중 threshold 생성, provider/order quantity/cap 변경, stale quote bypass를 수행하지 않는다.
  - 다음 액션: targeted test, compile, source-quality contract test, `git diff --check`, review gate 무결함을 확인한 뒤 사용자 명시 지시에 따라 우아한 재기동하고 새 PID의 기존 PREOPEN runtime env 보존 및 `low_profit_stagnation_confirmation` 발화 가능 상태를 검증한다.
  - 실행 기록 (2026-07-15 08:34 KST): 판정=`implemented_reviewed_and_runtime_applied`. 기존 저수익 청산은 hold wall-clock과 adjusted profit band만으로 즉시 발동했으나, 이제 별도 `low_profit_stagnation_*` anchor를 시작하고 기존 PREOPEN-selected `SCALP_PROFIT_STAGNATION_MIN_SEC=180`, `MAX_PROFIT_MOVE_PCT=0.15`, `MAX_PEAK_IMPROVE_PCT=0.10`을 재사용한다. 수익 또는 고점 개선 시 anchor를 재설정하고, 180초 정체 확인 후에도 `holding_flow_override`를 거친다. 신규 threshold/env는 추가하지 않았으며 hard/protect/emergency/trailing 우선순위와 broker sell guard는 유지했다. `low_profit_stagnation_confirmation` stage는 quote stale/age/source를 포함한 source-quality contract를 갖는다. targeted holding tests=`13 passed`, source-quality audit 전체=`100 passed`, threshold preopen profit-stagnation tests=`2 passed`, compile/pass, `git diff --check`/checklist parser pass이며 review gate 재검토 결과 미해결 finding=`0`이다. `./restart.sh`가 old PID=`10400`을 종료하고 new PID=`20255`를 기동했으며 runtime handoff는 passed=`true`, pid_passed=`true`, missing_family_count=`0`, findings=`[]`다. 새 PID는 `KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE=2026-07-15`, low-profit enabled=`true`, min_hold=`1800`, adjusted band=`0.20~1.00`, 기존 stagnation min_sec=`180`, move/peak=`0.15/0.10`을 보존했다. 재기동 직후 eligible 저수익 보유종목이 없어 confirmation event=`0`은 정상 무발화이며, 다음 자연 발화에서 anchor start/reset/confirmed와 후속 MFE/MAE를 관찰한다.

- [x] `[SoftStopRecoveryOpportunity0715] overnight soft-stop 물타기 및 반등확인 기회손실 경로 보완` (`Due: 2026-07-15`, `Slot: INTRADAY`, `TimeWindow: 08:08~09:10`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-07-15.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-15.jsonl), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [test_holding_flow_override.py](/home/ubuntu/KORStockScan/src/tests/test_holding_flow_override.py), [test_sniper_scale_in.py](/home/ubuntu/KORStockScan/src/tests/test_sniper_scale_in.py)
  - 판정 기준: KB금융(105560)의 position wall-clock hold=`64697s`가 deep-recovery `120~480s` 창을 오염한 경로를 NXT 08:00 또는 명시적 KRX-only 09:00 active-session elapsed로 보정한다. fresh trusted WS true OFI/depth/pressure/top-depth composite가 지지하면 약한 tick pressure 또는 micro-VWAP를 대체 evidence로 허용하고, `scalp_soft_stop_pct + LOSS`의 max defer는 worsen floor 미도달 시 90초 1회만 연장한다. 수동관리 등록 성공은 같은 loop의 broker SELL을 중단해야 한다.
  - 금지: REST quote를 positive micro evidence로 사용하거나 hard/protect/emergency/worsen/account/order/quantity guard를 우회하지 않는다. 주문가능금액 0원은 당시 사용자 수동매매에 따른 정상 계좌 상태로 판정하여 코드 오류 및 완화 근거에서 제외한다.
  - 실행 기록 (2026-07-15 09:05 KST): 판정=`implemented_reviewed_and_runtime_applied`. holding/scale-in 전체=`751 passed`, source-quality audit=`100 passed`, compile/formatter/diff/parser=`pass`, review gate 미해결 finding=`0`이다. `./restart.sh`가 old PID=`20255`를 종료하고 new PID=`29539`를 기동했으며 runtime handoff passed=`true`, pid_passed=`true`, missing_family_count=`0`, runtime_policy_fail_count=`0`이다. 새 PID에서 WS 실수신을 확인했고 동일 PID env로 실행한 `kt00001` 주문가능금액은 `2,810,172원`, source=`api_fresh`, fallback=`false`, errors=`[]`였다.

- [ ] `[RuntimeEnvIntradayObserve0715] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-07-15`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-14.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, scale_in_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0715] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-07-15`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-14.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0715] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-07-15`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-07-15.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-15.jsonl), [threshold_events_2026-07-15.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-15.jsonl), [observation_source_quality_audit_2026-07-15.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-15.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-07-15 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0715] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-07-15`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-07-15.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-15.json), [threshold_cycle_ev_2026-07-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-15.json), [code_improvement_workorder_2026-07-15.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-15.json), [threshold_cycle_postclose_verification_2026-07-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-15.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0715] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-07-15`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-14.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0715] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-07-15`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-14.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0715] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-07-15`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-07-14.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-14.md), [code_improvement_workorder_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-14.json)
  - 판정 기준: selected_order_count=110와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0715] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-07-15`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-14.json), [runtime_apply_gap_audit_2026-07-14.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-14.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`237`, rollup_required_count=`237`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 236}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0715] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-07-15`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-07-14.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-07-14.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`16`, run_count=`16`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, scalp_sim_ai_deferred_review, pattern_lab_currentness_audit`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:15, source_missing_or_unreadable:7, upstream_drift_signal:7, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
