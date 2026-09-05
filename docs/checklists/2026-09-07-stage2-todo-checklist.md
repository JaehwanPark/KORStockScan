# 2026-09-07 Stage2 To-Do Checklist

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

## 수동 보강 체크리스트

- [x] `[SamsungEntryFinalReviewDecision0907] Samsung 진입 목적 불일치·후보 근거 결함의 보완 범위 판정` (`Due: 2026-09-07`, `Slot: PREOPEN`, `TimeWindow: 07:00~07:20`, `Track: ScalpingLogic`)
  - Source: [Samsung 최종 목적·자동화·달성 가능성 리뷰](../audit-reports/2026-09-05-samsung-machine-entry-final-review.md), [samsung_machine_entry_tuning.py](/home/ubuntu/KORStockScan/src/engine/monitoring/samsung_machine_entry_tuning.py), [samsung_entry_policy.py](/home/ubuntu/KORStockScan/src/trading/order/samsung_entry_policy.py)
  - 완료 판정(2026-09-05): F1~F8을 식별하고 사용자 구현 지시에 따라 actual-policy/as-of → 기존 timing owner 상승·반등 → 불필요 veto/표본 분리 → 경제성 분모 순으로 범위를 확정했다. 신호 subset의 신규 tightening 권한은 제거하고 진단으로 유지한다.
  - 이 항목은 완료된 범위 판정 기록이며 구현·검증은 `SamsungEntryRiseReboundImplementation0907`, 자연 생산/실적용 확인은 `SamsungEntryRiseReboundNaturalEvidence0907`이 소유한다.

- [x] `[SamsungEntryRiseReboundImplementation0907] Samsung 실제 적용 근거·상승반등 timing 통합 구현 및 재리뷰` (`Due: 2026-09-07`, `Slot: PREOPEN`, `TimeWindow: 07:00~07:20`, `Track: ScalpingLogic`)
  - Source: [Samsung 최종 리뷰 §7](../audit-reports/2026-09-05-samsung-machine-entry-final-review.md), [report-based-automation-traceability.md](../report-based-automation-traceability.md)
  - 구현: v9 실제 applied/source cutoff/청산 원장, 기계별 연속 적용 cohort, broker 체결금액 EV/완료율 ETA, subset 신규승격 제거와 기존 timing owner의 Samsung 상승·반등 recipe를 연결했다. Morning PLANNED SOR fallback도 선택 정책을 제출 전에 검사한다. 최근 5거래일 신호 허용은 Samsung scope에만 적용하며 양의 paired EV·순이익 개선·표본/coverage·one-scope guard는 유지한다.
  - 검증 완료(2026-09-05): 반례·producer/consumer·runtime·preflight·postclose/PREOPEN 영향 테스트 962 passed, 변경 Python Ruff/Black/compile, diff whitespace와 checklist parser PASS. 구현→리뷰→수정→재리뷰 후 구현 범위 미해결 finding 0건이다. 8월 27일/9월 4일 보관 자료의 읽기 전용 재계산은 원장/후보 계약 PASS, mutation 0건이다. 실제 개선 후보 확보·실적용·수익 증명은 별도 OPEN owner가 확인한다.
  - 권한 경계: 코드/문서와 로컬 읽기 전용 검증이며 정책 적용·봇 재기동·주문·취소·env/lock·수량/target/holding/provider/broker/hard safety는 변경하지 않는다.

- [ ] `[SamsungEntryRiseReboundNaturalEvidence0907] Samsung 상승반등 원천·후보·PREOPEN 실제 소비 확인` (`Due: 2026-09-07`, `Slot: POSTCLOSE`, `TimeWindow: 22:10~22:25`, `Track: ScalpingLogic`)
  - Source: [Samsung 최종 리뷰 §7](../audit-reports/2026-09-05-samsung-machine-entry-final-review.md), [machine_entry_timing_tuning.py](/home/ubuntu/KORStockScan/src/engine/automation/machine_entry_timing_tuning.py)
  - 현재 근거: 9월 4일 timing actual anchor 6건은 전부 source 결손이고 Samsung 동적 paired 완료 0건이다. 과거 결손을 재실행으로 합성하지 않는다. exact-route 자연 수집은 OPEN `MachineExactRouteReceiptRuntimeAcceptance0907`과 대사한다.
  - 판정: source gap은 구체적 원천 repair/quarantine, 무신호·미체결은 자연 관측, 충분한 표본인데 경제성 미충족은 현 가설 미지지로 구분한다. 표본 증가만으로 양의 EV/승격을 보장하지 않는다. 현재 EV가 음수라는 이유만으로 양수 개선 후보를 거절하지 않는다.
  - 완료 조건: 8 unique lifecycle/8 paired 완료·5 관찰일·최근 5 source-day 양의 EV/순이익 개선·coverage/same-stage/price guard를 통과한 scope만 다음 거래일 정책에 선택한다. 코드/후보 생성과 실제 적용을 구분하고 exact-date policy hash, runtime signal/provenance의 recipe·WAIT/ENTER/REJECT, 후속 실체결 성과를 대사한다. 후보 없음은 baseline 유지이지 반등-only 실매수 전환 완료가 아니다.
  - 권한 경계: 기존 승인 자동화 범위의 자연 실행 확인이다. 표본 확보를 위한 실주문, 정책 강제 적용, bot 재기동, guard 해제·baseline 제거를 허용하지 않는다.

