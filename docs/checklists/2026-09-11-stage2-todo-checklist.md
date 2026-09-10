# 2026-09-11 Stage2 To-Do Checklist

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

## 전일 승인 배포의 다음 거래일 확인

- [ ] `[MachineProfitStagnationStartupAcceptance0911] 배포된 최소 보조청산의 다음 거래일 service·정책·신규 entry 소비 확인` (`Due: 2026-09-11`, `Slot: INTRADAY`, `TimeWindow: 07:55~14:35`, `Track: RuntimeStability`)
  - 9/11 08:13 오류 수리: [owner scope 수리](../audit-reports/2026-09-11-owner-scope-startup-repair.md). 07:32 LX108320 marker/라벨 누락으로 당일 owner policy 발행 실패, 삼성 preflight는 전일 정책 소비로 ownership source 결손/매매PID0. 격리 수리f6fa0f9e/85 tests PASS, code_review_closed이나 미배포다. 원07:54 적용창 이후 당일 복구·매매 재기동/고정 release 반영은 별도 승인 범위 확인이 필요하며 stale policy로 우회하지 않는다. main14564·widget15604 실행과 신규 entry 성공은 별도다. SK텔레콤 전일 SELL0022607은 공통 원장 정상 terminal, 에피소드 HELD10 미정리로 실제 보유와 구분한다. 본 owner OPEN 유지.
  - 9/11 07:32 사용자 “오늘만 신규1주” 승인 반영: [1일 수량 배포](../audit-reports/2026-09-11-one-day-machine-quantity.md), 위젯/삼성427ab86e·저가주5abbf613 및95 drop-in9개/로드된129개 경로 대사. 오늘 새 leg1주(episode2개 총2주), 기존10주 보유/접수 주문 보존. 기존3개 policy pin·예약은 유지하며 현재PID0/미래 기동 미확인이다. 본 owner의 자연 신규 entry 확인에서 `new_entry_quantity_receipt`와 실제 주문 원장 수량을 함께 확인한다. 원칙상의 기본10/총20 승인 정책과 오늘 사용자 override를 구분한다.
  - 9/11 승인 후속: [추천 구현·배포](../audit-reports/2026-09-11-widget-episode-approved-deployment.md), [18행 successor](../audit-reports/2026-09-11-widget-episode-approved-ledger.json). 롯데 오후 개선/정오 신규·LX세미콘 오전 신규3개를 기존 gate 통과 후 반영. low-price 별도90 drop-in/신규 timer4개·변경2개와07:32 exact owner scope를 대사한다. 나머지15행의 보류/차단/거절/관찰은 유지하며 미래 실제 PID·신규 entry·경제성은 OPEN.
  - 실제 배포00:20 KST: low-price4f073800/90 drop-in2개, 공통 consumer340c1d00, widget PID2651657/f9d53a9a 유지. 기존 롯데 오후 timer reload의00:20 조기 preflight는 종료·예약 복구했고 exact9/11 applied 정책은 원시각으로 보존했다. 정상 다음 preflight/실제 PID·경제성 완료가 아니며09:40/09:44·13:10/13:14·14:20/14:24 예정으로 대사한다.
  - Latest deployment 2026-09-10 23:53 KST: [전체 scope 추가기능 배포](../audit-reports/2026-09-10-approved-additions-deployment.md), `data/runtime/machine_additions_deployment.json`; machine `f9d53a9a`, widget PID2651657/23:53:08, 9개80-drop-in과 세 policy pin 확인. 진입 직전 악화 보류·WS 목표 상향을 기존 위젯/에피소드 전체의9/11 신규 신호/진입부터 지속 적용. 기존 보유 제외·timing conflict·수량/안전 guard 유지. 다음날 자연 소비/경제성은 OPEN. 아래19:19 receipt는 이전 배포 이력이다.
  - Source: [9/10 별도 승인 배포](../audit-reports/2026-09-10-machine-profit-stagnation-deployment.md), `data/runtime/machine_profit_stagnation_deployment.json`. 사용자 승인으로9/11 신규 진입부터 동일 설정을 이후 거래일에도 유지. machine 릴리스273807e3/9개 service·preflight drop-in 설치, widget PID1138215 기동·정책 pin hash 검증 완료. main/장후 selector/PID/cron은 불변이다.
  - Acceptance: widget 기존 새 PID의 연속 가동 또는 이후 정당한 새 PID·정책 PATH/SHA256, 삼성07:57/13:14/13:59 및 저가주 profile별 자연 timer/preflight 경로,9/11 실제 신규 entry에서 policy selected/직접 blocker, 이전 보유 미편입·정확한 수량/target 보존을 확인한다. 연속 가동 widget의9/10 startup receipt를9/11 신규 기동 receipt라고 표시하지 않는다. 오늘 빈 entry timestamp의 missing-evidence 표시와 유효 신규 entry 결손을 구분한다.
  - Handoff: 자연 주문 전환·실제 비용/순이익·자본점유는 기존 MachineLifecycleTurnoverObjectiveFollowup0910의 후속 장후 owner에 연결한다. 미관측 표본은 not_yet_observed이며 강제 주문/기동/원장 편입 또는 정책 확대 권한이 아니다. rollback은 열린 보조 주문의 terminal/원 목표 복원 대사 뒤 시행한다.
  - 9/10 장후 인계: 같은 ID/Due/Acceptance를9/11 실행 파일로 이관했다. [장후 최종 대사](../audit-reports/2026-09-10-postclose-monitoring-resume-review.md). 예약 경로/pin의 사전 검증이며 미래 PID/신규 entry 성공은 not_yet_due다.

