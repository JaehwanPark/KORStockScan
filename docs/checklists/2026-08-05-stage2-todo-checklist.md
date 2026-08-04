# 2026-08-05 Stage2 To-Do Checklist

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

## 사용자 지시 구현

- [x] `[LimitDownObservationEffectiveness0805] 하한가 관찰 포착 및 exact-empty 근접 하한가 보조군 구현·리뷰` (`Due: 2026-08-05`, `Slot: INTRADAY`, `TimeWindow: 09:00~15:30`, `Track: ScalpingLogic`)
  - Source: [limit_down_watch.py](/home/ubuntu/KORStockScan/src/engine/scalping/limit_down_watch.py), [limit_down_watch_report.py](/home/ubuntu/KORStockScan/src/engine/monitoring/limit_down_watch_report.py), [kiwoom-api-data-contract.md](/home/ubuntu/KORStockScan/docs/kiwoom-api-data-contract.md)
  - 판정 기준: KRX 장중에만 체류시간을 계산하고 0B 체결과 0D 호가를 분리 포착한다. 공식 전일 하한가가 0건일 때만 전일 저가 `-29.5%~-27%` 및 저가 대비 종가 회복 `5% 이상`인 `near_limit_rebound`를 공식 일봉과 DB 일봉 교차검증 후 관찰 전용으로 등록한다.
  - 당시 금지: 후속 사용자 지시 전까지 `near_limit_rebound`를 기존 exact 하한가 unlock counterfactual/live-auto 표본에 합치거나 BUY·실주문 권한으로 사용하지 않는다. 후속 전환은 아래 `LimitDownSingleSampleAutoLive0805`가 독립 소유한다.
  - 다음 액션: targeted test와 review gate가 finding 0건이면 완료하고, 자연 0B/0D 및 유형별 postclose 산출물은 런타임 재기동 이후 별도 관찰한다.
  - 실행 결과 (`2026-08-05 07:43 KST`): 공식 upstream `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`의 `kiwoom_docs/종목정보.md`, `kiwoom_docs/실시간시세.md`, `kiwoom/realtime/packets.py`, `kiwoom/specs.py`를 재확인했다. KRX 장중 세션에서만 관찰 등록·체류를 시작하고, 0D 호가를 0B 체결과 분리해 5초 snapshot 및 REG route/item provenance로 기록하며, 유효 빈 소스도 idle heartbeat를 저장한다. exact 0건일 때만 `near_limit_rebound`를 DB 완성일 `2635`행 preflight, `ka10081` 전일/전전일 OHLC, `ka10099` 관리·환기·투자유의 상태로 교차검증한다. 신규 cohort는 exact unlock label/sim/live-auto와 runtime promotion에서 명시적으로 제외했다. 자체리뷰에서 0D 매 이벤트 디스크 쓰기와 관리·환기 필터 결손을 발견해 보완했고 재리뷰 finding=`0`; 관련 `263 passed`, compile, Ruff(기존 비변경 F841 제외), Black, `git diff --check`, checklist parser를 통과했다. 실 API 임시 smoke는 exact/near=`0/0`, status=`pass`, blocked=`0`이며 운영 artifact와 bot 상태는 변경하지 않았다.