- [x] `[AvgDownExistingAxisReplayImplementation0907] AVG_DOWN 기존축 경제성·중복 경로 개선계획의 A~C 구현·리뷰 종결` (`Due: 2026-09-07`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:35`, `Track: ScalpingLogic`)
  - Source: [AVG_DOWN 기존축 구현계획](../proposals/avg-down-existing-axis-economic-replay-plan-2026-09-05.md), [scalping_avg_down_recovery_calibration.py](/home/ubuntu/KORStockScan/src/engine/monitoring/scalping_avg_down_recovery_calibration.py), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py)
  - 완료 상태(2026-09-05): A(P0/P1) exact-route/source contract와 단일축 allowlist, B(P2/P3a) 기존 행동 보존 route replay와 비용 차감 fixed-exit source-only 계산, C(P3b 가능성 판정/P4/P5) 경제성·feasibility·AI/PREOPEN/PID identity를 구현했다. 신규 전략축·cron·수량/횟수/익절·주문 권한은 추가하지 않았다.
  - 구현 방향: 기존 `scalping_avg_down_recovery_quality_gate` 유지, 초기 보정 대상은 기존 `SHALLOW_VOLATILITY_AVG_DOWN_MIN_BUY_PRESSURE` 한 키다. exact decision/receipt/terminal·비용·authority를 연결하고 기존 경로의 행동을 보존한 뒤 A=current/B=단일값 후보/C=NO_ADD 순기여를 비교한다. Deep·late-loss는 별도 하위 경로 진단이고 shallow 승격의 동시 통과 조건이 아니다.
  - 완료 조건: 1초 mark·중복·미체결의 완료 표본 승격과 sim funnel의 runtime EV 표본 사용을 차단한다. 금지키/다중값 ENV, AI evidence ID/hash/date 불일치도 차단한다. 같은 최종 행동이면 `no_effect_after_route_arbitration`, 고정 종료 분석만 가능하면 source-only, 유효 개선이 없으면 `hold_no_edge`로 구별한다. 단계별 review/fix/re-review와 해당 검증을 수행하고 P0~P5의 완료/미완료·repair·acceptance를 보고한다.
  - 종결 판정: old schema, sim/submit proxy, 중복·상충 decision/terminal, 비성숙 결과, 다중/금지 env, stale AI identity, KRX/NXT scope 결손은 fail-closed다. 작은 순기여에는 별도 +1%·target-hit·MFE/MAE 허들을 적용하지 않는다. 정상 hold/보고서 일시 누락은 마지막 승인값만 명시적 carry-forward하고 source-quality hard block·safety·runtime current 충돌은 유지하지 않는다.
  - 1차 구현 당시 자동화 상태: 기존 postclose wrapper → direct v2 report → same-date AI → PREOPEN one-axis selection → 비전략 candidate provenance env → PID route event가 연결됐다. 당시 원천은 `fixed_observed_exit_source_only`이고 생산 v2 paired exit 표본은 없었으므로 실제 threshold 선택·env 적용·수익 개선을 완료로 보고하지 않았다.
  - 1차 리뷰 근거: AVG_DOWN producer/경제성/helper/holding observer/source audit/daily AI/PREOPEN/verifier와 공통 PYRAMID 경로를 review→fix→re-review했다. Source-only target identity 검증 누락과 paired 라벨만으로 공통 관측 매도가를 재사용할 수 있던 권한 결함을 재리뷰에서 보완했다. A/B/C별 완료 상태·종료가격·exit-policy·terminal source ID와 exact decision ID가 모두 필요하고 fixed/paired 누적 분모를 분리했다. 당시 영향 회귀 2,148건과 checklist parser 테스트 53건, Ruff, Black, 변경 모듈 compile, wrapper `bash -n`, 실제 checklist parse, `git diff --check`를 통과했다.
  - 재점검 이력(2026-09-05): 위 1차 완료 뒤 producer→consumer/달성 가능성 리뷰에서 paired 생산 경로 단절, terminal episode 오결합, mixed 진단 EV veto, real sizing/coverage 오분류 등을 확인해 `AvgDownFinalReviewRepair0907`을 열었다. 해당 보완은 아래 완료 항목으로 종결됐으며, 기존 완료 기록과 보완 종결 어느 쪽도 자연 실적용·수익개선 완료를 뜻하지 않는다.
  - 권한 경계: 이 계획은 실주문·취소, bot 재기동, live env 선택, provider, quantity/cap/추가 횟수/cooldown, quote freshness, broker/hard safety 또는 새 +0.30% 익절을 승인하지 않는다. 기존 경로 우선순위 변경·폐기와 live bounded 범위 확정은 영향/근거와 적용 계약을 별도로 검토한다.

- [x] `[AvgDownFinalReviewRepair0907] AVG_DOWN 최종 리뷰의 근거 오결합·판정 오류·생산 가능성 보완` (`Due: 2026-09-07`, `Slot: PREOPEN`, `TimeWindow: 06:40~07:20`, `Track: ScalpingLogic`)
  - Source: [AVG_DOWN 재점검·종결 기록 §0.1~§0.3](../proposals/avg-down-existing-axis-economic-replay-plan-2026-09-05.md), [scalping_avg_down_recovery_calibration.py](/home/ubuntu/KORStockScan/src/engine/monitoring/scalping_avg_down_recovery_calibration.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py)
  - 종결 판정(2026-09-05): R2/R3/R5/R7 판정 수정, R4 동일 decision sizing·coverage 분리, R6 unique ADD/NO_ADD 귀속, 고정 비용률·append 재시도에 더해 production cadence frame capture와 frozen full-policy snapshot, 격리된 기존 holding/exit policy adapter를 연결했다. 현재 상세 판정은 구현계획 §0.3이 소유한다.
  - 확대 범위: 사용자 선택은 독립 청산 재현 엔진 구현이다. `lifecycle/avg_down_replay.py`가 독립 수량/평단/다중 leg·pending/cancel·정책 상태·종료·당시 비용·exact-state input digest를 처리한다. 합성 full-policy 평가와 기록 소비 테스트는 실제 정책 자동 평가의 대체 증거가 아니다. quote 가정 outcome은 개별 행까지 source-only이며 live 승인 표본으로 재분류하지 않는다.
  - 구현 acceptance: 최초 원관측의 holding/exit/외부 ADM·LDM policy snapshot, 연속 fresh/conflict-free frame, A/B/C별 기존 full policy 실행, exact-state input digest와 action/sizing/virtual receipt 계보를 연결했다. 미기록 외부 I/O·AI·partial fill은 임의 HOLD/full fill로 채우지 않고 explicit replay gap으로 차단한다.
  - 검증(2026-09-05 최종 갱신): AVG_DOWN replay/policy replay/calibration, scale-in, holding/exit, source quality, daily/AI/PREOPEN, verifier, PYRAMID, pipeline logger, wrapper, observer와 checklist parser 통합 테스트 **2,503 passed**, 기존 외부 pandas-ta 경고 1건. 변경 모듈 Ruff·compile, wrapper `bash -n`, `git diff --check`와 실제 checklist parse도 통과했다. 기동 모듈의 기존 Ruff 93건은 HEAD와 동일하며 신규 finding 0건이다. 구현 범위 내 review→fix→re-review gate를 종결했으며 자연 runtime 표본, 실적용 또는 수익개선 승인은 아니다.
  - 판정 보완 결과: R2 terminal decision/episode/정책/venue/시간 lineage 오결합을 차단했다. R3 authoritative paired 결과를 mixed fixed-exit 진단이 자동 veto하는 분기와 feasibility 모순을 수정하고, R4 real sizing/downstream 미확인은 `hold_no_change`가 아니라 coverage 결손으로 분리했다.
  - 생산 경로 결과: R1 원관측의 fixed/source-only 성격을 유지하면서 독립 A/B/C replay 결과를 결속했다. 재현 가능한 exit 경로만 생산하고 observer→replay→source audit→report→AI/PREOPEN 통합 fixture를 검증했다. 기존 account/price/sizing snapshot을 재사용하며 추가 runtime API/주문이나 고정 수량 가정으로 누락을 채우지 않는다.
  - 조건 보완 결과: 당일 loaded config/PID가 검증되면 same-day route 없이 동일 정책 누적 근거를 유지하며 ADD 제거 tightening에는 유효 B-C=0/B-A>0 및 KRW 개선을 허용했다. R6 후보별 ADD/NO_ADD 행동 변화, unique episode·fill·terminal 귀속을 분리했다. 10건 floor/venue scope/source authority/hard safety는 낮추지 않았다.
  - 완료 판정: 오결합은 report/PREOPEN에서 fail-closed, valid paired positive+fixed negative는 일관된 authoritative 판정, 수량/미평가 결손은 명시적 coverage 상태, 비용 차감 작은 양수와 정상 NO_ADD는 결정된 경제성 계약과 일치함을 production-capable fixture와 targeted validation으로 확인했다. 재현 불가능한 exit 범위는 source-only gap으로 남긴다. 미래 표본 확보/수익 발생/실적용은 OPEN 자연증거 항목에서 별도로 판정한다.
  - 권한 경계: 코드 결함 보완은 종결했지만 live 적용 승인은 아니다. 봇 재기동·운영 보고서 재생성·env 선택을 수행하지 않았고 새 튜닝축·수량/횟수/cap·provider·broker/hard safety를 변경하지 않았다.
  - 후속 보완: 문자열 production field roundtrip, 저장 판정의 full-policy 우회 차단, arm별 AI/LDM 상태, source/decision 결속, 완료 이후 gap의 과잉 무효화, BBO 가격/수량 정합성, 취소→같은 평가의 청산 순서, 체결 후 virtual DB 평단/수량 동기화, nested verifier, frame/압축/AI 시간·횟수 한도, 동일 원천·정책·digest 과거 결과/응답 재사용을 검증했다. 큰 snapshot의 text 중복도 제거했다. 재현 불가능한 부분체결·split/market 주문·미기록 account 입력은 source-only gap으로 명시한다.

- [ ] `[AvgDownPairedExitRuntimeEvidence0907] AVG_DOWN v2 자연 원천·paired exit·PREOPEN/PID 적용 가능성 확인` (`Due: 2026-09-07`, `Slot: POSTCLOSE`, `TimeWindow: 21:55~22:10`, `Track: ScalpingLogic`)
  - Source: [AVG_DOWN 기존축 구현계획](../proposals/avg-down-existing-axis-economic-replay-plan-2026-09-05.md), [scalping_avg_down_recovery_calibration.py](/home/ubuntu/KORStockScan/src/engine/monitoring/scalping_avg_down_recovery_calibration.py), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py)
  - 선행 owner: 완료된 `AvgDownFinalReviewRepair0907`이 production frame, 기존 정책 adapter, source audit와 consumer 연결을 소유한다. 이 OPEN 항목은 다음 자연 거래일의 frame/paired 결과·입력 결손·권한 경계를 먼저 판정하고, 별도 승인된 runtime-authoritative 근거가 있을 때만 AI/PREOPEN/PID·post-apply까지 대사한다.
  - 권한 acceptance: quote 가정 독립 결과는 완료되어도 source-only이며 자연 표본 증가만으로 runtime-authoritative terminal이나 PREOPEN 적용 권한이 되지 않는다. 운영자가 실권한 전환을 요청하면 별도 승인 범위와 검증 계약을 먼저 확정한다. 고정 종료/quote 결과의 라벨 변경으로 이 경계를 닫지 않는다.
  - 현재 상태: 기존 생산 보고서는 v1 proxy이고 신규 자연 `avg_down_route_arbitration_v2` 및 독립 A/B/C exit replay의 생산→승격 완결성을 확인하지 못했다. fixed observed exit가 양수이거나 단순 paired 라벨이 있어도 유효한 A/B/C terminal·원천 권한이 없으면 source-only다. 전체 PREOPEN env verify의 pass를 이 family의 선택/PID 소비 증거로 쓰지 않는다.
  - 판정 기준: 선행 보완에서 확정한 versioned 계약으로 source-quality preflight, 검증된 runtime current provenance, unique complete parent episode 10건, 같은 AVG_DOWN/sizing/cost policy cohort, 실제 영향 venue scope와 비용 차감 증분 경제성을 확인한다. same-day route의 대체 loaded config 계약과 ADD 제거 tightening의 B-C=0 예외는 구현계획 §0.2의 수정·검증 범위를 따른다. AI/PREOPEN candidate ID·digest·key·value·date와 후보별 PID/행동/실체결/unique terminal 귀속을 별도 대사한다.
  - 완료 조건: paired exit replay 자료가 없으면 무리하게 승인하지 않고 exit-state/terminal 입력 결손을 구체적인 code-improvement acceptance로 남긴다. 조건이 닫혀도 기존 same-stage 단일 누적 갱신 선별을 통과한 exact-date PREOPEN env와 다음 PID 관측 전에는 실적용으로 판정하지 않는다.
  - 금지: 표본 확보를 위한 실주문 강행, 구형 45건 proxy 재사용, KRX/NXT 근거 혼합, threshold 외 전략축·quantity/cap·provider·bot·broker/hard-safety 변경.

- [x] `[PyramidExistingAxisReplayPlan0907] 기존 PYRAMID 단일축 경제성 재현 개선계획의 구현 범위·진행 판정` (`Due: 2026-09-07`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:15`, `Track: ScalpingLogic`)
  - Source: [PYRAMID 기존축 개선계획](../proposals/pyramid-existing-axis-economic-replay-plan-2026-09-05.md), [scalping_pyramid_intraday_feedback.py](/home/ubuntu/KORStockScan/src/engine/monitoring/scalping_pyramid_intraday_feedback.py), [scalping_pyramid_quality_calibration.py](/home/ubuntu/KORStockScan/src/engine/monitoring/scalping_pyramid_quality_calibration.py)
  - 완료 상태(2026-09-05): P0→P4 코드·계약 구현과 review/fix loop를 종결했다. Feedback schema v5가 same-event gate/BBO/existing resolver/latest terminal sell/coverage를 보존하고, calibration은 same-complete-episode fixed-exit replay와 비용 1회 차감 `source_quality_adjusted_ev_pct`로 기존 min-profit 한 축만 판정한다. Consumer는 event schema, passive resolver price/BBO, 평가 venue/session을 독립 재검증하고 candidate evidence ID/version/hash는 same-date AI와 PREOPEN에서 다시 검증한다.
  - 첫 구현 범위: configured/effective threshold·원가/비용·event/venue/policy/종료 연결·coverage 대사, 현재값 gate 재현, 동일 기회의 현재/후보/추가매수 없음 paired 경제성 비교. 실제 호가·downstream 판단이 없는 행은 source gap으로 분리하고 관측 종료가격 고정 분석을 실제 체결/인과 효과로 승격하지 않는다.
  - 완료 조건: 기존 `scalping_pyramid_quality_gate`와 `SCALPING_PYRAMID_MIN_PROFIT_PCT`만 추천 대상으로 유지한다. base/strong/prior/bridge 의미, 비용 1회 차감, missing/partial fill 분리, 한 단계 양의 순기여·현재 대비 개선, KRX 근거 없는 NXT-only 공통축 적용 차단, AI candidate ID/version/hash/date·PREOPEN 단일축 전달을 테스트한다. 단계별 리뷰·재리뷰와 영향 테스트를 통과하고 계획의 P0~P4 완료 또는 명시적 결손/권한 경계를 기록한다.
  - 종결 근거: 2026-09-04 raw의 비생산 임시 재생성은 observed gate 2건, exact-ready 0건이며 두 건 모두 scout bridge owner 충돌과 구형 BBO/resolver 결손으로 `source_quality_blocked:threshold_replay_no_comparable_episodes`였다. 과거자료를 mark/threshold 가상 가격으로 복원하지 않았다. 자연 장후 AI/PREOPEN 소비 확인은 별도 OPEN `PyramidEconomicFeasibilityHandoff0907`이 소유한다.
  - 검증 근거: feedback/calibration/daily-AI/PREOPEN 430건과 holding/scale-in 1,023건(합계 1,453건), Ruff, Black, 변경 모듈 compile, checklist parser 35건, `git diff --check` 통과. 검토 범위 내 미해결 결함 0건.
  - 권한 경계: 새 튜닝축/익절/보유시간 정책, quantity/cap, provider, bot 재기동, 실주문·취소, broker/hard safety 변경과 수동 env 적용은 포함하지 않는다. 자연 표본 확보를 위해 이 경계를 우회하지 않는다.

