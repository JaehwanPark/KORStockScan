# 프리마켓 기회 전달·제출 지연 우선 보완과 유형별 보조입력 연구계획

> **10/28 후속 공통 설계:** [기한·신호 유효성·처리 경로 재설계](main-regular-submit-deadline-fresh-recheck-and-discovery-latency-remediation-plan-2026-10-27.md#entry-validity-redesign-20261028)가 신규 기한 대안과 상시/비상시 구현 우선순위를 소유한다. 이 문서의 원5초·기존 기한 보존은 당시 구현과 현재 승인된 운영값의 기록이며, 후속 연구의 기한을 고정하지 않는다. 기존 배분·패턴·원천 안전 및 PRE/REGULAR의 분리 수용은 유지한다.

## 1. 결정·범위·기준

**최초 관찰·재관찰의 적격 대기와 PASS 이후 불필요한 처리시간을 먼저 줄인다. 보조판정은 적격 누적 PRE 모집단에서 입력 효과와 프롬프트 효과를 분리해 연구한다.** 같은 입력에서 정상 제출까지 도달하는지와 승리/실패를 얼마나 구별하는지를 각각 검증한다. 만료·가격·계좌/주문 안전 기준을 완화해 PASS나 제출 수를 늘리지 않는다.

최초08:54 요청은 상세계획 수립이었고 구현·호출·배포·기동은 없었다. 후속 사용자 승인으로 구현과 추가 연구를 실행한 결과는 §9에 기록한다. 배포·재기동·RFHIC startup hold 해제는 이 작업에서 실행하지 않는다. BUY 전달 수리와 별도 SELL 수리/중지 owner의 완료는 구분한다.

- 기준2026-10-28 08:45:37 KST: selected `29a3c14758f2f7935fc811b8b49719314bb0702c`, 원 Main2852722/start78626491, release `postclose-ready-20261028-29a3c1475`, bundle `4abcce1001c0cc689d7b749376ba91be6455f479e4332dc97a1d2fc2d39ca46f`. 원 PID는 종료됐고 `RFHIC_sell_timeout_repair_20261028`의 startup hold가 active다.
- [기준·18개 선택본/작업본 SHA·strict 원본 보존](../../tmp/premarket-delivery-remediation-plan-20261028/baseline.json):18개 중9개가 mutable 작업본과 다르다. 구현 착수 당시 최신 선택본과 승인된 병행 작업을 다시 대사한다. 작업본 전체 복사·오래된 후보 재배포·무관한 변경 덮어쓰기를 하지 않는다.
- session `NXT_PREMARKET`, policy cohort `PRE/NXT`와 runtime alias `premarket_krx_like`, data route `nxt_only`/item `_NX`, broker 요청 `NXT`를 각각 결속한다. 역사 PRE/SOR는 원 계약·item/route를 따로 검증하고 현재 PRE/NXT 수용으로 합산하지 않는다. 실제 체결 거래소는 명시적 execution receipt 전까지 unknown이다.
- 현재 준비된 BUY 창08:03~08:40을 유지한다. 시작 전 대기를 collector 결함으로 분류하지 않는다. 시작시각·패널·API·슬롯/체류/재시도 변경은 source 수리와 구분한 후보이며 자동 적용하지 않는다.
- 현재 실행 owner는 `MachinePatternOpportunityResearch1023`와 `MainEntrySourceTerminalRepair1022`다. 신규 OPEN ID·cron·worker·원장·startup validator를 만들지 않는다. 완료된10/27 공통 수리는 재개발하지 않는다.

근거: [PRE 원인·후행 대사 §15~§16](../audits/main-regular-nonfixed-opportunity-and-auxiliary-adequacy-review-2026-10-27.md#16-프리마켓-전달보조판정과-후행-결과-대사--2026-10-28-0840), [공통 전달 수리·구현](main-regular-submit-deadline-fresh-recheck-and-discovery-latency-remediation-plan-2026-10-27.md), [기존 보조 연구·예산·유형별 결과](main-auxiliary-spread-liquidity-and-deadline-remediation-plan-2026-10-27.md), [공통 저장 계약](main-ai-comparison-ledger-dedup-and-incremental-storage-plan-2026-10-07.md). PRE 후속 상세 범위는 이 문서가 소유하고, 공통 수리·저장·안전 계약은 기존 owner가 유지한다.

## 2. 원 사례와 분류

| 사례 | 확인한 사실 | 처리 |
| --- | --- | --- |
| 케이아이엔엑스093320 |08:05~08:10 가격+10.83%;08:07:31·08:09:01 적격 대기,08:19까지 claim0 |최초 관찰 배분 비교. 가격 상승만으로 실행 가능한 WIN/놓친 주문을 확정하지 않음 |
| 삼아알미늄006110 |08:05~08:15 +2.46% 창 이후08:16:45 첫 배정 |적격 대기·관찰 요구·당시 slot 순서 재생 |
| 나무가190510 |첫 관찰 수신 공백/stale 종료 뒤 후속 상승 창 재관찰0 |원 stale 유지; 다음 적격·retry due·새 발견·배분 순서 대사 |
| 알테오젠196170 |기계 ENTER17/provider17→유효PASS3·CAUTION10·의미 검증 거부1·timeout3 |PASS3은 원5초 소진2·별도latency clock1. AI 실패 예측과 분리 |
| 심텍222800 |원2신호 모두121,900→121,800 유지선 위반 후 invalidated_before_claim |정상 재검사 음성군. 인계 결함으로 제거하거나 원 신호 복구 금지 |
| RFHIC218410·안랩053800 |비상시 중가 Main PASS2·BUY receipt2·원 ask 관측 trade 경로WIN2 |정상 전달 회귀군. 안랩 ask95,400/체결96,200·실현 손익/venue는 별도 |
| 가비아079940 |exact lease 수신은 있으나 context refresh는 ValueError class만 기록 |context/기한 실패 원인 재현 전 OPEN |

08:19 queue185/미배정152와 중지 뒤08:32 queue188/미배정155는 서로 다른 snapshot이다. 미배정을 모두 적격 대기·실패 기회로 계산하지 않는다. 중지 전 probe42행과 종료 경계 generation-changed5행도 분리한다. 유효 Main 기계19개·local 원천 부적격1개·probe-only1개를 구분한다. [분모·원기한·BUY·U 결속](../../tmp/premarket-delivery-aux-review-20261028/final-review.json).

## 3. P0-A — 최초 관찰·재관찰 전달

### A1. 실제 배분과 상태 전이를 재현한다

기존 [queue](../../src/scanners/zero_base_discovery_queue.py)의 `observe/claim/resolve`, [runtime](../../src/scanners/zero_base_discovery_runtime.py)의 `finish_scan/drain_results/dispatch_due_probes`, [probe](../../src/engine/scalping/zero_base_probe.py)를 확장한다. 미관찰 우선·activity/age 순환·long residence 보상·short-slot 예약/borrow는 이미 존재한다. 새 fairness queue를 만들지 않는다.

1. 보존된 discovery/admission/queue/lease·consumer readiness·slot 반환을 시간순으로 대사한다. 당시 master·active/manual·fresh/due·관찰 요구·실제 저장/반납 증거가 있는 창만 원 실행 재현으로 인정한다. 현재 snapshot만으로 과거 dequeue를 역산하지 않는다.
2. 발견, 최초/재관찰, `eligible_due` 관측, claim·등록 송신·첫 exact 수신·필수 입력 성숙·기계·최종 편입/거부를 연결한다. `eligible_since`는 dispatch 표본상 대기이며 연속 적격으로 추정하지 않는다. restart/stale/active 전이 뒤 대기를 과거 first_seen에서 가져오지 않는다.
3. 실제 적격 후보·physical lease·고유 종목/기회 구간·Main attempt의 분모를 나눈다. 로컬 등록·서버 종목별 ACK·실제0B/0D 수신도 구분한다. 미구독 창에 synthetic tick/기계 결과를 만들지 않는다.
4. source 갱신과 원 claim 대응·`next_due` 전이를 검사한다. 새 발견이 in-flight 원천을 바꾸거나 due를 잃는지, 종료 뒤 active cache가 남는지, slot 반환 뒤 불필요 대기가 생기는지 원 형태로 시험한다. 확인된 전이/wake 결함만 기존 owner에서 수리한다.
5. 원 순위·시각 증거가 없으면 과거 원인은 null로 남기고 기존 admission delta에 최소 필드를 추가한다. 새 주기적 전수 로그·중복 원장은 만들지 않는다. 다음 같은 PRE branch에서 자연 원인 확인을 이어간다.

### A2. 기존 자원 안에서 두 배분 후보를 비교한다

먼저 동일 source·도착·slot 점유/반납·체류 요구로 현행을 재생한다. 전이 결함 수리와 아래 배분 정책은 별개다.

| 후보 | 동결할 변경안 | 확인할 부작용 |
| --- | --- | --- |
| Q1 최초 관찰 대기 |기존 oldest-service turn에서 first_seen 대신 현재 인증된 적격 대기/service 대기를 우선 비교. 기존 long-deferred 우선권·cohort·short 예약과 나머지 activity turn 유지 |restore/시각 결손의 허위 우선권, activity 기회 지연, 긴 관찰 독점 |
| Q2 재관찰 기아 |현재 due를 지난 재관찰이 있으면 기존 age turn에서 마지막 service 대기와 최초 후보의 적격 대기를 함께 비교. 같은 turn 사용, 새 batch/예약 slot 없음 |신규 후보 기아, 같은 종목 반복 점유, panel SHA 변경을 새 기회로 오인 |

Q1/Q2는 사전 봉인할 배분 후보이며 source 수리에 숨겨 적용하지 않는다. exact sort key·동점·state 수명/restore·source 조건을 동결한다. 인증된 대기 정보가 없으면 현행 순서를 유지한다. 기존5슬롯·동시성·lease/short 예약·체류·retry due를 유지하고, 이미 실행 중인 lease 중단·재시도 앞당김·미래 상승 우선순위는 없다.

최초/재관찰별 적격 대기 분포/최댓값, 성숙 전 이탈, 기계/Main 도달, 종목별 반복 점유, dispatch/writer 비용을 비교한다. 미관찰 종목의 가상 lease에 다른 종목 체류나 결과를 대입하지 않는다. exact source가 보존된 경우만 후보 기계 W/STOP/TIMEOUT/U를 계산하고, 나머지는 배정 시각 모의 비교·기계 결과 미관측으로 분리한다.

검토 기준은 동일 적격 입력에서 지연/기아 감소·guard/resource 위반 없음과 검증 가능한 추가 승리/실패의 변화다. 지연 감소만으로 alpha 우월성을 발행하지 않는다. 배분 순서 변경은 비교 결과·원 정책/수명·되돌릴 설정을 갖춘 승인 대상으로 제시한다.

### A3. 발견 이전 범위는 별도 대사한다

현재 PRE [source owner](../../src/scanners/zero_base_discovery_source.py)는 activity 패널이며 독립 가격 패널 전체를 발견하는 계약은 아니다. 이오테크닉스처럼 큐 이전에 없는 종목은 Q1/Q2의 실패가 아니다. 기존 필터 전 응답/제외 사유로 범위를 대사한다. activity+gainers·API/연속조회·구독 추가, 시작08:03 변경은 자동 구현하지 않는다. 필요성이 입증되면 공식 Kiwoom Reference Gate와 요청/부하·운영 권한을 갖춘 별도 변경안으로 제시한다. 과거 무수신을 API 결함/정상 무거래로 단정하지 않는다.

## 4. P0-B — PASS 이후 정상 제출 전달

### B1. 같은 attempt의 두 시계를 결속한다

원 native signal+5초/wall/perf와 [EntryPolicy](../../src/trading/entry/entry_policy.py)의 signal reference 기준1,200ms는 다른 수명이다. 시작점을 같다고 간주하거나5초로 합치지 않는다. [signal reference owner](../../src/engine/sniper_entry_latency.py)의 `freeze_signal_reference/clear_signal_reference`, [Main caller](../../src/engine/sniper_state_handlers.py)의 `_submit_watching_triggered_entry`와 직접 반환, async result, [physical guard](../../src/trading/entry/physical_send_guard.py)를 함께 본다.

1. 08:05:48의4.9초 허용/5.233초 거부는 [원 입력 재현](../../tmp/premarket-coverage-20261028/exact-auxiliary-deadline-validation.json)을 재사용한다. generic 오류를 정책 변경으로 오분류하지 않는다.08:09:56의10~12ms 초과도 원 판단과 로그 발행 시각을 구분한다.
2. 08:06:05는 원5초 내 별도latency 차단이다. `entry_signal_time/price/strategy_id`, request/evaluation/trace/native claim·deadline, freeze/clear caller를 같은 attempt에 연결한다. 원 reference가 없는 과거 잔존 여부는 null이며 새 진단을 과거 원인 입증으로 소급하지 않는다.
3. 같은 strategy의 이전 시도가 auxiliary 반환/예외/취소 뒤 reference를 남겨 새 claim에 재사용하는지 격리 재현한다. 재현되면 기존 freeze/clear owner에서 attempt 소유권을 결속하고 해당 시도 종료 시 정확히 정리한다. 이전 주문/부분체결/uncertain reference는 새 BUY를 위해 지우지 않는다.
4. 현재 freeze가 producer 계약에 맞으면 임의로 응답시각으로 옮기지 않는다. 올바른 두 clock의 정상 거부는 유지하고 실제 불필요 비용을 B2에서 줄인다. 새 시계·deadline 상향·now+5는 없다.

필요한 최소 소유권/clock 필드는 기존 call-local terminal·timing/disposition에 추가한다. 분류 세분화 자체를 완료로 삼지 않고, AI·자금 통과 후보가 같은 기한·가격·안전 조건에서 정상 submit과 adapter까지 이어지는지를 시험한다.

### B2. 실제 critical path 비용을 줄인다

| 구간 | 작업 | 유지할 경계 |
| --- | --- | --- |
| 입력/요청 전 |현재 immutable loader·필수 binding 투영의 배포된 수리 확인. 같은 즉시 경계의 반복 thaw/hash/직렬화·진단 I/O가 실측될 때만 통합 |현재 pointer/dependency·native eligibility는 독립 소비 경계에서 재검사 |
| 응답→Main |기존 coordinator 완료 수집·wake·Main 소비 대사. 동기 일반종목/비동기 상시 경로 모두 검사 |다른 request/generation 결과 채택 금지, 원 deadline 유지 |
| Main→submit |필수 저장·native 검사·분할/수량·intent 순서의 wall/perf 비용 비교. 원인인 중복 reader/복사만 기존 owner에서 제거 |필수 trace/outbox/intent append·fsync 성공을 enqueue로 대체하지 않음 |
| submit→adapter |실제 caller를 통해 source/quote/가격·route·수량·custody/기한 검사. 만료 조기 종료와 최종 재검사 함께 유지 |SAFE/CAUTION은 기존 slippage 후 정상 경로. DANGER/stale/계좌/주문 guard 보존 |
| 만료/가격 변경 뒤 |기존 verified NOT_SENT→새 native claim→fresh 기계/AI 경로의 wake/정리 재사용 |옛 PASS/소비 claim 재사용·불확실 주문 재전송·무한 재가격 금지 |

동일 원 입력·정책·가짜 provider/계좌·격리 writer에서 원/후 코드의 전체 submit 경로를 비교한다. broker adapter만 no-network spy로 바꾸고 submit 성공 stub은 쓰지 않는다. 준비, provider/대기, 응답 저장, 완료 전달, Main, 최종 검사의 중첩을 제거해 순수 local 비용을 보고한다. cold/warm·경합·저장 포화·파일/세대 변경과 지연의 다른 큐 전가를 확인한다.

코드 완료는 같은 기한 내 정상 fixture의 정상 submit/단일 initial leg adapter 도달, 원기한/가격/안전 거부 fixture의 adapter0, 불필요 local 비용 감소다. 모든 과거 PASS의 강제 제출이나 실주문을 요구하지 않는다. 새 자연 표본의 잔여기한·정상 submit·정당한 terminal은 별도 확인한다. provider 자체가 예산을 소진한 timeout은 유지하고 offline transport 한도를 live에 복사하지 않는다.

## 5. P1 — 누적 PRE 모집단과 유형

### C1. 누적 전수와 실제 전달 표본을 나눈다

1. 기존 [population owner](../../src/engine/scalping/reversal_auxiliary_research_population.py)에서 retained inventory 전체를 열거하고 PRE 원천일별 적격/제외/U·사유/hash를 보고한다. clean boundary와 더 좁은 family refresh인2026-09-29 이후 적격 누적을 평가한다.09/28 이전 자료는 역사/audit·custody 역할로 보존한다. 실행 시 native source scope/발행 계약이 더 좁으면 그 차이를 공개한다.
2. 실제 과거 기계 ENTER·AI 요청과 현재 선택 정책의 누적 원천 재생 확인점을 분리한다. 전자는 실제 전달/오판, 후자는 현재 정책의 미호출 확인점까지 포함하는 모집단이다. 재생 ENTER를 과거 실제 호출/감시/주문으로 표시하지 않는다. 큐 이전·관찰 미도달은 A의 coverage 분모로 남긴다.
3. session·item/route/transport epoch/sequence, 원 ask/확인시각·정책/branch·요청 schema를 고정한다. 이후 가격은 label 전용이다. 같은 종목/일자/route의 중첩30분 구간과 복수 branch의 동일 기회를 cluster로 묶고 attempt/고유 확인점/독립 구간 수를 각각 제시한다.
4. 라벨은 **최대30분·비용 후+0.4%·소프트손절−3%보다 목표 선도달**이다. 비용은 승인된 label contract에 결속한다. 오늘 kernel의0.23%를 임의 실비로 바꾸지 않는다. WIN/STOP/TIMEOUT/U와 trade 경로/실행 가능한 bid·실제 fill/완료 손익의 증거 등급을 분리한다. 가격 기준이 다른 라벨을 같은 승률 분모로 합산하지 않는다.
5. 봉인·연속성/비용 결손은 row/window 제외 또는 U로 보존한다. 오늘 알테오젠17개는 중지로 path_end_before_horizon이며 단순 대기로 TIMEOUT이 되지 않는다. 기존 보강 경로가 같은 item/창을 독립 인증할 때만 새 label revision을 발행한다. 원 U/실패를 덮어쓰지 않는다.

### C2. 상시·비상시와 종목유형을 구분한다

| 축 | 기준 |
| --- | --- |
| 감시 |원 확인시각의 설정상 상시 여부와 실제 fixed-watch/비상시 probe→Main attachment를 각각 보존. 실제 이력 미확인은 UNVERIFIED. 현재5종목 설정으로 과거를 추정하지 않음 |
| 시장/경로 |PRE 주 평가, 원 PRE/NXT·PRE/SOR를 정책·data/요청 route별 분리. REGULAR/AFTER는 회귀용이며 PRE 우월성 대체 불가 |
| 종목유형 |기존 catalog 종목group·LT_20000/20000_TO_100000/GE_100000. 원 확인가격과 native band/cell_key 사용;20,000·100,000 경계 확인. 삼성 native ALL scope는 유지하고 종목 표 추가 |
| 패턴/길이 |원 decision phase·선택 branch·실제 접두 길이·coverage를 보조 분석. 임의 섹터/유동성 class·새 수치 veto를 만들지 않음 |

유형별 실제 prompt/registry/input transform SHA를 고정한다. 모든 종목에 A나 하나의 새 prompt를 일괄 배정하지 않는다. 기존 A는 승리 복원 회귀군이며 현행 운영 prompt와 같은 것으로 간주하지 않는다. 기존22개 PRE 탐색 표본/실제 감시 확인3개를 누적 전수로 부르지 않는다. UNVERIFIED는 설정상/재생 연구에 활용할 수 있으나 실제 감시별 자연 효과와 분리한다.

## 6. P1 — 짧은 관측과30분 목표를 구별하는 입력 연구

### C3. 계산 가능한 사실의 역할·시간구간을 분리한다

기존 [risk-role 변환](../../src/engine/scalping/reversal_auxiliary_risk_role_experiment.py)의 `_path`는 `recent_return_minus_target_gap`과 목표거리 등을 같은 risk citation에 연결한다. production은 [SHA 고정 opt-in owner](../../src/engine/scalping/reversal_auxiliary_production_input.py)를 사용한다. [risk-context 실험](../../src/engine/scalping/reversal_auxiliary_risk_context_experiment.py)은 이미 접두와 미래 목표를 구분하지만 연구 전용이고, 이전 E/F는 승리 손실·실패 PASS 개선 부재로 미채택이다. 문구가 있다는 사실을 운영 개선으로 세거나 후보 이름만 바꿔 재등록하지 않는다.

연구용 I/IP는 기존 risk-context 실험 owner의 명시적 opt-in 모드로 확장한다. production이 SHA로 고정한 기존 risk-role 변환은 연구 편의를 위해 수정하지 않는다. I/IP의 계약·실제 요청 bytes를 별도로 결속한다. 이후 효과가 확인돼 production 입력 전환을 구현할 때만 기존 publisher/compatibility registry·직접/전이 소비자 목록을 대사해 정확한 신구 계약과 실패 음성을 함께 검증한다. 새 hash pair 하나를 추가한 것만으로 현행 소비자 인계를 완료 처리하지 않는다.

후보는 기존 실험 owner에서 아래 사실을 간결하게 투영한다. 원 확인시각까지의 prefix만 사용하고 구간 시작/종료·단위·coverage·native identity를 결속한다. 새 input contract는 serializer/validator round-trip도 함께 검증한다.

| 사실 | 후보의 표현·역할 |
| --- | --- |
| 미래 목표 |net target/horizon, 원 ask·비용에 따른 필요 가격과 현재 확인가격 대비 거리. 목표의 정의/기하학적 거리이며 단독 실패 반증이 아님 |
| 과거 관측 |실제 접두 span·표본수/coverage·수익률.13초 상승을30분 진척으로 해석/선형 외삽하지 않음 |
| 과거 수익률−미래 거리 |후보 I는 이 유도 차이의 risk 바인딩과 모호한 진척 비교를 생략. 원 입력/응답은 보존하며 거리/과거 수익률 원 사실은 유지해 정보 은폐와 구분 |
| 회복 유지/새 손상 |원 phase·anchor 이후 같은 구간의 trade·최저/최고·되밀림, 알려진 방향/수량/coverage, 검증된 bid/ask 변화. 회복 전 매도를 현재 실패로 단정하지 않음 |
| 호가/유동성 |절대 spread/비율은 중립 사실. 같은 구간의 bid 후퇴·ask·수량 악화는 실제 근거가 있을 때 별도 사실. trade 반등을 bid 개선으로 대체하지 않음 |
|30분 미달 위험 |회복·흐름·목표거리를 함께 평가하되 새 되밀림과 별도 해석. 임의 도달 확률/예정시간·‘짧으니 PASS’를 생성하지 않음 |

짧은 접두가 기계 최소 관찰을 충족하면 그 길이만으로 부정 증거가 되지 않는다. optional 결손은 unknown, 필수 source/clock 결손은 해당 행 부적격이다. 실제 새 매도·되밀림과 source/기한 실패는 보존한다.

유형별 prompt 후보 P에 공통으로 넣을 영어 ASCII 연구 초안:

```text
Past prefix return and the future 30-minute target use different intervals.
Do not subtract past return from the post-entry target or extrapolate a short prefix.
Target distance alone is not evidence that the entry will fail.
Assess current recovery, newly observed damage, and target-reach risk separately.
Use price, known-side quantity, and verified quotes from matching intervals.
Missing optional observations are unknown. Do not force PASS or invent thresholds.
```

기존 유형별 prompt 위에서 비교한다. 상시라는 이유로 현재 접두를 긴 관측으로 확장하지 않고, 비상시의 짧은 lease/optional 결손만으로 실패를 추정하지 않는다. 가격대별 절대 호가폭/거리 해석은 실제 quote를 쓰며 숫자 veto를 발명하지 않는다. 최종 문구 공유 여부도 유형별 결과로 판단한다.

### C4. 네 arm으로 입력·prompt 효과를 분리한다

| arm | 입력 | prompt | 역할 |
| --- | --- | --- | --- |
| N |동결 현행 입력 |각 유형의 현행 prompt |운영 대조군 |
| I |C3 개선 입력 |N과 동일 |입력/사실 배치 효과 |
| P |N과 동일 |유형별 시간구간 해석 개선 |prompt 효과 |
| IP |I와 동일 |P와 동일 |결합/상호작용 |

모델·endpoint·생성 설정·출력 schema·semantic validator는 가능하면 고정한다. 새 사실로 validator 변경이 필요하면 별도 validation identity/호환 범위를 기록해 계약 차이를 prompt 효과로 합산하지 않는다. exact wire 요청이 같을 때만 cache를 재사용한다. label만 정정되면 요청은 재호출하지 않고 원 응답 참조+새 label로 집계한다.

개발 진단군은 알테오젠 초기 CAUTION4개·137310 STOP PASS·111770 승리 오차단·기존 A 회귀 및 유형별 실패/승리를 대조하되 실제 PRE 기록만 PRE 성과에 넣는다. 다른 시장의111770은 cross-market 회귀다. 오늘 U는 사실/해석 시험에만 쓰고 승리 복원 계산에서 제외한다. 이미 본 개발군과 최종 평가군은 분리한다.

### C5. 호출·독립 평가·판단

1. 전수 eligible census와 기존 exact 요청/응답 inventory를 호출0으로 준비한다. 기존 [research owner](../../src/engine/scalping/reversal_auxiliary_research.py)와 공통 store의 partition/content 참조를 재사용한다. 현행 N과 과거 native live 요청이 다르면 같은 대조군 응답으로 쓰지 않는다.
2. 개발 배치는 **최대24개 고유 확인점×4arm=96요청**이다. 원 오류 진단군과 유형·길이·W/STOP/TIMEOUT 층화 표본을 사전 동결한다. 부족 유형은 부족으로 남기고 label은 요청에 넣지 않는다.
3. 독립 평가 배치는 **최대40개×N/사전 고정한 유형별 후보=80요청**이다. 개발·기존 연구와 겹치지 않는 날짜/종목-원천-시간 cluster를 우선한다. 같은30분 구간의 새 branch/key는 독립 표본이 아니다. 독립 날짜가 없으면 시간 분리/한계를 공개하고 탐색 상태를 유지한다. auxiliary holdout을 기계 자체의 독립 검증으로 확대하지 않는다.
4. 변동 진단은 사전 지정한 **최대12개 추가 attempt**다. 좋은 응답만 골라 성과를 바꾸지 않는다. 초기 설계의 최악 신규량은188회이며 exact cache만큼 감소한다. 이는 신규 허가/한도가 아니다. 실행 직전 native 누적 grant·차감/uncertain·동시 예약을 대사해 미호출 차집합을 기존 한도 안에서만 처리한다. 잔여/미완료를 공개하고 날짜/arm별 예산 초기화·장후100-attempt 예산 합산을 하지 않는다.
5. 전수 원천의 날짜별/누적 W/STOP/TIMEOUT/U와 sampled paired 성과를 분리한다. 실패 진단 과대표집의 raw 승률을 모집단 승률로 발표하지 않는다. 가능한 경우 층별 비중/포함확률로 추정치를 별도 제시하고 표본수·독립 cluster·선정/비응답 편향을 공개한다.

필수 표는 `날짜/누적 × 실제 상시·비상시·UNVERIFIED × 종목group/가격대 × PRE 경로`별 승리 PASS/비PASS, STOP PASS, TIMEOUT PASS, 유효 PASS 승률, input/response invalid, provider timeout·U다. 같은 쌍의 승리 복원/손실·실패 차단/새 실패 PASS와 A 승리 보존 회귀를 함께 낸다. 한 유형의 이익으로 다른 유형의 손실을 가리지 않는다.

실행 완료 후 각 유형의 현행/후보 요청·input/response/validator·원천/label 참조와 누적/독립 평가 결과를 기존 연구 manifest에 봉인한다. 장후는 등록된 후보를 평가하는 기존 owner를 사용하며, 이번 연구 모드를 자동 prompt 생성·전유형 일괄 등록·호출한도 해제 기능으로 연결하지 않는다.

해당 scope에서 **기존 승리 PASS를 보존하며 실패 PASS가 줄어드는지**를 우선 판단한다. 승리 복원만 있고 실패 PASS가 그대로면 탐색 효과로 구분하고, trade-off는 값을 공개해 자동 교체하지 않는다. 한쪽 label만 있는 소표본100%·호환성 PASS로 우월성을 선언하지 않는다. 손익비·양의 실현 PnL·보편 uplift를 새 진입 채택 조건으로 덧붙이지 않는다. 운영 등록/발행은 기존 native 계약을 별도로 충족해야 한다.

## 7. 순서·산출물·리뷰

아래 산출물은 기존 보고서/partition 안의 진단이며 신규 runtime gate가 아니다. 지표 계약은 다음과 같이 명시한다.

| 필드 | 전달/제출 대사 | 보조 연구 |
| --- | --- | --- |
| metric_role |funnel_count |diagnostic_win_rate |
| decision_authority |기존 owner의 원인/배분 후보·source 수리 검토 |유형별 연구 후보 비교, 기계 승격/운영 적용 권한 없음 |
| window_policy |동일 PRE source-date/actor/item·dispatch 적격 창, 원 attempt 시계 |적격 누적 PRE·고정 확인점/cluster·동일 paired/label revision |
| sample_floor |정확한 시각/신원·상태가 확인된 사건1개부터 진단. 부재는 null |적격 source·유효 응답/라벨을 가진 공통 pair부터 진단. 한쪽 label/독립 평가 부재는 우월성 미확정 |
| primary_decision_metric |최초/재관찰 적격 대기·성숙/기계 도달, 유효 PASS의 정상 submit 도달/잔여기한 |동일 쌍의 승리 보존/복원과 실패 PASS 감소·유효 PASS 승률 |
| source_quality_gate |원 master·route/epoch·lease/PID/정책·clock·실제 writer/terminal |날짜/연속 원천·확인 접두·비용/label·watch 분류·exact 요청/validator 결속 |
| forbidden_uses |단독 수익/venue/정책 승인·guard 우회·미배정 전부를 놓친 주문으로 집계 |표본의 전수 우월성·실현 손익 주장·A의 전유형 배정·runtime 게시/기계 BLOCK 승격 |

| 단계 | 작업 | 다음 단계 기준 |
| --- | --- | --- |
| S0 |선택/정책·중지 actor·원 사례/18개 SHA 재확인 |완료 기능·실제 결함·정상 거부 구분 |
| S1 우선 |A1 적격/전이와 B1 두 clock·직접 return 재현 |확인된 source/reference 결함만 수리. 미재현은 null+다음 정확 창 |
| S2 우선 |B2 실제 비용·A1 wake/반납/상태 수리 |구현→리뷰→보완→재리뷰→정상/음성·동기/비동기 caller 회귀 |
| S3 |Q1/Q2 비교와 C1/C2 누적 census·기존 응답 재집계 |실제/모의 도달·미관측 분리. 호출0으로도 기존 오판 보고 |
| S4 |C3~C5 네 arm/독립 paired |grant 내 미호출만 처리. 유형별 탐색/검증/미채택·미완료 표시 |
| S5 |전달 수리와 후보 인계 |최신 parent·consumer inventory·교체/삭제·실제 검증 영수증. prompt 미채택 때문에 source 수리 준비를 막지 않음 |
| S6 승인된 전환 |native running/stopped 경로·정책 인계·후보/선택 후 검증 |RFHIC stop/hold owner와 정합. 임의 시작/hold 삭제 없음. prompt는 해당 scope 게시/소비 별도 |
| S7 자연 수용 |정확 PRE의 실제 PID/정책/item/route로 관찰·새 PASS→submit 대사 |정상 submit/정당한 guard terminal까지 확인. 주문/구독으로 표본 제조 금지 |

기존 검증 위치와 음성 범위:

- A: `test_zero_base_discovery_queue/runtime/source`, `test_zero_base_probe`, `test_zero_base_main_attach`. 신규 폭주+due 재관찰, long/short 예약, stale→fresh·active 해제·in-flight 갱신, fsync/rollback·restore·중복 callback·정상 stop/generation.
- B: `test_entry_shared_deadline_latency`, `test_scanner_async_entry_bridge`, `test_entry_physical_send_guard`, `test_main_integrated_bottlenecks`, `test_entry_split_order_plan`, `src/trading/tests/test_entry_policy.py`. 동일 strategy/새 attempt·잘못된 clear,5초/1,200ms·wall/perf, 다른 PID/route/policy·quote 변경·부분체결/uncertain·동시 completion.
- C: 기존 `test_reversal_auxiliary_risk_role_experiment/risk_context_experiment/production_input/wire/research_population/prior_inventory/research`, `test_offline_comparison_store`. prefix 경계·미래/label 누출·단위/시간·optional missing·route/watch 미확인·identity/계약 위조·cache 정확성·uncertain 차감.
- 실제 수정에 맞춰 기존 fixture를 확장하고 compile·`git diff --check`를 수행한다. 문서 단계는 trading suite/provider 실행 없이 링크·owner·권한·print-only backlog로 검증한다.

다음 native 거래일 PRE 수용 창은10/29 08:05~08:20이다. 실제 승인된 적용/기동이 없으면 관측 예정이며 완료 약속이 아니다.10/28 REGULAR09:30~10:00·source28 장후 Acceptance는 유지하고 PRE로 대체하지 않는다. 이 문서는 새 예약이나 장후 전체 재실행 지시가 아니다.

## 8. 저장·의존성·대체/제거·완료 경계

같은 입력/원 응답은 공통 store에 한 번 보관한다. 전수는 작은 census/partition, 선정 pair만 materialize한다. 실제 변경 source/feature/input/prompt/validator/label의 영향을 받은 partition만 재생하고 최대30분/anchor·정정 의존성을 보존한다. token/계좌 값은 출력하지 않는다.

구현 전 source/정규화·요청/응답·label·집계·게시·독립 preparation·strict/controller·최종 PID 소비별 `reuse/read-only revalidate/regenerate`, issuer/reader·source/code/scope SHA를 기록한다. 이번 문서 작업 재생성0. S2도 무관한 EOD·완료 장후·AI 전체 원장 재생성의 사유가 아니다. 실제 무효화된 consumer만 native 절차로 갱신하고 terminal 봉인 뒤 추가 PASS를 위해 다시 쓰지 않는다.

| 처분 | 대상·이유/종결 |
| --- | --- |
| retained |queue/admission·lease/native 편입, 원5초/별도latency, 가격/계좌/수량/주문/custody·outbox, 공통 store·원 응답/실패/U·역사 reader. 현재 또는 봉인 증거 소비자가 있음 |
| consolidated 후보 |재현된 동일 경계 copy/hash/emit·reference 정리. 실제 caller 전환/실패 unwind 뒤 기존 중복 제거 |
| removed 후보 |대체된 잘못된 시도간 reference 재사용/중복 처리. 과거 증거는 삭제하지 않음. 아직 제거 완료가 아님 |
| research-only/deferred |Q1/Q2·I/P/IP 운영 적용. 누적/paired·발행·운영 권한 충족 뒤 해당 scope만 전환. 부족 표본/복원 불가/경제성은 기존 owner에 null/OPEN |

결과는 코드/리뷰·배분/prompt 선택·배포·정확 PID·자연 전달/제출·후행 라벨·완료 손익을 구분한다. 기준 commit과 non-test source/test/doc 추가·삭제, consumer/entrypoint 증감을 기록한다. 신규 runtime 모듈·worker·원장0을 기본으로 기존 package owner를 확장한다. 표본 부재로 코드 수리를 반복 재개발하거나 guard를 낮추지 않는다.

리뷰는 기존 기능 중복, 두 clock 합산/갱신, 미관측 가격의 WIN 승격, 실제 watch 추정, census/표본 혼동, A/현행 N 혼동, 과거 negative 결과 은폐, 운영/중지 권한 누출을 확인한다. 이번 결과는 문서와 작은 baseline/검증 참조다. [계획 검증](../../tmp/premarket-delivery-remediation-plan-20261028/validation.json)에 링크·단일 current owner·strict 원본·parser·diff를 기록한다.


## 9. 후속 구현 승인·배포 전 검증 결과 — 2026-10-28

사용자가 본 계획의 구현·리뷰/보완·추가 누적 PRE 연구 호출과 배포 전 결과 보고를 후속 승인했다. 위 최초 계획-only 상태는08:54의 이력이다. 구현은 기존 scanner slot 반환 후 정상 admission wake, Q1/Q2 opt-in 후보, native 계약을 보존하는 temporal 입력, PRE scope inventory와 complete127-member 인계/독립 준비 reader에 반영했다. PASS 지연은 병행 완료된 identity-bound clock·준비 복사 수리 parent5f20853f6와 통합했으며 단순 종료 cleanup을 중복 적용하지 않았다.

누적 현행 기계 확인점3,552건 중 W798/STOP272/TIMEOUT101/U2,381이다.10/13 PRE 원천은 존재하지만 native 검증80,389행 모두 종료 epoch 미인증으로 제외했다. 실제 감시 fixed41/probe114/미확인3,397을 분리했다. 신규 AI91회·기존 exact 응답12건 재사용으로24점4arm 개발과 독립2점/기존 Main 진단2점 평가를 마쳤다. trade23점에서는 N8승/17PASS→I11/20·P8/16·IP12/21이며 bar 보강1점은 별도다. 유형별 조합의 개발값13/21은 탐색 성과이고 STOP3점 전부 PASS·독립 평가 실패 표본0이라 운영 채택은 하지 않았다.

runtime 통합의 fixture3개 결손을 보완한 후 영향5모드와 최종 전체1,308개가 통과했고, 인계46·독립 준비993·codec128·실제 입력 admission3건 검증을 기록했다. 중복 수치는 합산하지 않는다. 코드668d76c0c의 상세 변경·교체/보존·정확 consumer/stage·예산·실패/제외·다음 자연 수용은 [기존 audit §18](../audits/main-regular-nonfixed-opportunity-and-auxiliary-adequacy-review-2026-10-27.md#premarket-delivery-implementation-20261028)이 소유한다. 배포·재기동·hold/selector·운영 정책 변경0이다. native 최종 P5/active-parent/선택 후 준비/실제 PID는 최종 RFHIC 전환 세대에서 별도 검증하며 현재 배포 준비 PASS로 합산하지 않는다.