- [x] `[LimitDownSingleSampleAutoLive0805] 유형별 1개 검증 표본 자동 실매매 후보화·누적 자동갱신 검증·리뷰·게시` (`Due: 2026-08-05`, `Slot: INTRADAY`, `TimeWindow: 09:00~15:30`, `Track: ScalpingLogic`)
  - Source: [limit_down_watch_research.py](/home/ubuntu/KORStockScan/src/engine/monitoring/limit_down_watch_research.py), [limit_down_watch.py](/home/ubuntu/KORStockScan/src/engine/scalping/limit_down_watch.py), [scalping_scanner.py](/home/ubuntu/KORStockScan/src/scanners/scalping_scanner.py)
  - 판정 기준: source-quality가 유효한 `cohort×가격대` ordered path 1개부터 비용 차감 EV·downside p10·MAE·BBO 기준을 모두 통과하면 장후 bounded-live artifact를 생성하고, 다음 거래일 런타임이 사용자 승인 없이 최신 prior-date 정책을 자동 로드한다. 매 장후 이전 rolling row와 당일 row를 row-id로 중복 제거해 cumulative를 자동 갱신하며 최신 artifact가 blocked이면 이전 ready 정책을 상속하지 않는다.
  - 보호장치: exact는 연속 두 unlock 체결, `near_limit_rebound`는 시가 회복 및 저가 대비 `1%` 이상 반등의 연속 두 체결을 요구한다. 공통으로 fresh BBO·spread `1.5%`·일 1회·동시 1종목·물타기/재진입/오버나이트 금지와 정상 scalping AI·submit·hard safety를 유지한다. provider·threshold·수량 owner·cap·bot 상태는 변경하지 않는다.
  - 다음 액션: review gate finding 0, targeted test, cumulative 자동갱신/자동철회, compile, formatter/lint, diff/checklist parser 검증 후 의미 단위 커밋·푸시한다. 봇 재기동은 이 항목의 권한이 아니다.
  - 실행 결과 (`2026-08-05 KST`): exact `2회+/1회`와 `near_limit_rebound`를 독립 `cohort×가격대` cell로 유지하면서 source-quality 유효 ordered path 1건부터 비용·EV·하방·MAE·BBO 기준을 모두 통과한 유형만 no-approval bounded-live artifact로 만든다. 런타임은 최신 prior-date artifact를 자동 로드하되 near 유형은 raw 0B 연속 두 틱의 시가 회복·저가 대비 `1%` 반등 확인 이벤트와 제출 직전 fresh quote를 재검증한다. 장후 producer는 최신 prior rolling rows와 당일 rows를 row-id로 중복 제거해 누적 갱신하고, prior 계약/행 유일성/누적 count 손상 또는 최신 누적 EV·하방 기준 이탈 시 source-quality 차단 및 다음 기동 정책 자동 철회를 수행한다. 리뷰에서 near sim provenance 오기, snapshot/raw-tick 확인 의미 불일치, prior 누적 artifact 무검증을 찾아 모두 보완했다. 확대 회귀 `321 passed`, Black, targeted Ruff(legacy E402/F401/F841 제외), compile, checklist parser, `git diff --check`를 통과하고 미해결 finding=`0`이다. provider·일반 threshold·position sizing owner·cap·bot 상태와 현재 PID는 변경하지 않았다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-08-04` postclose -> `2026-08-05`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [ ] `[ThresholdEnvAutoApplyPreopen0805] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-08-05`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-04.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0805] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-08-05`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-08-04.json), [code_improvement_workorder_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-04.json), [threshold_apply_2026-08-05.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-05.json), [threshold_runtime_env_2026-08-05.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-08-05.json), [threshold_runtime_env_verify_2026-08-05.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-08-05.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`4`, forced_scout_with_post_sell_count=`13`, post_sell_join_coverage_pct=`3.186275`, outcome_coverage_state=`partial`, profitable_forced_scout_count=`8`, loss_or_flat_forced_scout_count=`5`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0805] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-08-05`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-04.json)
  - 판정 기준: selected_families=entry_split_order_plan, scale_in_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, lifecycle_decision_matrix_runtime, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0805] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-08-05`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-04.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0805] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-08-05`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-08-05.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-05.jsonl), [threshold_events_2026-08-05.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-05.jsonl), [observation_source_quality_audit_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-05.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-08-05 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0805] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-08-05`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-05.json), [threshold_cycle_ev_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-05.json), [code_improvement_workorder_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-05.json), [threshold_cycle_postclose_verification_2026-08-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-05.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0805] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-08-05`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-04.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0805] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-08-05`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-04.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0805] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-08-05`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-08-04.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-08-04.md), [code_improvement_workorder_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-04.json)
  - 판정 기준: selected_order_count=80와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0805] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-08-05`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-04.json), [runtime_apply_gap_audit_2026-08-04.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-04.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`327`, rollup_required_count=`327`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 326}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0805] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-08-05`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-08-04.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-08-04.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`15`, run_count=`15`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:14, source_missing_or_unreadable:7, upstream_drift_signal:7, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
