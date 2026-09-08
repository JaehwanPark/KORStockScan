# 2026-09-08 Stage2 To-Do Checklist

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
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-09-07", "sources": {"automation_chain_trigger_decision": {"sha256": "62c94bcf3f74b63d546ac8cf59844ddc6ef94d6918517f0d8ff2a91bc28eec8c"}, "code_improvement_workorder": {"sha256": "08f2aad61c3e56dcc8412527ce1e00d9c1bbc9d43de0c8ea10aca44eaecc9a40"}, "machine_microstructure_attribution": {"sha256": "4449ce3ad3a632dae284af5faddbd8da77eae618f93ee1a67fe7fe558d44f560"}, "machine_microstructure_policy_approval": {"sha256": "099b313ebbe5873238599cd777ab9fae22855ef2de0e5650d822a513ebafcbcc"}, "main_ai_quality_r0_r3": {"sha256": "4cef54a501aed2d533992f0203cbec48b0378f367e4724aa677ce92b9a513699"}, "rising_missed_scout_workorder": {"sha256": "850cddbaaf3a9d32000049ec9a2ed4048dd0d5cdb8639e2441bdfd9fba15bfb9"}, "runtime_apply_gap_audit": {"sha256": "d295176aa16248dd04612be00a262279b8865ace1b51930c8f13463c3487c227"}, "threshold_cycle_ev": {"sha256": "3cafe0d2bce4f25570548534cf9f01982e52e7aa976898eb81274fcc80909038"}, "tuning_performance_control_tower": {"sha256": "cc55d16f6bde9e07df8378f452d20d60f7743653bedffd5d662af624895352f8"}}} -->
## 자동 생성 체크리스트 (`2026-09-07` postclose -> `2026-09-08`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 승인 재설계 자연 수용

- [ ] `[PatternLabSmallNetNaturalEvidence0908] Claude lab v3 순이익·빈도 연구와 단일-owner 전달 자연 확인` (`Due: 2026-09-08`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~21:55`, `Track: ScalpingLogic`)
  - Source: [#67/#69 보완 리뷰](../audit-reports/2026-09-08-pattern-lab-small-net-remediation-review.md), `analysis/claude_scalping_pattern_lab/outputs/run_manifest.json`, `data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-09-08.json`.
  - 완료 조건: 기존 main paired producer가 실제 매입/매도 총액·비용·순익을 포함한 당일 self-hash source를 자연 생성하고 lab v3가 일별/rolling10거래일/누적을 분리한다. 누락은 null/제외 사유로 남기며 정상 empty와 source failure를 구분한다. manifest 3종 hash → automation → currentness/AI review → EV/workorder의 같은 날짜·generation을 확인한다. ADM/LDM 복구, fallback/latency canary, 2-lab 합의 대기 및 0건 blocker 추천은 새로 만들지 않는다.
  - 경제성/전달: 미검증 스냅샷의 gross/zero 복원값은 승인 근거로 쓰지 않는다. full/partial/scale-in, venue/session/profile을 분리한 작은 양수 순EV도 연구 입력으로 전달하되 기존 owner의 상승/반등·증분 순익·승인/PREOPEN/PID 조건을 대체하지 않는다. 합성 회귀 fixture의 성공은 실수익 개선이 아니다.
  - 유지 판단: [기존-owner 후속 보완](../audit-reports/2026-09-08-pattern-lab-owner-selection-followup-review.md)의 Daily 판정 재계산/hash → AI 경제성 숫자·전수 native ID → EV/workorder를 확인한다. 20개 유효 lifecycle 원천 거래일에도 선택 가능한 개선 후보가 없으면 `order_pattern_lab_bounded_maintenance_review`의 수리/통합/폐기 또는 근거 있는 유지 판단을 남긴다. 기존 설정의 작은 양수 코호트만으로 닫지 않는다. 과거 5개 완료 행의 매입/매도 총액 결손을 합성하거나 같은 과거일을 반복 재실행하지 않는다. 운영 env/lock/봇/주문/provider/quantity/cap/안전 변경과 외부 sync는 수행하지 않는다.

- [ ] `[DailyThresholdNaturalAcceptance0908] 소액 순이익 승인 계약의 자연 source·PREOPEN·실수익 확인` (`Due: 2026-09-08`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~21:55`, `Track: RuntimeStability`)
  - Source: [9/8 승인 재설계·교차 리뷰](../audit-reports/2026-09-08-small-net-profit-approval-review.md), [9/7 이관 이력](2026-09-07-stage2-todo-checklist.md). stable ID와 미완료 acceptance를 유지하며 과거 완료를 주장하지 않는다.
  - 첫 자연 확인: 다음 정상 코드 로드 이후 `score_recovery_real_economics_observed`의 exact identity/당시 실효 profile → 동일일 lifecycle paired의 실제 매입·매도·비용·순손익 → 같은 장후 Daily의 20거래일 real book을 대사한다. [1~3 후속 보완](../audit-reports/2026-09-08-scanner-daily-net-approval-followup-review.md)에서 기존 Entry split/AI 원천/paired owner를 Daily 앞으로 이동했고 중복 실행은 추가하지 않았다. 새 wrapper snapshot이 이 순서를 소비해야 한다. OFF/실패/source 미도착은 별도 사유로 남기며 과거 profile을 합성하거나 같은 과거일을 반복 재실행해 표본을 만들지 않는다.
  - 승인/소비: verified 당일 PREOPEN profile, full-only 20건/2일·평균−2표준오차>0·합계 net>0, partial의 순익 여력 소진/반복 손실 veto, scope 분리와 기존 AI/source/장전 guard를 확인한다. [owner 재선택](../audit-reports/2026-09-08-pattern-lab-owner-selection-followup-review.md)은 실거래 대안 한 축의 학습/holdout 비교, AI의 current/recommended/search SHA와 다음 PREOPEN 재계산을 대사한다. 통과 시 전체 profile/scoped version을 자동 전달하되 운영 lock 충돌은 별도 보류 사유로 남긴다. 기존 override를 해제하거나 수동 env/매매 재기동으로 자연 수용을 만들지 않는다. 이후 실제 시장 PID 소비·비용 차감 순익은 별도 확인한다.
  - 기존 acceptance 유지: Entry split real-only 분모, family readiness와 실제 apply 후보 분리, eligible 조정 후보만의 AI parsed review, full/partial별 실제 비용 차감 EV/순이익과 제출·체결 참여율·rollback을 확인한다. 코드 PASS·CF·과거 손익 귀속 복원은 실수익 개선이 아니다.
  - 유지 판단: 20개 유효 source 거래일 내 profile 없음/미매수/미체결/미청산·비용 결손/양수 edge 없음 중 병목과 소유자를 명시하고 `accept|keep_collecting|repair_source|rollback|retire`를 판단한다. OFF·applied 무표본 상태는 CF로 자동 최초 권한을 만들지 않으며 기존 override도 해제하지 않는다. 운영 lock·주문·수량/cap·provider·hard safety 변경은 별도 권한이다.