- [ ] `[KRXDaily100NextDayStartupAcceptance0911] KRX 일일100 정책과 다음날 실제 기동 경로 확인` (`Due: 2026-09-11`, `Slot: PREOPEN`, `TimeWindow: 07:30~08:05`, `Track: RuntimeStability`)
  - 9/11 최신 소스 대사: [전수 점검](../audit-reports/2026-09-11-full-recommendation-deployment-audit.md). main 정체청산 adapter의 공통 함수 추출은 Git 통합 대상이나 선택939d90f6에는 미배포이며 의존성 `src/trading/order/profit_stagnation.py`도 필요하다. 기존 연산 parity 검증 완료/현행 기동 필수 blocker 아님. 배포 교체와07:35 정책·07:55 PID 수용을 분리한다.
  - Latest deployment 2026-09-10 23:51 KST: 공통 수리 배포 `939d90f6`/`postclose-repaired-20260911`, cron9/공유 경로와 V2.14 승인 코드10개 hash 일치. [배포 근거](../audit-reports/2026-09-10-approved-additions-deployment.md). 9/11 PREOPEN activation/env·07:55 실제 PID는 예정 전이며 본 ID OPEN 유지.
  - 경로 수리 리뷰: [9/10 routing review](../audit-reports/2026-09-10-runtime-release-routing-review.md). start env/log 보존·실제 cron 명령 판별·조회 lock 부작용을 보완했다. workspace bootstrap 수정과 선택 b665e0a3/실제 PID 세대를 구분하며, cron 재설치·선택 교체·매매 재기동 없이 내일 기존 예약/정책 소비를 확인한다.
  - 장후 handoff: [장후 지시문 §8.8](../postclose-tuning-result-review-task-instructions.md#88-다음-거래일-preopen0755-기동-handoff)에 따라 선택 원장/root/commit·cron9행·실제 장후 worker 세대, 다음 거래일 후보/source hash·정책 blocker·미배포 수리/rollback을 기록한다. 장후 준비 확인은 다음날 PID 성공이나 재기동 승인으로 대신하지 않는다. 이 문서 현행화에서는 실제 장후/배포/기동을 실행하지 않았다.
  - Source: [고정 배포·재기동 영향 점검](../audit-reports/2026-09-10-entry-intraday-activation-review.md)의 과거 작업폴더 경로는 9/10 18:31 승인 설치로 해소했다. [설치 근거](../audit-reports/2026-09-10-fixed-release-postclose-startup-review.md): 07:35/07:55 및 workspace restart는 공통 선택 `unified-runtime-20260910`/b665e0a3를 사용한다. 선택 원장·소스 clean·공유 state와 cron drift 검증은 설치 완료이며, 내일 실제 후보/PID 소비는 아직 미래 상태다.
  - Acceptance: source9/10의 KRX 후보 및9/11 activation 또는 정확한 blocker, 실제 PID root/commit/dirty·runtime verify, V2.14/1주/정책 cap100/두 env budget100, 오늘 pin 미상속·날짜별 quota, WS/Provider 첫 소비를 분리 확인한다. 후보0/미승인은 강제 BUY로 복구하지 않으며 NXT/다른 owner와 safety는 불변이다. 사전 artifact 정상은 실제 자연 기동·체결·순이익 완료가 아니다.
  - 9/10 장후 인계: 같은 ID/Due/Acceptance를9/11 실행 파일로 이관했다. [장후 최종 대사](../audit-reports/2026-09-10-postclose-monitoring-resume-review.md). 예약 경로/pin의 사전 검증이며 미래 PID/신규 entry 성공은 not_yet_due다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-09-10", "sources": {"automation_chain_trigger_decision": {"sha256": "42f94d595d35bcba8266d68cf804cd7551877fc6916f62e5cc241bff20179173"}, "code_improvement_workorder": {"sha256": "4f370dc934663b510f80054ccacedf762d40a1a7e9c9e30e5e0c360aa5388572"}, "disposition_evidence_0_0": {"sha256": "8a5e7312a8fb6a7c9ec8facdff8cd79dbbc9b91017c353c390f7aeadc9316a6f"}, "disposition_evidence_10_0": {"sha256": "8a5e7312a8fb6a7c9ec8facdff8cd79dbbc9b91017c353c390f7aeadc9316a6f"}, "disposition_evidence_11_0": {"sha256": "8a5e7312a8fb6a7c9ec8facdff8cd79dbbc9b91017c353c390f7aeadc9316a6f"}, "disposition_evidence_12_0": {"sha256": "8a5e7312a8fb6a7c9ec8facdff8cd79dbbc9b91017c353c390f7aeadc9316a6f"}, "disposition_evidence_13_0": {"sha256": "8a5e7312a8fb6a7c9ec8facdff8cd79dbbc9b91017c353c390f7aeadc9316a6f"}, "disposition_evidence_14_0": {"sha256": "8a5e7312a8fb6a7c9ec8facdff8cd79dbbc9b91017c353c390f7aeadc9316a6f"}, "disposition_evidence_1_0": {"sha256": "8a5e7312a8fb6a7c9ec8facdff8cd79dbbc9b91017c353c390f7aeadc9316a6f"}, "disposition_evidence_2_0": {"sha256": "8a5e7312a8fb6a7c9ec8facdff8cd79dbbc9b91017c353c390f7aeadc9316a6f"}, "disposition_evidence_3_0": {"sha256": "8a5e7312a8fb6a7c9ec8facdff8cd79dbbc9b91017c353c390f7aeadc9316a6f"}, "disposition_evidence_4_0": {"sha256": "8a5e7312a8fb6a7c9ec8facdff8cd79dbbc9b91017c353c390f7aeadc9316a6f"}, "disposition_evidence_5_0": {"sha256": "8a5e7312a8fb6a7c9ec8facdff8cd79dbbc9b91017c353c390f7aeadc9316a6f"}, "disposition_evidence_6_0": {"sha256": "8a5e7312a8fb6a7c9ec8facdff8cd79dbbc9b91017c353c390f7aeadc9316a6f"}, "disposition_evidence_7_0": {"sha256": "8a5e7312a8fb6a7c9ec8facdff8cd79dbbc9b91017c353c390f7aeadc9316a6f"}, "disposition_evidence_8_0": {"sha256": "8a5e7312a8fb6a7c9ec8facdff8cd79dbbc9b91017c353c390f7aeadc9316a6f"}, "disposition_evidence_9_0": {"sha256": "8a5e7312a8fb6a7c9ec8facdff8cd79dbbc9b91017c353c390f7aeadc9316a6f"}, "entry_recheck_drought_controller": {"sha256": "389a542cf11c0736ca0e5ff30c2cdaa09bcfd738412b7e20ca4b138b41f59f13"}, "low_price_two_leg_expanded_candidate_research": {"sha256": "c42fe91eb1c59bb9896775f223fade53b5998a8bd6b094c7d7aafb3bde284f73"}, "low_price_two_leg_tuning": {"sha256": "642908827ba254da5baad165de016bc97d58ba78b91be64de0f44734875c79ff"}, "machine_entry_timing_tuning": {"sha256": "010a12acea4f03df318c132eebfa76f2f2233007d50ba2d011262ae7acab4122"}, "machine_microstructure_attribution": {"sha256": "d2c050106bdf62bd69388be7c869cce01a071903b7846458ce62e90bcb893162"}, "machine_microstructure_policy_approval": {"sha256": "5d70a63786edaedd80257d10dd1144a2de447042393b85b4117ff540bb170bdf"}, "main_ai_quality_r0_r3": {"sha256": "525457b0167ce6354ef54319ac596048f556da4edb6e0fa2b7d9dc9185a8ffd2"}, "postclose_recommendation_dispositions": {"sha256": "f5f348c8af04f8c3cca08404566c9920470994eefdb97f01f3db8e7dc1118a78"}, "preopen_apply_plan": {"sha256": "34f420110b47d5d818554d96774afcd1c731a173a2d03c3a1d10d0cdffb73f13"}, "preopen_pid_verification": {"sha256": "4abd1733d740fa943d274abe93696149379e240885bb4588fc5d1fe4d0d9b2ae"}, "preopen_runtime_manifest": {"sha256": "9c4de3fe30e2fca616ff4a7fe22cf4b436167f510c05701b859feaa8d26aa97b"}, "rising_missed_scout_workorder": {"sha256": "c99a74123dff27a14f34fa92811054589f7f0a6abda50b61f1cd32e6ef6a47ff"}, "runtime_apply_gap_audit": {"sha256": "c2bdcd2e2da0959d5a28af40e5750ac9eb4fe8b9c7b71d56d30165eca561a4d5"}, "samsung_machine_entry_tuning": {"sha256": "89b2d355b787c55a09742c438b5b4ca9f46f8b8ce1f5c498a466f75cd93c7701"}, "threshold_cycle_ev": {"sha256": "c363c3f7d37ac0a21bfd4075a39c2669085834ef332425050821128b5a573f73"}, "tuning_performance_control_tower": {"sha256": "825d4207aad97777003bf069df4db2b98ae6c272d1f500a98fb43ea72bd1edde"}, "widget_advisory_calibration": {"sha256": "077f2c0d229967204b97bed822821937e05156900fa3741869ff1104d202480d"}, "widget_auto_trade_policy_calibration": {"sha256": "c29687db7a44daec14c4aa3e654d8d9587019d0f5abff8a0ace60e7e01ade077"}, "widget_collector_expansion_recommendation": {"sha256": "11220bda0f8c02ae63a359755a005ee586f66b36444c645ad447125c9f893b30"}, "widget_symbol_runtime_policy_apply": {"sha256": "a6de994b32a9437e403529a8d1d472e04a9e13d3d97330e38dd39521ea0d922b"}, "widget_symbol_signal_policy_research": {"sha256": "f4c9e0166e439464dbb202494ce5bdbaad2679df6f3e74453f32111b635de5fa"}}} -->
<!-- POSTCLOSE_RECOMMENDATION_INTAKE_START -->
## 추천 전수 전달 대사

- source-date: `2026-09-10`; status: `warning`
- native rows SHA256: `fa7556b4b9ff01c8e2fb3d7a6dbbb24dd2986884611c4c7fd395c67d47b79aa9`
- counts: `{"already_implemented_verified_eligible": 0, "already_implemented_verified_nonrequest": 0, "blocked_external_dependency": 0, "blocked_external_dependency_nonrequest": 0, "blocked_missing_evidence": 15, "blocked_missing_evidence_nonrequest": 2, "deferred": 20, "eligible_actionable_open": 0, "eligible_runtime_effect_false_total": 15, "implement_now_unaccounted_count": 0, "implementation_requested_total": 15, "implemented_pass1": 0, "implemented_pass2": 0, "intake_total": 67, "intake_unaccounted_count": 0, "invalid_or_missing_authority_nonrequest": 0, "invalid_or_missing_authority_total": 0, "nonimplementation_total": 52, "observed_no_patch": 27, "rejected": 3, "user_authority_nonrequest": 0, "user_authority_total": 0}`
- dispositions: `{"blocked_missing_evidence": 17, "deferred": 20, "observed_no_patch": 27, "rejected": 3}`
- 운영 terminal, 구현 fixed-point, PREOPEN 선택, PID 소비, 경제성은 별도 상태다.

| Owner | Native recommendation dispositions |
| --- | --- |
| low_price_two_leg_expanded_candidate_research | `{"blocked_missing_evidence": 1, "deferred": 5}` |
| machine_microstructure_attribution | `{"observed_no_patch": 1}` |
| main | `{"blocked_missing_evidence": 15, "deferred": 8, "observed_no_patch": 26}` |
| widget_collector_expansion_recommendation | `{"deferred": 7}` |
| widget_symbol_signal_policy_research | `{"blocked_missing_evidence": 1, "rejected": 3}` |
<!-- POSTCLOSE_RECOMMENDATION_INTAKE_END -->

## 자동 생성 체크리스트 (`2026-09-10` postclose -> `2026-09-11`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (07:45~09:00)

- [ ] `[MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0911] micro observer 저장공간·연속수집 source gap 복구 확인` (`Due: 2026-09-11`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:45`, `Track: RuntimeStability`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-10.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-10.json)
  - 판정 기준: workorder `main-ai-gap-bcac5db7e4fcd80fe58d6580`의 owner=`MicroReversionForwardCollectorContinuity`, reason_codes=`row_exclusion_required, past_market_row_missing=0`를 source-only producer 보완으로 닫는다. 장전 free bytes가 writer low-disk watermark를 충분히 상회하는지 확인하고, 부족하면 실주문과 무관한 closed-date verified compression만 실행한 뒤 observer canary를 재검증한다.
  - 완료 조건: exact-date canary remains pass or row-exclusion-only through close; later clean windows continue collecting; provider replay remains held until queue-loss scope has an exact exclusion receipt or the next clean date
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[ThresholdEnvAutoApplyPreopen0911] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-09-11`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-10.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.

- [ ] `[RisingMissedScoutRuntimePreopen0911] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-09-11`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-09-10.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-09-10.json), [code_improvement_workorder_2026-09-10.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-10.json), [threshold_apply_2026-09-11.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-09-11.json), [threshold_runtime_env_2026-09-11.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-11.json), [threshold_runtime_env_verify_2026-09-11.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-11.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`5`, forced_scout_with_post_sell_count=`5`, post_sell_join_coverage_pct=`1.201923`, outcome_coverage_state=`partial`, profitable_forced_scout_count=`3`, loss_or_flat_forced_scout_count=`2`, current_missed_count=`0`)의 outcome join coverage와 code-improvement order를 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0911] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-09-11`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - source9/10 main drought KRX267AI/6submit·NXT64/0, recheck 자연 비용/정책/PID의 잔여를 인계한다. 기존 floor·scope와 원 source hash를 보존하고 새 exact date/최초 bottleneck→다음 consumer를 확인한다. 과거 missing scanner rank10·WS repair/volume/anchor를 raw 합성하지 않는다. [전수 근거](../audit-reports/2026-09-10-postclose-monitoring-resume-review.md).
  - Source: [threshold_cycle_ev_2026-09-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-10.json)
  - 전일 postclose candidate_selected_families=score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, post_probe_winner_recovery, entry_opportunity_recheck_runtime, holding_decision_context_v1, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0911] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-09-11`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - source9/10 SimProbeIntradayCoverage0910의024060 과거 terminal 결손은 원천 부족으로 유지한다.19:45 active0만으로 과거 lifecycle 완료를 주장하지 않으며 actual_order_submitted=false·새 원천과 원 record identity를 확인한다. [장후 대사](../audit-reports/2026-09-10-postclose-monitoring-resume-review.md).
  - Source: [threshold_cycle_ev_2026-09-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-10.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0911] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-09-11`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-09-11.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-09-11.jsonl), [threshold_events_2026-09-11.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-09-11.jsonl), [observation_source_quality_audit_2026-09-11.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-11.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-09-11 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (16:25~21:55)

- [ ] `[ThresholdDailyEVReport0911] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-09-11`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-09-10.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-09-10.json), [threshold_cycle_ev_2026-09-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-10.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0911] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-09-11`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-10.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-10.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0911] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-09-11`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - source9/10 인계: [장후 복구·전수 ledger](../audit-reports/2026-09-10-postclose-monitoring-resume-review.md), [수리 검증](../audit-reports/2026-09-10-postclose-source-repair-validation.md). native15 direct evidence blockers, main AI exact3/net4/paired14의 같은 부모 교집합과 Pattern consumer 결손을 기존 source owner로 확인한다. a023ca6a(기존5104a5c0 포함)의 code_review_closed/recovery_artifact_verified와 selected_release_updated=false를 구분한다. 선택b665에는 공유 경로 수리가 없어 다음 자연 장후 재발 가능성이 남는다. 검토 commit·범위·정책 pin·안전한 chain 종료·rollback을 갖춘 별도 배포 승인 없이는 selector/cron/PID를 바꾸지 않는다.
  - Source: [code_improvement_workorder_2026-09-10.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-09-10.md), [code_improvement_workorder_2026-09-10.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-10.json)
  - 판정 기준: selected_order_count=27와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[MachineLifecycleTurnoverObjectiveFollowup0911] 위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인` (`Due: 2026-09-11`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: ScalpingLogic`)
  - source9/10의 WidgetEpisodeApprovedNextDayExecution0910/MachineLifecycleTurnoverObjectiveFollowup0910 잔여 인계: [전체 수용조건과 당일 별도 개발 이력](2026-09-10-stage2-todo-checklist.md), [장후 분모](../audit-reports/2026-09-10-postclose-monitoring-resume-review.md). actual timing2/eligible0·4군paired0와 과거 보유/수동 successor/원 비용을 분리한다. 진입악화 보류·WS목표 상향은 별도 미배포 개발 권한이며 최소 보조청산273807e3 지속pin과 혼합하지 않는다. 기존 acceptance를 축소하지 않고 신규 source·consumer/정산·비용후 순익/빈도/tail/자본시간을 확인한다.
  - Source: [machine_microstructure_policy_approval_postclose_2026-09-10.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_2026-09-10.json), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 판정 기준: 승인 후보 수와 무관하게 `followup_required=true`인 미완료 목적 항목 `machine_lifecycle_turnover_policy_research_v1`(status=`EVIDENCE_ACCUMULATING`, next_action=`repair_excluded_source_report_contracts_and_rerun`)의 상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.
  - 상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, `EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. `CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.
  - 권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[AutomationTriggerDecisionSummary0911] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-09-11`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-09-10.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-09-10.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`6`, skip_count=`0`, source_missing_count=`5`, force_override_count=`0`, run_steps_sample=`pattern_lab_currentness_audit, pattern_lab_ai_review, observation_source_quality_audit, pattern_lab_propagation_audit, runtime_apply_gap_audit`, skip_steps_sample=`-`, top_reasons=`disabled_by_runtime_policy:8, output_missing_or_unreadable:5, source_missing_or_unreadable:5, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

- [ ] `[PostcloseSourceQualityGateReview0911] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-09-11`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-09-11.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-11.json), [threshold_cycle_ev_2026-09-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-11.json), [code_improvement_workorder_2026-09-11.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-11.json), [threshold_cycle_postclose_verification_2026-09-11.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-09-11.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```


## 사용자 승인 1일 수량 override 후속

- [ ] `[MachineOneDayQuantityExpiryAcceptance0914] 9/11 신규1주 override 만료·다음 거래일 신규10주 복귀 확인` (`Due: 2026-09-14`, `Slot: INTRADAY`, `TimeWindow: 07:55~15:30`, `Track: RuntimeStability`)
  - Source: [1일 수량 구현/배포 receipt](../audit-reports/2026-09-11-one-day-machine-quantity.md), `data/runtime/machine_one_day_quantity_deployment.json`, 실제 machine PID/code·신규 signal feature/entry execution policy.
  - Acceptance: 9/12 00:00 KST 이후 신규 배정10/episode2개 총20의 자동 복귀와 실제 소비 code를 읽기 전용 대사한다. 자연 신규 신호가 있으면 원장 수량을 확인하며, 신호0을 실패로 만들거나 주문을 강제하지 않는다. 9/11에 이미 생성·접수·보유한1주 lot은 원래 수량으로 관리되고 신규10주와 섞어 재작성되지 않아야 한다. 배포·재시작·새 승인 재발행은 기본 요구가 아니다.