- [ ] `[PyramidEconomicFeasibilityHandoff0907] PYRAMID 경제성·조건 달성 판정의 장후 AI 소비 확인` (`Due: 2026-09-07`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: ScalpingLogic`)
  - Source: [scalping_pyramid_quality_calibration.py](/home/ubuntu/KORStockScan/src/engine/monitoring/scalping_pyramid_quality_calibration.py), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - 구현 완료(2026-09-05): 라벨 비율만으로 여러 quality env를 변경하는 경로와 다른 진입 anchor의 전체 Normal-winner EV veto를 제거했다. 임계값 자체의 비용 차감 순기여 양수·현재 대비 개선·다음 단계 eligible floor·0.1%p 제한을 적용하고, 같은 날짜 direct PYRAMID 후보와 `condition_feasibility`를 장후 AI review 목록에 연결했다. static fallback은 현재 런타임 관측으로 인정하지 않는다.
  - 판정 기준: 당일 `supplemental_calibration_sources.scalping_pyramid_quality_calibration.merged_candidate_count=1`, AI 입력/parsed review의 family census 포함, direct 후보와 current/recommended/feasibility 일치를 확인한다. `no_economic_candidate`는 현재 threshold-only 가설 기각, `positive_candidate_unreachable_in_one_step`는 source-only 경로 재설계 검토로 닫으며 무기한 `hold_sample`로 오분류하지 않는다.
  - 완료 조건: 임계값 후보가 양의 비용 차감 순기여와 현재 대비 개선을 모두 만족하고 공통축에 KRX parent 근거가 있을 때만 한 축을 추천한다. NXT-only는 `hold_runtime_scope`, AI reject/missing과 source-quality/owner conflict가 있는 후보는 PREOPEN env를 생성하지 않는다. 현재 가설 기각 시 조건 삭제나 실주문 강행 없이 새 유효 종료 표본 또는 별도 source-only 가설로만 재검토한다.
  - 다음 액션: `economic_hypothesis_rejected`, `bounded_path_redesign_required`, `candidate_reviewed_preopen_pending`, `handoff_missing_requires_fix` 중 하나로 종결한다. 자연 장후 AI 재검토 전 기존 2026-09-04 review artifact에는 새 PYRAMID 검토가 없으므로 자동 적용 완료로 보고하지 않는다.
  - 권한 경계: 이 확인은 보고서/AI 입력/후보 계약 전용이며 bot 재기동, 실주문·취소, quantity/cap, provider 또는 broker/hard safety 변경을 허용하지 않는다.

- [ ] `[MachineExactRouteReceiptRuntimeAcceptance0907] machine active-owner exact-route receipt와 decision source ID 자연 반영 확인` (`Due: 2026-09-07`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:45`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py), [kiwoom_websocket.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py), [scalp_micro_reversion_registration_receipt_2026-09-07.json](/home/ubuntu/KORStockScan/data/runtime/scalp_micro_reversion_registration_receipt/scalp_micro_reversion_registration_receipt_2026-09-07.json), [machine_microstructure_attribution_2026-09-07.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_attribution/machine_microstructure_attribution_2026-09-07.json)
  - 현재 코드 판정: manifest·authority·item census·target-date causal timestamp가 모두 유효한 뒤에만 exact route 격리를 허용한다. 특정 0B/0D route 미수신은 해당 symbol×route anchor만 제외하고 unrelated route의 rolling EV 입력은 유지한다. 복구 불가능한 과거 receipt-only 결손은 `terminal_source_date_quarantine`로 종결하지만 signal timestamp, source event ID 또는 owner lifecycle 계약 결함이 동반되면 `requires_structural_repair`와 `requires_code_fix`를 유지한다.
  - 완료 조건: 정상 process lifecycle 뒤 당일 receipt의 requested/item census가 manifest와 일치하고 설정·최초·마지막 수신시각이 생성시각 이전의 exact target date에서 인과순서를 지키며, 모든 active-owner exact route에 0B·0D 최초 수신시각·양의 수신 횟수·transport epoch·nonnegative 최대 inter-arrival gap이 있다. actual decision leg는 `source_entry_event_id`와 `signal_decision_at`을 보존한다.
  - 다음 액션: 전체 완결이면 rolling source 입력 허용, 일부 route만 미수신이면 해당 route 격리와 정상 route 유지, 전역 계약 결함이면 fail-closed, 거래일 종료 뒤 receipt-only 결손이면 사후 합성·반복 재실행 없이 exact source date quarantine으로 닫는다. 자연 신호 0건은 실패가 아니며 receipt/consumer 계약을 기준으로 판정한다.
  - 권한 경계: source-quality/runtime reflection 확인 전용이다. 이 acceptance를 위해 bot/service를 재기동하거나 실주문·취소, threshold, provider, quantity/cap, 가격·target·holding/exit, broker/hard safety를 변경하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-09-04` postclose -> `2026-09-07`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (07:45~09:00)

- [x] `[MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0907] micro observer 저장공간·연속수집 source gap 복구 확인` (`Due: 2026-09-07`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:45`, `Track: RuntimeStability`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-04.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-04.json)
  - 판정 기준: workorder `main-ai-gap-eaaf062c7486bc1ac7fbfcf8`의 owner=`MicroReversionForwardCollectorContinuity`, reason_codes=`row_exclusion_required, past_market_row_missing=0`를 source-only producer 보완으로 닫는다. 장전 free bytes가 writer low-disk watermark를 충분히 상회하는지 확인하고, 부족하면 실주문과 무관한 closed-date verified compression만 실행한 뒤 observer canary를 재검증한다.
  - 완료 조건: exact-date canary remains pass or row-exclusion-only through close; later clean windows continue collecting; provider replay remains held until queue-loss scope has an exact exclusion receipt or the next clean date
  - 장전 종결(2026-09-05): 마지막 exact-date(2026-09-04) canary는 `stopped_clean`, `stop_required=false`, queue full/drop·writer/depth-writer error·low-disk breach가 모두 0이고, exchange timestamp regression 5행만 `raw_row_exclusion_required`로 격리됐다. 현재 free bytes는 `14,204,506,112`(13.229 GiB)로 5 GiB low watermark보다 8.229 GiB 높아 closed-date compression은 실행하지 않았다. 다음 clean-date 자연 수집은 이 장전 용량/계약 점검을 다시 여는 조건이 아니라 장중 source-quality 관찰 항목에서 확인한다.
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [x] `[ThresholdEnvAutoApplyPreopen0907] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-09-07`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-04.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 종결 판정(2026-09-05): `applied_guard_passed_env`. 표준 wrapper를 source date `2026-09-04`, target date `2026-09-07`, `auto_bounded_live`/AI-required로 실행해 apply plan과 runtime env/env manifest/verify를 생성했다. 독립 handoff 재검증은 `status=pass`, runtime-policy fail 0, dated-override fail 0, unverified selected family 0이며 333개 env override와 25개 selected family가 manifest에 결속됐다. 미래 target-date 사전 실행이라 machine-approval/Main-AI 보조 PREOPEN producer는 exact-current-date guard에서 정상 차단됐고, 월요일 07:35 등록 cron이 당일 동일 wrapper를 재실행한다. 차단 family를 수동 승격하거나 봇을 재기동하지 않았다.