## 장전 체크리스트 (07:45~09:00)

- [ ] `[MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0908] micro observer 저장공간·연속수집 source gap 복구 확인` (`Due: 2026-09-08`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:45`, `Track: RuntimeStability`)
  - 11:28 보완: [WS ingress 수리 리뷰](../audit-reports/2026-09-08-ws-ingress-backlog-repair-review.md). 매 tick의 전체 history deepcopy 병목을 제거하고 raw 0B/0D 전수 관측과 coalesced 최신 full snapshot 전달을 분리했다. 305 tests PASS, 코드7077831a main push 완료. PID461794/f67a7ec7은 자연 재연결 후 유효21787/22806으로 회복했으나 새 코드 미반영이다. 동시 수정 중인 다른 src/deploy의 review·commit 확정 전에는 재기동하지 않고, 기존 승인 범위의 다음 안전한 재기동에서 PID/source/WS·broker 대사를 닫는다. 과거 loss·Provider hold·through-close는 OPEN 유지.
  - 09:53 실행: [due 작업 실행·보완](../audit-reports/2026-09-08-intraday-due-work-execution.md). writer/queue 오류 0, 여유 약10.73GB, 유효 enqueue 5739/5246→7862/6611로 재개. timestamp loss의 64개 tail은 전수 exclusion receipt가 아니므로 through-close·Provider hold는 OPEN 유지. frozen 측정/guard를 바꾸지 않고 offline storage 수리의 정확한 hash/AST 호환 검사를 보완했다.
  - 9/8 08:40 관찰: [08:50 모니터링 리뷰](../audit-reports/2026-09-08-preopen-intraday-monitoring-0850.md). disk 약11.2GB > low watermark5GiB, trade writer2/2(SOR/KRX 별도 partition)·depth writer1/1, queue/drop/worker/writer/storage-stop 0. 마지막 timestamp rejection 08:18:37 이후 새 유효 수집은 증가했지만 과거 exact exclusion과 장마감 연속성·Provider hold acceptance는 아직 OPEN이다. 원본 결손을 복원하거나 완료로 체크하지 않았다.
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-07.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-07.json)
  - 판정 기준: workorder `main-ai-gap-ed4ddcd772f6b4eced07cf72`의 owner=`MicroReversionForwardCollectorContinuity`, reason_codes=`row_exclusion_required, past_market_row_missing=18`를 source-only producer 보완으로 닫는다. 장전 free bytes가 writer low-disk watermark를 충분히 상회하는지 확인하고, 부족하면 실주문과 무관한 closed-date verified compression만 실행한 뒤 observer canary를 재검증한다.
  - 완료 조건: exact-date canary remains pass or row-exclusion-only through close; later clean windows continue collecting; provider replay remains held until queue-loss scope has an exact exclusion receipt or the next clean date
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [x] `[ThresholdEnvAutoApplyPreopen0908] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-09-08`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - 09:53 완료 근거: [실행 리뷰](../audit-reports/2026-09-08-intraday-due-work-execution.md). 당일 07:35 apply/20 selected family와 PID461794의 read-only verify PASS, missing/mismatch/finding 0. `applied_guard_passed_env`; 비선택·blocked family는 수동 우회하지 않았다. 실제 효과는 아래 장중 OPEN owner와 별개다.
  - Source: [threshold_cycle_ev_2026-09-07.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-07.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [x] `[RisingMissedScoutRuntimePreopen0908] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-09-08`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - 09:53 완료 근거: [3개 stable ID 대사](../audit-reports/2026-09-08-intraday-due-work-execution.md). main workorder에 각각 1회 `attach_existing_family`, 모두 runtime/apply false이며 selected family에 없음. `source_only_no_runtime_authority`로 귀속 확인을 닫는다. BBO source/economic floor는 미완료이고 #8/#9 상세검토를 재개하지 않았다.
  - Source: [rising_missed_scout_workorder_2026-09-07.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-09-07.json), [code_improvement_workorder_2026-09-07.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-07.json), [threshold_apply_2026-09-08.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-09-08.json), [threshold_runtime_env_2026-09-08.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-08.json), [threshold_runtime_env_verify_2026-09-08.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-08.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`3`, forced_scout_with_post_sell_count=`2`, post_sell_join_coverage_pct=`0.498753`, outcome_coverage_state=`partial`, profitable_forced_scout_count=`2`, loss_or_flat_forced_scout_count=`0`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0908] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-09-08`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - 10:03 후속 실행: 10:00 BUY Funnel을 기존 producer에 입력해 native followup6개를 메모리상 검증했다. runtime/apply false, workorder→EV→runtime summary→verifier 연결 유지. [재리뷰](../audit-reports/2026-09-08-intraday-due-work-execution.md#1003-재리뷰와-남은-작업-실행). 정식 장후 generation 발행이나 실체결 acceptance 완료는 아니다.
  - 09:53 실행: [원인 대사](../audit-reports/2026-09-08-intraday-due-work-execution.md). runtime/PID verify PASS이나 09:50 KRX submitted 0, exact attempt54=terminal48+pending6, 미분류 terminal0. spread/DANGER와 AI stale/WAIT/DROP veto를 분리했고 threshold·stale·AI guard는 유지했다. 이후 자연 전환과 장후 drought workorder/EntryRecheckNaturalAttribution0907 handoff까지 OPEN이다.
  - Source: [threshold_cycle_ev_2026-09-07.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-07.json)
  - 전일 postclose candidate_selected_families=score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, post_probe_winner_recovery, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [x] `[SimProbeIntradayCoverage0908] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-09-08`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - 09:50 현행 비우선 최소 점검 완료: [실행 리뷰](../audit-reports/2026-09-08-intraday-due-work-execution.md). Swing probe/auto policy·greenfield OFF, 독립 sim worker 미관측, scalp 저장 active0. Swing 저장 3행은 pre-baseline 2026-01-11이며 주문 false/broker forbidden true로 현재 holding/EV에 사용하지 않는다. 현재 sim 무표본을 실패·복원·성과 튜닝 지시로 바꾸지 않았다.
  - Source: [threshold_cycle_ev_2026-09-07.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-07.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0908] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-09-08`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - 10:03 선행 실행: [재리뷰·남은 작업 실행](../audit-reports/2026-09-08-intraday-due-work-execution.md#1003-재리뷰와-남은-작업-실행). 기존 lock으로 write/backfill 없는 수동 감사1회: 41529 events/72 stages, PASS, hard gap/unknown/review warning0. enqueue 전 micro 유실이나 이후 row까지 승인하지 않으며 14:20 예정 점검은 OPEN 유지한다.
  - Source: [pipeline_events_2026-09-08.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-09-08.jsonl), [threshold_events_2026-09-08.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-09-08.jsonl), [observation_source_quality_audit_2026-09-08.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-08.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-09-08 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (16:25~21:55)

- [ ] `[ThresholdDailyEVReport0908] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-09-08`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-09-07.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-09-07.json), [threshold_cycle_ev_2026-09-07.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-07.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0908] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-09-08`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-07.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-07.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0908] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-09-08`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-09-07.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-09-07.md), [code_improvement_workorder_2026-09-07.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-07.json)
  - 판정 기준: selected_order_count=15와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[MachineLifecycleTurnoverObjectiveFollowup0908] 위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인` (`Due: 2026-09-08`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_policy_approval_postclose_2026-09-07.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_2026-09-07.json), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 판정 기준: 승인 후보 수와 무관하게 `followup_required=true`인 미완료 목적 항목 `machine_lifecycle_turnover_policy_research_v1`(status=`EVIDENCE_ACCUMULATING`, next_action=`quarantine_current_source_date_and_continue_next_exact_date_collection`)의 상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.
  - 상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, `EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. `CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.
  - 권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[AutomationTriggerDecisionSummary0908] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-09-08`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-09-07.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-09-07.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`6`, skip_count=`0`, source_missing_count=`5`, force_override_count=`0`, run_steps_sample=`pattern_lab_currentness_audit, pattern_lab_ai_review, observation_source_quality_audit, pattern_lab_propagation_audit, runtime_apply_gap_audit`, skip_steps_sample=`-`, top_reasons=`disabled_by_runtime_policy:8, output_missing_or_unreadable:5, source_missing_or_unreadable:5`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

- [ ] `[PostcloseSourceQualityGateReview0908] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-09-08`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-09-08.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-08.json), [threshold_cycle_ev_2026-09-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-08.json), [code_improvement_workorder_2026-09-08.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-08.json), [threshold_cycle_postclose_verification_2026-09-08.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-09-08.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## 9/7 postclose 복구의 다음 자연 acceptance

- [ ] `[PostcloseRecoverySourceAcceptance0908] 복구 후 exact source·receipt 및 native 추천 ID 재검증` (`Due: 2026-09-08`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~21:55`, `Track: RuntimeStability`)
  - Source: [9/7 복구 검토](../audit-reports/2026-09-07-postclose-monitoring-recovery-review.md), [자정 이후 우선순위 보완](../audit-reports/2026-09-08-postclose-priority-repair-review.md), [최신 frozen native intake ledger](../audit-reports/2026-09-08-postclose-priority-repair-ledger.json). `PostcloseSourceQualityGateReview0908`과 같은 audit/workorder를 소비한다.
  - 범위: ledger의 미완료 implement-now 9건은 NXT order/attempt/owner별 실제 결손 census, unknown/N/A의 원본 provenance, micro evaluation venue 및 holding payload receipt, AI review 원본 source hash를 요구한다. 저장되지 않은 원본을 합성하거나 0으로 채우지 않는다. 전체 시장/퇴역 sim의 표본 모집은 이 항목의 권한이 아니다.
  - machine/R0: 검증된 ingress loss의 9/7 날짜 제외를 유지하고 다음 exact-date ordered/route/epoch receipt를 확인한다. 보존된 과거 R2/R3 9개 날짜의 semantic mismatch는 비압축 storage warning이며 튜닝 재사용·재생성·삭제 권한이 없다.
  - 9/7 복구 결과: CF route 관찰 3행을 실제 ADD/NO_ADD와 분리해 record 40904/40942의 NXT 체결·비용·순손익 연결을 복원했다. gap 5→2, 실제 eligible lifecycle 0→2이며 Main AI custody workorder는 제거됐다. 이는 새 수익이나 나머지 receipt/taxonomy/Telegram 계약의 전수 완료가 아니다. 과거 market 18행·legacy identity 2행을 합성하지 않는다.
  - 최종 요약 자연 확인: 9/8 wrapper의 tower→checklist→strict verifier가 `postclose_summary_sources_v1`의 같은 date/hash로 닫히고 controller 명령 실패가 과거 성공 artifact로 숨겨지지 않는지 확인한다. 완료된 #8/#9 상세검토는 재개하지 않는다.
  - 추천 대사: frozen 65행 ledger의 ID 없는 26행은 당시 canonical 산출물 기록으로 보존한다. 이후 별도 사용자 승인 구현의 [26행 native projection ledger](../audit-reports/2026-09-07-widget-episode-recommendation-ledger.json)는 원본 hash/위치와 producer native ID를 결속한 후속 근거다. 두 ledger를 91개 작업으로 합산하거나 원본을 새 경제성 산출물로 바꾸지 않는다. 새 자연 산출물의 native ID/consumer/acceptance를 대사하고 이미 승인·구현된 축은 아래 `WidgetEpisodeRecommendationApplyAcceptance0908`에서 확인한다. 나머지 9개 workorder의 증거 대기는 별개다.
  - Acceptance: 동일 corrected producer→candidate→consumer→verifier에서 source/hash/date가 일치하고, 각 기존 native ID에 신규 exact evidence 또는 직접 결함 위치가 결속됐을 때만 resolved 판정한다. source-quality-valid paired 0은 hold_sample이며 live threshold/provider/bot/order/수량/안전 변경을 허용하지 않는다.


## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

## 전일 미완료 자연 acceptance 이관

- [ ] `[EntryRecheckNaturalAttribution0907] recheck 보완 후 정상 기동 PID 소비·exact submit/fill/청산 귀속 확인` (`Due: 2026-09-08`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~21:50`, `Track: ScalpingLogic`)
  - 정기 producer 소비: 11:35 START→11:36:20 DONE, 운영 as-of11:35:20의 report6/exact3/cache12와 aggregate/KRX/PREMARKET validator PASS를 읽기 전용 확인했다. 수동 재생성 없이 진단 owner 소비는 관측됐으나 critical은 계속된다. controller·이력·PREOPEN/PID·제출/체결 acceptance까지 완료한 것은 아니다.
  - 9/8 추가 보완: [schema6/exact3 재리뷰](../audit-reports/2026-09-08-buy-funnel-entry-recheck-remediation-review.md). 10:25 raw332행의 순수 재대사 결과107=terminal107+pending0+submit0, 미분류/순서 위반0; refresh7pass/5records=AI6+가격1이다. 누락 terminal·재시도와 공통 ledger·call-local ID/종료 관측을 수리했고 기존 매매 함수 본문·guard·#23 조건은 유지했다. 다음 자연 cache12/report6/exact3와 controller/source hash를 확인하며 구 9/3·4 및 schema5/exact2의 9/7 이력을 재라벨링하지 않는다. 최소 재생성의 source 복원 가능성, 새 코드 PID의 ID 소비, PREOPEN·submit/fill/net acceptance는 OPEN이다. 봇 재기동·장후 전체 재실행·수동 canonical 재생성 없음.
  - 10:25 기준 집중 점검: [#119→#23 반례와 보완 순서](../audit-reports/2026-09-08-buy-funnel-entry-recheck-1025-review.md). 기존71=66+5+0은 재현되지만010170의 raw 가격 재검증 차단이 Sentinel cache/분류에서 누락되고, refresh5는7pass/5records이며 재시도·promotion 교체의 cycle 귀속도 갈라진다. 기존92 PASS가 이 새 결함의 종결 증거는 아니다. 수집/분류→공통 exact ledger·producer ID 전달→3거래일 구 schema 이력 달성 가능성→실제 귀속 순으로 보완 검토한다. 현재07:35 PREOPEN/PID461794의 recheck OFF는9/3·4 source gap을 정상 소비한 결과다. 이번 요청은 점검이므로 구현·강제 ON·장후 전체 재실행은 하지 않았고 F1~F3 및 기존 자연 acceptance는 OPEN으로 유지한다.
  - 이관 정정: 9/7 미완료의 동일 ID를 9/8로 이관했다. 아래 9/7 env와 07:35/07:55는 원래 계획·과거 근거이며 오늘 적용 증거가 아니다. 현행 9/8 exact-date PREOPEN/PID와 새 3거래일 history를 대사하고 다음 장후→다음 PREOPEN 연결을 구분한다. 새 기동·env 적용은 수행하지 않는다.
  - Source: [2026-09-06 최종 재점검](../audit-reports/2026-09-06-one-share-drought-final-review.md), [9월 7일 runtime env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-07.json)
  - 선행 조건: `EntryRecheckFeasibilityRepairReview0907` 보완·검증 종결. 기존 예정 07:35 PREOPEN와 07:55 기동 이후 실제 PID의 selected profile/의존 probe 계약과 장후 exact attempt→accepted submit→fill→valid terminal 귀속을 확인한다. env PASS를 실제 수익 개선으로 해석하지 않는다.
  - 추가 확인: 일일 `entry_recheck_drought_controller`가 정상 생성되고 PREOPEN manifest의 `entry_recheck_drought_controller` source로만 소비되는지 확인한다. scope별 `evaluated/armed/submitted/filled/completed/paired`, dominant evaluation blocker, `INTRADAY_ESCALATION_SCOPES`와 실제 동일-scope recovery mark/cap을 대조하며 다른 scope의 경제성이나 cap을 재사용하지 않는다. 누적 backtest 미실행일의 artifact 부재는 정상이고 controller 부재만 결함이다.
  - Sentinel 선행 계약 이행: 완료 기록 `BuyFunnelFinalContractReviewRepair0907`의 schema5/exact2 report·일반8/lossless10 cache, 날짜/scope/digest binding을 확인한다. 정확한 최근 3거래일 중 구 schema3/4나 비격리 compacted-terminal 결손이 남으면 적용 대기 사유로 명시하며 옛 보고서를 무검증 승인하지 않는다. 장기 PID의 upstream terminal raw 보존은 다음 별도 허용된 정상 기동 이후 확인한다. KRX/NXT scope를 종목/시각으로 추정하지 않으며, 식별 가능한 결손 row/scope는 제외 후 정상 원천을 유지한다. source 준비→정기 장후 controller→다음 PREOPEN→PID·실제 귀속을 확인하고, 코드 PASS를 다음 장전 적용 확정이나 수익 개선 증거로 쓰지 않는다.
  - 완료 조건: applied/not-applied·원인별 blocker·유효 경제성 pair·source gap·현재 판정 window/다음 자동 ON/OFF 근거를 보고한다. 자연 match 또는 청산 0건은 계측/자연 표본 상태로 구분하고 성공·실패·확대 승인으로 단정하지 않는다. 사용자 추가 개입 없는 정책 복귀 경로도 회귀 증거와 대조한다.
  - 현재 후속 owner: [리뷰 §10](../audit-reports/2026-09-06-one-share-drought-final-review.md#10-r1r5-구현수정재리뷰)의 controller v4/exact attempt v3 계약을 확인한다. 구 9/4 controller/기존 9/7 env의 ON을 새 코드 소비로 간주하지 않는다. 새 schema 산출물이 없어 PREOPEN에서 제외되면 버전/생성 순서 문제로 보고하고 기존 허용된 복구 절차로 source 생성→PREOPEN 재검증하며 구 성과/stop을 임의 삭제하지 않는다. 예약 원장의 ambiguous 건은 브로커 대사 없는 자동 반환을 금지한다. bot 재기동·실주문으로 검증하지 않는다.
  - 자연 수용시험: scope별 평가→arm→예약→accepted→fill→terminal→동일 fill-quality paired와 20거래일 창의 실제 전환율/표본 ETA를 보고한다. 확대 floor 달성 가능성이 낮으면 단독 causal blocker/source-contract 수리를 먼저 제안하고 신호 완화·cap 증액으로 표본을 만들지 않는다. 누적 진단은 정기 호출/의존성에서 제외된 상태를 확인한다. 미제출 arm이 NXT 한도를 소진하지 않되 기존 실제 총량은 유지되는지, 새 장후 소요시간과 비용 차감 EV를 별도로 확인한다.

- [ ] `[ScannerLookupAttentionNaturalEvidence0908] 신규 generation pair·장후 정책·다음 PREOPEN/PID 자연 적용 확인` (`Due: 2026-09-08`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~20:40`, `Track: ScalpingLogic`)
  - 9/8 승인 문턱 후속 보완: [1~3 구현 리뷰](../audit-reports/2026-09-08-scanner-daily-net-approval-followup-review.md). `small_net_v1`에서 base/holdout/R6의 고정 +0.10%p를 양수 순EV·원화 net와 거래일 cluster를 반영한 불확실성 여유로 대체한다. 새 source 날짜의 계약 누락은 거부한다. source·실체결·독립 holdout·tail guard는 유지하며 CF 교체 pair를 실제 candidate/control 인과 증분으로 바꾸지 않는다. `economic_acceptance`의 빈도·일별 net·자본시간(null 허용), 20유효 source일 유지·통합·폐기 사유를 확인한다. 코드 검증과 자연 정책/PID/실수익은 별도다.
  - 선행/관측 정정: 9/7 13:19 부분 census(resource row36, generation1/1일, candidate0/control5, reorder0)는 구 v1 자료다. R1~R5 코드 종결 후 새 코드가 정상 배포된 자연 PID의 resource v2·decision v4를 확인한다. 이번 작업은 봇 재기동/운영 정책 발행을 수행하지 않았다. 이 항목은 9/8 postclose와 다음 장전/PID 적용을 소유하며 실제 소비 증거까지 완료 처리하지 않는다.
  - Source: [최종 구현·리뷰](../audit-reports/2026-09-07-scanner-lookup-attention-final-review.md), `data/report/scanner_lookup_attention_tuning/scanner_lookup_attention_tuning_2026-09-08.json`, `data/threshold_cycle/scanner_lookup_attention_policy/scanner_lookup_attention_policy_2026-09-08.json`. 새 코드가 반영된 자연 PID에서 KRX 정규장 candidate의 generation/code/rank/tier/owner/예약 partition, base/counterfactual score와 promoted/capacity-pruned terminal을 대사한다.
  - 완료 조건: 비조회순위 경쟁군 포함 partition count/code hash·scanner 자격·실제 선택 재현과 같은 후속 generation(180~360초) 관측 label을 확인한다. invalid는 해당 partition만 제외하고 raw/retained·제외 사유를 보고한다. `not_observed`/`no_capacity_competition`/`hold_no_effect`/`hold_sample`/`hold_no_edge`를 구분한다. 비중복 pair3/2일의 양수 incoming 및 증분 proxy와 별도 실제 full-fill base·독립 holdout EV가 모두 통과하면 다음 거래일09:00 전 receipt가 자동 발행되고 해당 hash가 scanner→runtime attach→R6에 이어져야 한다. 장중 전일 파일 변경은 적용값을 바꾸지 않아야 한다. 20관찰일 동안 유효 교체가 없으면 독립 보너스/장후 평가를 기존 scanner 진단에 통합할지 재검토한다. 표본을 만들기 위한 slot/threshold/수량 완화나 bot 재기동은 이 항목의 권한이 아니다.