- [x] `[LowPriceEconomicRuntimeContractRepair0907] 저가 2-leg 비용·근거·자동화 계약 보완` (`Due: 2026-09-07`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: ScalpingLogic`)
  - Source: [low-price two-leg machines](../low-price-two-leg-machines.md), [policy_runtime.py](/home/ubuntu/KORStockScan/src/trading/low_price_two_leg/policy_runtime.py), [low_price_two_leg_tuning.py](/home/ubuntu/KORStockScan/src/engine/monitoring/low_price_two_leg_tuning.py), [low_price_two_leg_expanded_candidate_research.py](/home/ubuntu/KORStockScan/src/engine/monitoring/low_price_two_leg_expanded_candidate_research.py)
  - 판정 기준: minute-bar 연구와 실제결과 튜닝이 공통 round-trip cost `0.23%`를 사용하고, report/candidate/source-quality hash가 결속되며, 후보 선택이 비용차감 일평균 순이익을 우선하고 EV·빈도를 보조지표로 유지해야 한다. 기존 13개 승인은 현 비용으로 calibration half/holdout/full을 재평가하고 비양수 profile만 명시 격리한다.
  - 종결 판정(2026-09-05): 공통 비용계약과 source/report binding, source-valid 관측일 분모, content-bound `ka10080` checkpoint, bounded defer/resume, 중앙 verifier의 `2026-09-04 -> 2026-09-07` handoff를 구현했다. 재비용화 결과 `cj_cgv_morning`, `youngone_midday`, `sk_telecom_midday` 3개만 격리되고 나머지 승인 10개는 통과한다. 격리 profile preflight는 exit 4로 즉시 종결하며 broker gateway를 만들지 않는다.
  - 재점검 정정(2026-09-05): 위 완료는 1차 구현 기록이다. [최종 재점검 LP-F1~F5](../audit-reports/2026-09-05-low-price-two-leg-final-review.md)에서 확인한 추가 결함은 아래 완료 기록 `LowPriceFinalReviewRepairDecision0907`에서 보완했다. 자연 산출물/실적용/수익 확인은 별도 OPEN owner가 소유한다.
  - 권한 경계: 기존 drawdown/near-low 축만 평가하며 quantity, target, validity, stop/forced exit, provider/bot/cap, broker/account/order/cooldown 또는 hard-safety를 변경하지 않는다.

- [x] `[LowPriceFinalReviewRepairDecision0907] 저가 2-leg 최종 결함 보완·경제성 조건 재설계 구현 종결` (`Due: 2026-09-07`, `Slot: PREOPEN`, `TimeWindow: 08:30~08:45`, `Track: ScalpingLogic`)
  - Source: [저가 2-leg 최종 재점검 LP-F1~F5](../audit-reports/2026-09-05-low-price-two-leg-final-review.md), [low_price_two_leg_tuning.py](/home/ubuntu/KORStockScan/src/engine/monitoring/low_price_two_leg_tuning.py), [policy_runtime.py](/home/ubuntu/KORStockScan/src/trading/low_price_two_leg/policy_runtime.py)
  - 종결 판정(2026-09-05): v7 report/v3 candidate가 실제 적용 정책·artifact/report/SQ hash를 결속하며 신규 subset mutation·숨긴 정책 변경·schema downgrade를 거절한다. v3 research/v6 expanded가 기존 두 필터의 독립 최초 신호와 동일기간 비용차감 순이익/양수 EV를 비교한다. HELD는 다음 날짜와 holdout까지 유지하며 외부 해소 근거 없이 진입·청산을 만들지 않는다.
  - 조건 보완: 부분집합 5일/8 broker-priced legs/+0.005%p는 진단으로만 유지하고 단독 신규 live 승격은 제거했다. 신규 연구의 half 양수/half별 3-leg floor는 진단화했으며 전체 calibration/holdout floor와 양수 경제성·carry guard는 유지한다. CJ CGV/영원무역은 half 재검토·새 승인 필요, SK텔레콤은 전체/holdout 경제성 실패로 분리한다.
  - 검증: 저가주·연구·expanded·wrapper·중앙 verifier·microstructure·entry-timing·parser 통합 **692 passed**. Ruff·compile·shell syntax·diff whitespace 통과. 임시 CLI→candidate→PREOPEN, 허위 mutation/미적용 prior/나중에 생긴 source 정책, EV 상승·순이익 감소, 날짜 경계 HELD, half 경고, 비교 contract 변조 및 lookback 캐시 provenance 반례를 추가했다. review→fix→re-review의 구현 범위 내 미해결 finding은 없다.
  - 권한 경계: 실제 9/7 policy는 읽기 전용 대사만 했으며 기존 hash, 50 loader-ready/3 격리, mutation 0을 유지한다. 새 정책의 자동 live 승격/수익개선을 입증한 것이 아니다. 새로운 실권한은 별도 실체결·승인 계약을 필요로 하며 봇/주문/격리/운영 artifact는 변경하지 않았다.

- [ ] `[EpisodeRecommendationRuntimeAcceptance0907] Episode 53-profile 정책 inventory·50-profile runtime 자연 적용 확인` (`Due: 2026-09-07`, `Slot: PREOPEN`, `TimeWindow: 08:50~14:45`, `Track: ScalpingLogic`)
  - Source: [low_price_two_leg_expanded_profile_evidence_2026-09-04.json](/home/ubuntu/KORStockScan/data/config/low_price_two_leg_expanded_profile_evidence_2026-09-04.json), [low_price_two_leg_policy_2026-09-07.json](/home/ubuntu/KORStockScan/data/threshold_cycle/low_price_two_leg/applied/low_price_two_leg_policy_2026-09-07.json), [profiles.py](/home/ubuntu/KORStockScan/src/trading/low_price_two_leg/profiles.py)
  - 판정 기준: applied policy가 exact target date, 53개 full inventory, frozen evidence/source hash, `profile_revision_transition` 13건(로직 8·시간확장 5), 공통 비용계약, 3개 runtime exclusion, policy hash를 통과하고 신규 timer 10개가 enabled 상태인지 확인한다. 격리되지 않은 50개 중 각 신규 profile authority가 main bot/shared token/manual owner/evidence/applied hash를 모두 통과한 경우에만 자연 기동한다.
  - 다음 액션: 신규 신호의 `runtime_policy_hash`와 profile ID를 관찰하고 기존 held/open-order state가 신호일 snapshot을 유지하는지 확인한다. 자연 신호 0건은 실패가 아니며 policy/timer/authority 결손만 fail로 닫는다.
  - 장전 준비(2026-09-05 보완): exact-date applied policy를 표준 적용기로 원자 갱신했고 `validate_applied=(true, valid)`, inventory 53/53, loader ready 50/53, current-cost 격리 3/53, revision 13건(로직 8·신규 시간대 5), policy/evidence hash 일치다. 격리 profile의 실제 read-only preflight는 terminal exit 4로 broker gateway 전에 차단됐다. 신규 profile 5개의 preflight/live timer 10개 설치 상태는 유지한다. 실제 main-bot/shared-token/manual-owner authority와 50개 active profile의 자연 `runtime_policy_hash` receipt는 거래일 장중에만 관찰할 수 있으므로 본 항목은 OPEN을 유지한다.
  - 권한 경계: acceptance 과정에서 주문 취소·재제출, 기존 보유 retarget/resize, provider/bot/cap, stop/forced exit, broker/hard-safety 변경을 하지 않는다.

- [x] `[RisingMissedScoutRuntimePreopen0907] rising_missed_scout_workorder 후속 구현 및 귀속 확인` (`Due: 2026-09-07`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-09-04.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-09-04.json), [code_improvement_workorder_2026-09-04.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-04.json), [threshold_apply_2026-09-07.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-09-07.json), [threshold_runtime_env_2026-09-07.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-07.json), [threshold_runtime_env_verify_2026-09-07.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-07.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder`의 `join_ready`, `contrast_ready`, `economic_inference_ready`와 code-improvement order별 `implementation_status`를 확인한다. source-only order는 runtime family/env 반영 대상이 아니며 `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`가 모두 명시된 경우 `source_only_no_runtime_authority`로 종결한다. entry-turn은 당일 pre-anchor path receipt가 있으면 source-quality floor 미달과 별개로 runtime 계측 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder` 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `source_only_no_runtime_authority`, `runtime_instrumentation_reflected_source_quality_pending`, `runtime_receipt_not_observed`, `report_missing_or_stale`, `source_only_contract_failed` 중 하나로 order별 종결한다. source-only family에 PREOPEN env가 없다는 이유만으로 실패 처리하지 않는다.
  - 종결 판정(2026-09-05): entry-turn BBO order는 `runtime_instrumentation_reflected_source_quality_pending`으로 닫는다(`pre_anchor_bbo_path_event_count=2690`, exact join 2.866242%, pre-anchor 2.229299%, paired 0%로 경제성 승격은 계속 차단). classifier-prior feedback order는 `source_only_no_runtime_authority`로 닫는다(prior 92건, `implementation_status=implemented`). 두 order 모두 `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`이며 해당 source-only family는 2026-09-07 selected env에 없다. 기존 별도 family인 `rising_missed_normal_buy_bridge`와 혼동해 권한을 승격하지 않았다.

## 장중 체크리스트 (09:05~15:20)

- [ ] `[RuntimeEnvIntradayObserve0907] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-09-07`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-04.json)
  - 전일 postclose candidate_selected_families=entry_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, post_probe_winner_recovery, scalping_pyramid_quality_gate, holding_decision_context_v1, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26이며 실제 기동 기대 목록으로 직접 사용하지 않는다.
  - 판정 기준: 당일 PREOPEN verify가 통과한 threshold_runtime_env의 selected_families와 selection_change_summary(신규 ON/정책 갱신/carry-forward·operator lock 유지/OFF·제외)를 기준으로 runtime event provenance를 확인한다.
  - 금지: 관찰 결과만으로 장중 runtime을 변경하지 않는다. 사용자 명시 override는 fresh/conflict-free source, 단일 blocker 인과, 기존 bounded_tunable 단일 축, rollback과 즉시 attribution 계약을 모두 충족해야 한다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0907] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-09-07`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-09-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-04.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0907] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-09-07`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-09-07.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-09-07.jsonl), [threshold_events_2026-09-07.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-09-07.jsonl), [observation_source_quality_audit_2026-09-07.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-07.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-09-07 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (16:25~22:35)

- [ ] `[LowPriceEconomicReplayNaturalEvidence0907] 저가 기존축 paired 연구의 자연 산출물·권한 경계 확인` (`Due: 2026-09-07`, `Slot: POSTCLOSE`, `TimeWindow: 22:25~22:35`, `Track: ScalpingLogic`)
  - Source: [저가 2-leg 보완 구현 판정](../audit-reports/2026-09-05-low-price-two-leg-final-review.md), [entry spot research](/home/ubuntu/KORStockScan/src/engine/monitoring/low_price_two_leg_entry_spot_research.py), [expanded recommendation](/home/ubuntu/KORStockScan/src/engine/monitoring/low_price_two_leg_expanded_candidate_research.py)
  - 다음 액션: 자연 postclose v7/v3 tuning 후보의 source-date 실제 applied hash와 carry 정책을 확인하고, expanded v6의 `existing_axis_economic_replay`, current/candidate 동일 날짜·비용·원시 episode, HELD/carry-in·blocked dates, 순이익/EV 판정을 대사한다. root 추천·consumer 검증에 빠진 handoff는 실패로 분리한다.
  - 완료 조건: source policy 미확인·외부 custody 해소 결손·표본 부족·무개선을 구체적으로 구분하고 각 실제 적용 프로필의 provenance/실현손익은 기존 `EpisodeRecommendationRuntimeAcceptance0907`과 대사한다. source-only 양수 결과나 보고서 0건을 임의 live 승인 또는 시스템 실패로 바꾸지 않는다.
  - 금지: 표본을 만들기 위한 실주문/격리 해제, 보유 가상 청산, stop/target/quantity/계좌·주문 guard 변경, source-only paired 결과의 실체결 근거 승격, 무승인 봇 재기동.

- [ ] `[ThresholdDailyEVReport0907] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-09-07`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [tuning_performance_control_tower_2026-09-04.json](/home/ubuntu/KORStockScan/data/report/tuning_performance_control_tower/tuning_performance_control_tower_2026-09-04.json), [threshold_cycle_ev_2026-09-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-04.json)
  - 판정 기준: tuning performance control tower를 먼저 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0907] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-09-07`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-09-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-04.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[MainAIQualitySourceGapRuntimeExecutionReceiptCustodyRepair0907] RuntimeExecutionReceiptCustodyRepair main lifecycle source gap 복구 확인` (`Due: 2026-09-07`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: ScalpingLogic`)
  - Source: [main_ai_quality_r0_r3_cycle_2026-09-04.json](/home/ubuntu/KORStockScan/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-04.json)
  - 판정 기준: workorder `main-ai-gap-54507dbbb4904a6bb30f8956`의 owner=`RuntimeExecutionReceiptCustodyRepair`, reason_codes=`pipeline_lifecycle_instrumentation_gap_count=1, real_submitted_lifecycle_count=3, broker_execution_unique_count=2`를 source-only producer 보완으로 닫는다. 공식 raw execution envelope의 order/execution identity를 합성 없이 검증하고 결손 lifecycle만 제외한 뒤 paired producer를 재검증한다.
  - 완료 조건: official raw execution envelope/order/execution identity is complete for each repair-required lifecycle or the affected row remains explicitly excluded; custody and order authority remain unchanged
  - 권한 경계: 이 항목은 source-quality/instrumentation 복구 전용이며 runtime env, 실주문·취소, threshold, provider/bot, quantity/cap, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[CodeImprovementWorkorderReview0907] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-09-07`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-09-04.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-09-04.md), [code_improvement_workorder_2026-09-04.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-04.json)
  - 판정 기준: selected_order_count=47와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0907] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-09-07`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-09-04.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-09-04.json), [runtime_apply_gap_audit_2026-09-04.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-09-04.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`233`, rollup_required_count=`233`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 232}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[MachineLifecycleTurnoverObjectiveFollowup0907] 위젯·episode 빠른 회전 목적의 미완료 후속 구현 확인` (`Due: 2026-09-07`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: ScalpingLogic`)
  - Source: [machine_microstructure_policy_approval_postclose_2026-09-04.json](/home/ubuntu/KORStockScan/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_2026-09-04.json), [machine_microstructure_attribution.py](/home/ubuntu/KORStockScan/src/engine/monitoring/machine_microstructure_attribution.py)
  - 판정 기준: 승인 후보 수와 무관하게 `followup_required=true`인 미완료 목적 항목 `machine_lifecycle_turnover_policy_research_v1`(status=`EVIDENCE_ACCUMULATING`, next_action=`repair_current_attribution_source_contract_and_rerun`)의 상태와 상태별 `next_action`을 확인하고 구현 또는 표본수집 경로로 닫는다.
  - 상태별 다음 액션: `IMPLEMENTATION_REQUIRED`는 source-only rolling paired policy 연구를 구현하고, `EVIDENCE_ACCUMULATING`은 exact-date floor 충족까지 수집·재검증한다. `CANDIDATE_QUEUE_HANDOFF|COMPLETE`는 closed 상태이므로 report에서 제외되고 다음 refresh에서 builder-owned 항목이 제거된다.
  - 권한 경계: 이 POSTCLOSE 후속 항목은 source-only 구현·검증 작업이며 runtime env, 실주문, target/timeout/cooldown/cap, threshold, provider/bot, hard safety 또는 broker guard 변경 권한이 없다.