- [ ] `[AIDecisionActionOutcomeNaturalEvidence0908] #76→R0–R3→#82→optimizer→후속 consumer 자연 handoff 검증` (`Due: 2026-09-08`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~21:55`, `Track: ScalpingLogic`)
  - 복구 후 경계: 9/7 source를 9/8에 provider0로 재생성해 lifecycle custody gap5→2와 consumer terminal을 확인했다. 복원된 NXT2건은 새 prompt 효과가 아니며 legacy identity2행·market18행·Entry control0/holding checkpoint는 별도다. 기존 custody 수리 기록은 완료 근거로 보존하고 새 자연 결손은 `PostcloseRecoverySourceAcceptance0908`과 대사한다.
  - 3차 연결 확인: 9/7 이후 cycle의 R2/R3 hash와 current-axis postclose terminal, 다음 PREOPEN의 disabled/미승인/실패/적용 상태를 구분한다. 등록·승인·배포 없이 실제 적용을 기대하지 않으며 향후 허용된 적용의 exact request 전달/철회 census를 #76/#82 경제성과 구분한다. 최초 활성화 준비는 `MainAICurrentAxisActivationReadiness0908`가 소유한다.
  - 2차 보완 확인: 정상 `source_only_no_new_sample`, 연구 v2의 5일/10·20일 진단 분리, full/probe partition, 9/7 이후 Provider 연구 하한 5/5/3 및 #80 `r3_research_handoff` source hash/상태를 대사한다. 경제성 준비와 runtime 최초 승인·배포는 별도다.
  - #77 선행 확인: [R0–R3 리뷰](../audit-reports/2026-09-07-main-ai-r0-r3-remediation-review.md)의 `research_candidates`/full-gate `candidates` 분리, 5/10/20일 표본·paired 명목 비교·gap 수, exact R2 hash/권한/목록 검증과 postclose 및 다음 정상 PREOPEN의 #81 `retired_disabled` SKIP를 확인한다. valid empty·hold_sample·hold_no_edge·source gap을 분리하며 표본/실수익을 합성하지 않는다. 실제 Provider는 기존 승인된 budget/source gate 안에서만 자연 실행한다.
  - Source: [#76→#82 최종 보완 리뷰](../audit-reports/2026-09-07-ai-decision-action-outcome-calibration-final-review.md), `data/report/ai_prompt_detailed_paired_replay/`, `data/report/ai_decision_action_outcome_calibration/`, `data/report/main_ai_prompt_optimizer/`.
  - 판정 기준: terminal detailed artifact의 canonical hash/부분 성공 learning contract와 exact stage/venue/session/prompt/contract identity, #82 policy v5 accepted/excluded/current count, thin-positive/review-ready, optimizer 누적경제성 소비·당일 선택 고정·다음 세션 권고, metadata-only batch 재결속과 consumer 동일 hash를 대사한다. lifecycle custody 결손은 기존 `MainAIQualitySourceGapRuntimeExecutionReceiptCustodyRepair0907` owner에 연결한다.
  - 완료 조건: 21:05 후속 상세 재현 뒤 #82가 다시 생성되고 source generation이 optimizer/consumer까지 일치하며 central contract 검증이 PASS해야 한다. 호출 실패 행은 제외되고 정상 행은 보존되어야 한다. #81 legacy는 OFF이므로 R3가 생겨도 자동적용 경로로 보지 않는다. 지원되는 V2.14/V2.15 KRX만 기존 entry_setup_live_policy의 독립 promotion·PREOPEN·receipt 판정을 참조하고, 미지원 cohort는 source-only로 종결한다. 표본/EV 부족과 source gap·registry 고갈은 분리한다.
  - 금지: 표본을 만들기 위한 실주문, threshold/수량/cap/provider/bot/broker/hard-safety 변경, hashless legacy 자료의 live 근거 승격, #82 advisory의 직접 runtime 적용.

## 장전 모니터링 보고 수리의 자연 acceptance

- [x] `[ScannerPremarketCensusNaturalAcceptance0908] census 장전 예정 구간 분모 보완의 자연 report 소비 확인` (`Due: 2026-09-08`, `Slot: INTRADAY`, `TimeWindow: 09:15~09:20`, `Track: RuntimeStability`)
  - 09:53 완료 근거: [자연 generation 검증](../audit-reports/2026-09-08-intraday-due-work-execution.md). 09:15 target-date/hash report에서 required-window 필드, NXT 장전 정상과 due KRX/NXT cadence 결손 실패를 함께 확인했다. 해당 진단 수리만 닫으며 전체 scanner recall·BBO/경제성 floor는 미완료다. 다음 정기 12:00 report 관찰은 RuntimeEnvIntradayObserve0908에서 이어간다.
  - Source: [08:50 모니터링 리뷰](../audit-reports/2026-09-08-preopen-intraday-monitoring-0850.md), [producer](/home/ubuntu/KORStockScan/src/engine/monitoring/market_opportunity_census.py).
  - 확인: 08시 NXT-only snapshot의 빈 KRX는 `required_in_observed_window=false`이며 정규장 이후 due KRX/NXT 결손은 계속 cadence 실패여야 한다. 09:15 설치 trigger의 자연 report에서 이 필드와 target date/source hash를 확인한다. 현재 시각 source freshness는 snapshot 기준 cadence와 별도 확인한다.
  - 완료 조건: 예정 구간 오탐 제거와 missing due-session fail-closed가 실제 consumer에서 확인됨. NXT census와 PREMARKET_KRX_LIKE scanner를 cross-venue join하지 않고 BBO/terminal/economic floor를 유지한다. 코드 수리의 acceptance이며 양수 EV·runtime 승격을 요구하지 않는다.
  - 권한: source-only report/검증. 매매 process·env·threshold·provider·주문·수량·broker guard 변경 없음.

## 사용자 승인 추천의 9/8 적용 acceptance

recheck·lookup-attention·AI 자연 확인 3개는 위 이월 절의 동일 ID가 현재 owner다. 9/7 원 문서에는 이관 기록·과거 근거를 보존했다. 나머지 과거 링크는 해당 상태를 확인하며 완료 기록을 새 승인으로 바꾸지 않는다.

- [ ] `[WidgetEpisodeRecommendationApplyAcceptance0908] 위젯·에피소드 승인 추천의 exact-date 기동 및 owner 귀속 확인` (`Due: 2026-09-08`, `Slot: INTRADAY`, `TimeWindow: 08:57~14:45`, `Track: RuntimeStability`)
  - 10:03 후속 실행: SD morning liquidity guard/NO_TRADE(09:40:06), NHN morning scan-window-closed/NO_TRADE(09:51:01), 두 service Result success/exit0/position0 확인. 옛 순서 receipt를 새 hash로 묵시 정규화하지 않는 회귀 추가 후 관련295 tests PASS. [재리뷰](../audit-reports/2026-09-08-intraday-due-work-execution.md#1003-재리뷰와-남은-작업-실행). 이후 신규 midday/afternoon timer와 자연 signal/다음 정상 PID receipt는 OPEN이다.
  - 09:53 실행·보완: [위젯 hash 결정성 수리](../audit-reports/2026-09-08-intraday-due-work-execution.md). 080220 정책/현재 eligible state와 collector PID249964·trader PID21846 확인. blocked 상태 tuple 정렬을 보완했으며 기존 시작 receipt는 원래 순서를 재구성한 hash로만 검증했다. 새 코드 PID 반영·현재 signal별 소비를 주장하지 않고 재기동하지 않았다. TYM은 guard에 따른 정상 NO_TRADE/NO_FILL이며, 다음 정상 로드의 결정적 receipt와 나머지 예약 window·자연 신호/owner 귀속은 OPEN 유지.
  - Source: [구현·적용 검토](../audit-reports/2026-09-07-widget-episode-recommendation-implementation-review.md), [추천 원장](../audit-reports/2026-09-07-widget-episode-recommendation-ledger.json), [승인 evidence](../audit-reports/2026-09-07-low-price-recommendation-apply-evidence.json).
  - 승인 범위: 사용자 9/7 지시의 9/8 적용. Low-price 기존 수정8/신규3의 11건, 전체56/runtime eligible53 및 기존 quarantine3 유지. Widget080220 exact-date policy 사용. 미달 후보나 다른 profile의 자동 승격 권한은 없다.
  - 확인: TYM 오전09:05/09:09, NHN 정오13:25/13:29, 에스디바이오센서 오후14:10/14:14의 preflight/live timer, exact-date applied hash와 authority receipt/PID를 연결한다. 위젯 collector08:57와 실제 trader 정책 ID, 신규 자연 신호를 확인한다. 예약 전은 not_yet_due이며 실패 guard를 완화하지 않는다.
  - 완료 조건: 승인 profile의 해당 window별 natural preflight·PID 및 신호/valid-empty receipt, 독립 order/custody와 기존 holding target 보존을 확인한다. 매도 terminal과 비용 차감 손익은 실제 표본이 있을 때 별도 귀속하고 코드 완료나 policy publish를 EV 성공으로 세지 않는다.
  - Rollback: exact-date/hash/source 불일치는 해당 신규 진입 fail-closed. 사용자 재검토 뒤 다음 PREOPEN에서 이전 revision을 선택하며 기존 보유/target 주문은 당시 owner 계약을 유지한다.