- [ ] `[WidgetEpisodeSharedReadYieldGate0907] 위젯·episode 원격 이력 연구의 shared-rate 충돌 및 증분 재사용 보완` (`Due: 2026-09-07`, `Slot: POSTCLOSE`, `TimeWindow: 20:05~21:40`, `Track: RuntimeStability`)
  - Source: [run_widget_evaluation.sh](/home/ubuntu/KORStockScan/deploy/run_widget_evaluation.sh), [widget_symbol_signal_policy_research_2026-09-04.json](/home/ubuntu/KORStockScan/data/report/widget_symbol_signal_policy_research/widget_symbol_signal_policy_research_2026-09-04.json), [low_price_two_leg_expanded_candidate_research_2026-09-04.json](/home/ubuntu/KORStockScan/data/report/low_price_two_leg_expanded_candidate_research/low_price_two_leg_expanded_candidate_research_2026-09-04.json)
  - 판정 기준: EOD/main postclose의 shared REST read 점유 중 `ka10080_shared_read_rate_deferred`로 20:10 unit이 실패한 원인을 재현하고, exact source hash가 같은 clean-baseline 이력은 content-bound checkpoint/cache로 재사용하며 변경분만 호출하는지 확인한다. 위젯 research 약 15분과 episode expanded research 약 25분의 출력·consumer hash가 full replay와 같아야 하고, source가 달라지면 fail-safe full rebuild로 전환한다.
  - 완료 조건: 같은 target date에서 widget evaluation과 21:15 machine final refresh가 중복 원격 replay 없이 terminal success이고, 실패 시 bounded defer/resume가 기존 정상 artifact를 덮어쓰지 않으며 다음 PREOPEN policy/handoff가 exact source hash에 결속된다.
  - 부분 종결(2026-09-05): episode 저가 연구 측은 공식 `ka10080` request contract와 bar content hash에 결속된 symbol checkpoint, 동일 continuation page bounded retry, exit 75 wrapper resume(최대 3회), 기존 정상 report 비덮어쓰기를 구현·검증했다. 위젯 evaluation의 동일 계약과 실제 동시실행 terminal 증거가 남아 있으므로 항목 전체는 OPEN이다.
  - 권한 경계: source/report/runtime-cost 최적화 전용이다. 매매 process 재기동, 종목·profile·target·threshold·수량·cap·provider·broker/order·hard-safety 변경 권한이 없다.

- [ ] `[LegacyOneSharePostcloseYieldGate0907] legacy one-share opportunity 분석의 daily 핵심 경로 유지여부 판정` (`Due: 2026-09-07`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:50`, `Track: RuntimeStability`)
  - Source: [one_share_threshold_opportunity_2026-09-04.json](/home/ubuntu/KORStockScan/data/report/one_share_threshold_opportunity/one_share_threshold_opportunity_2026-09-04.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: forced record=`5523`, identity conflict=`3285`, post-sell joined=`0`, opportunity/workorder=`0`인 결과가 현재 신규 episode 2x10-share 계약에서 intended consumer를 갖는지 확인한다. current-owner event 또는 exact post-sell source가 없으면 daily core에서 제거하고 event-triggered 또는 manual/weekly diagnostic으로 전환한다.
  - 다음 액션: `keep_daily_valid_consumer`, `convert_to_event_triggered`, `convert_to_manual_or_weekly`, `retire_legacy_orphan` 중 하나로 닫는다.
  - 권한 경계: 장후 분석 주기·소비자 정합성 전용이다. legacy custody, 신규 수량, 주문·취소, runtime env, threshold/provider/bot/cap 또는 broker/hard safety를 변경하지 않는다.

- [ ] `[AutomationTriggerDecisionSummary0907] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-09-07`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-09-04.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-09-04.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`14`, run_count=`9`, skip_count=`0`, source_missing_count=`4`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, pattern_lab_currentness_audit, pattern_lab_ai_review`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:8, disabled_by_runtime_policy:5, source_missing_or_unreadable:4, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

- [ ] `[PostcloseSourceQualityGateReview0907] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-09-07`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-09-07.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-07.json), [threshold_cycle_ev_2026-09-07.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-07.json), [code_improvement_workorder_2026-09-07.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-07.json), [threshold_cycle_postclose_verification_2026-09-07.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-09-07.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
