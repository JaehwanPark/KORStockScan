# 준비·전달 보완 이후 잔여 병목과 미식별 패턴 상세 연구계획 — 2026-10-12

상태: **10/12 상세계획·연구 리뷰 이후, 10/13 후속 승인으로 R1/R2/R4와 신규6정의 구현·검증·등록·배포 및 기계/보조 정책 발행을 실행했다. 최신 장후 인계·복구 최종화07:00:37 종료와 target13 기동 준비 전체 계약을 확인했다. 실제07:35/07:55 수용은 미래 Acceptance다.** 본문의 미실행 기록은 원 연구 요청 당시 경계다. 18:30 일회성 점검도 실제 완료했으며 초기 17:15 기준과 분리해 아래에 반영한다.

## 2026-10-13 승인 구현의 리뷰 보완

사용자의 후속 구현·신규 패턴 등록·배포 승인에 따라 아래 실행 범위를 추가한다. 본문에 남은 미실행 표시는 10/12 연구 당시의 역사 기록이다. source date는 10/12, 다음 기동일은 10/13이며 05:35 native 최종화 감시를 함께 유지한다.

- R1은 ANY_MATCH 최소시간을 유지하고 전체 branch 입력시간·긴 관측 대기 횟수를 별도 생산한다. mixed 후보는 긴 슬롯 만석일 때 짧은 슬롯에도 들어가고, 다음 순환에서 긴 슬롯 우선권을 갖는다. 5슬롯/긴2개/60·150초와 원 deadline은 유지한다.
- R2는 현재 공식 Kiwoom HEAD와 relevant SDK/spec을 확인한 뒤 depth ingress에 exact item의 route/suffix만 보존한다. 과거 count0을 소급 복원하지 않는다. R4는 같은 finalize 호출의 첫 실패 이유와 원 capture/lease/record 신원을 attach consumer에 전달한다.
- 신규 등록은 제안 JSON의 실제 6개 정의·4scope를 기준으로 한다. H14는 `dd_min=0.4, dd_max=1.2`이며 설명의 얕은 눌림으로 숫자를 바꾸지 않는다. H6의 실제 DOWN 경계는 `session_max_exclusive=-0.4`다. FIRST_HOLD1/3는 native FIRST anchor 가격 이상 유지 후 최초 실제 수신 확인점이다. BREAKOUT60은 native root와 exact parity를 검증한다.
- frozen 이전 catalog/부모 bundle은 역사 검증에 유지한다. 등록은 English ASCII ID·정의/원천/결과/현재 parent hash·explicit operator receipt·scope OR 합집합을 결속한다. 같은 tick의 다중 branch는 한 opportunity/보조 요청/intent로 소비한다. 지정 초기 등록에 추가 경제성·미래 날짜 gate를 만들지 않는다.
- R3는 이미 구현된 stage clocks를 사용하여 결손 errno/단계를 보강한다. 확인되지 않은 함수 비용을 추정해 최적화하거나 전체 결합 성능 PASS를 선언하지 않는다.
- 검증된 변경만 기존 장후 수리 릴리스와 통합한다. Main은 native EOD stop 이후 OFF다. 선택 릴리스·원 정책 provenance·13 준비를 갱신하고 실제 07:35 PREOPEN/07:55 PID 소비는 자연 acceptance로 분리한다. 구현 완료와 미래 실행 완료를 합치지 않는다.

## 1. 기준과 완료된 작업

- [기존 상시·비상시 보완계획](main-fixed-nonfixed-signal-readiness-and-latency-remediation-plan-2026-10-12.md), [native 구현 리뷰](../audits/main-native-signal-claim-implementation-review-2026-10-12.md), [준비·전달 구현 리뷰](../audits/main-fixed-nonfixed-readiness-implementation-review-2026-10-12.md)의 구현·후속 재리뷰를 출발점으로 삼는다. S0/S1, N0/N1/N2, native-ready wakeup, inbox 경합 수리를 통째로 반복하지 않는다.
- 17:15:20 원천 기준 최신은 `native-readiness-20261012-v2`, commit `cf650549e7a07ed470cd95a500af43336d31232c`, PID `1215171` / start ticks `4182334`다. 실제 cwd·selector의 수집 전후 안정성과 PID별 원천을 [잠정 snapshot](../../tmp/main-machine-remediation-research-20261012/current-snapshot/snapshot.json)에 보존했다. 18:30 예약 실행에서도 같은 릴리스·PID/start를 다시 확인했다.
- 상시 Main 정상 캡처 ENTER_NOW 10, 별도 probe BLOCK 1, async 요청 14의 worker 보조 결과 PASS 3·CAUTION 4·미평가/불명 7이다. 캡처와 async·native lifecycle은 서로 다른 단계/as-of이므로 하나의 보존식으로 억지 합산하지 않는다.
- 비상시 종료 70 = source 62 + `required_feature_insufficient` 7 + assessed 1이다. source 사유는 route snapshot 26, 0B 없음 19, 0B age 16, 준비 경계 age 1이다. 7은 window 미완료 5와 no-match 표시 2다. 후속 검증에서 두 no-match의 0D 수신 건수 증빙이 결손임을 확인했으므로 정상 source coverage로 완료 처리하지 않는다. provider/broker 실패 건수로 바꾸지 않는다.
- 최신 성능 receipt의 warm loop 288회 p95 .895초·p99 2.862초·최대 6.081초, native→claim 13건 최대 3.046초다. 작은 N의 p95/p99를 일반 성능으로 주장하지 않는다. 성능 receipt 시각과 source snapshot 시각도 분리한다.

## 2. 이번에 해결할 질문

| 우선 | 질문 | 직접 owner | 완료 기준 |
|---|---|---|---|
| P0 | 혼합 정책에서 긴 입력 branch가 계속 미성숙 상태인가 | residence descriptor → discovery queue → probe branch coverage | 짧은 branch의 admission을 보존하면서 긴 branch에도 기존 긴 슬롯의 공정한 관측 기회 제공 |
| P0 | 0D 수신 건수 계측의 route 메타데이터 결손과 source 62건의 첫 단절 | WS depth history → probe observation → monitor, exact lease·N2 receipt | 실제 0D의 정확한 건수·source 검증 결속; 미입증/quiet와 freshness 유지 |
| P0 | probe ENTER가 Main 편입에서 왜 거절됐나 | `_zero_base_finalize_candidate_record` → `_zero_base_attach_receipt` → Main capture | 동일 lease/capture/record/native 신원과 첫 실패 경계·원 5초·단일 물리 cleanup 연결 |
| P1 | 실제 유효 신호의 긴 claim/응답 로컬 구간은 무엇인가 | native lifecycle·Main scheduler·AI stage clocks | 동일 event의 원 예산·유효 구간과 직접 원인 결속; 확인된 중복 비용만 축소 |
| P1 | PASS 이후 정상 Main 소비와 기존 guard가 분리되나 | exact async disposition → 기존 Main stage | 같은 attempt의 PASS·native 재검증·최종 guard 연결. 정상 거절을 미소비로 표시하지 않음 |
| 연구 | 충분한 원천의 정상 불일치 뒤 상승지속·얕은 눌림 유형을 놓치나 | 고정 수동 가설 → 기존 누적 normalized source → native 승패 | 현재 적용 portfolio 단독/후보 단독/OR 합집합 비교, 추가 기회·실패·미확정·집중도 공개 |

정상 no-match는 새로운 상승 패턴의 존재를 입증하지 않는다. 충분한 원천의 반사실 목표 선도달과 기존 정책 비매칭을 함께 확인한 뒤 연구 잔여 기회로 분류한다. 미성숙·UNKNOWN·source gap은 그 분모에서 제외한다.

## 3. R1 — 혼합 branch의 관측 배정 보완

현재 `residence_requirements`는 branch별 시간 중 **최소값**을 전체 `minimum_seconds`로 낸다. legacy FIRST 0초와 60/120초 rolling branch가 함께 있으면 0초가 된다. 현재 queue는 이 값이 60초 이상일 때만 150초 슬롯을 선택하므로, mixed scope는 긴 슬롯이 비어 있어도 60초만 배정될 수 있다. 이는 ANY_MATCH의 빠른 평가 가능성을 표현하지만 모든 등록 branch의 관측 기회를 보장하지 않는다.

### 변경 설계

1. 단일 최소시간을 덮어쓰지 않고 `any_branch_minimum`과 branch별 `full_input_requirement`를 구분한다. 정의/registry/scope hash, history·transition/hold·side/qty 요구와 현재 UNKNOWN을 보존한다. 새 거래 threshold·정책 gate는 만들지 않는다.
2. 짧은 슬롯은 입력이 준비된 branch를 원 ANY_MATCH 계약대로 관측한다. 긴 입력 branch의 결손은 함께 남긴다. 짧은 branch가 TRUE인데 다른 branch가 UNKNOWN이라는 이유로 전체 기회를 기다리지 않는다.
3. 기존 전체 5슬롯·150초 긴 슬롯 최대 2개 안에서 cold long branch가 있는 후보에 긴 슬롯을 배정한다. long 필요성이 있는 mixed candidate는 짧은 admission도 가능하되, 긴 관측을 계속 못 받은 기간/횟수와 cohort 순환을 근거로 기존 긴 슬롯에 공정하게 재배정한다. 새 슬롯·구독·요청 한도는 없다.
4. 전체 `max(requirement)`를 무조건 admission gate로 사용하지 않는다. 짧은 실행 가능한 branch의 후보를 전부 긴 슬롯 대기로 보내는 수정은 실패다. 현재 lease를 mid-flight 연장하거나 첫 수신 시각으로 60/150초를 재시작하지 않는다.
5. 검증된 shared-owner 연속 prefix 재사용은 별도 최적화다. 현재 구현이 admission에서 그 연속성을 입증하지 못하면 재사용하지 않는다. 마지막 owner REMOVE·reconnect·route/session 교체 구간을 이어붙이지 않는다.
6. actual-price/scope 변경은 first-data 시 재검증한다. 올바른 branch로 바뀌어 필요한 이력이 증가하면 원 remaining residence와 부족을 남기고 기한을 연장하지 않는다.

### 검증

- descriptor `{legacy:0, momentum:60, volume:120}`에서 mixed scope가 영구 60초 순환만 하는 현재 배정을 작은 fixture로 재현한다.
- 5슬롯/긴2, long 만석, 짧은 TRUE/긴 UNKNOWN, 후보 3round 순환·price-band 변경·source reset·cleanup pending·중복/late ACK를 검사한다.
- branch별 complete/incomplete coverage와 실제 lease·대기·cohort 분모를 보존한다. UNKNOWN→FALSE/BLOCK 전환·실제 packet 없는 history 증가·반복 hint에 의한 예산 연장 0.
- 변경 위치는 기존 source diagnostics·discovery queue/runtime·probe와 관련 기존 테스트다. 별도 descriptor registry나 engine-root module을 만들지 않는다.

## 4. R2 — source 62건의 첫 단절과 source 품질

### 4.1 확인된 0D metadata 계측 결함

`003280`의 17:09:58 receipt에는 exact 0D route sequence 20·age 약167.7ms와 packet/callback/normalized 시각이 있는데 `zero_base_ws_exact_0d_count=0`이다. 기존 `_probe_verified_no_match`는 0D count>0을 요구하므로 이 행과 `002990`의 정상 no-match 표시를 source coverage로 검증하지 못한다.

직접 원인은 현재 WS depth builder/append가 이력 행에 `market_route`를 보존하지 않고, `probe_ws_observation.arrivals`는 각 행에 정확한 route를 요구하는 차이다. [기존 생산자 형식의 격리 재현](../../tmp/main-machine-remediation-research-20261012/depth-metadata-reproduction.json)은 fresh exact 0D 존재·count0을 확인했고, 올바른 route metadata를 붙인 합성 대조에서는 count1이다. 실제 과거 행을 수정하거나 성공으로 복원하지 않았다.

구현 설계:

1. 기존 normalized item/route resolver의 검증된 item·market route·suffix와 실제 transport/sequence/receive clock을 depth history ingress에서 함께 보존한다. FID 해석·source 시각은 변경하지 않는다.
2. exact snapshot materialization과 route partition에서 메타데이터를 유지하고, probe reader/분 partition/monitor validator까지 연결한다. snapshot의 최신 quote를 수신 이력 여러 건으로 복제하지 않는다.
3. 역사 행에 route가 없으면 unknown 상태와 원 증빙을 남긴다. 표시를 고치려고 route/receive timestamp를 소급 채우거나 validator의 실제 원천 요구를 제거하지 않는다.
4. KRX/NXT/SOR·다른 item/epoch·lease 전/후·stale/future·duplicate quote와 snapshot/deque materialization을 표적 회귀한다. source 미수신과 메타데이터 누락을 분리하고 source/quote hard guard는 동일해야 한다.
5. WS parser/normalized source 경계를 실제 수정하기 전 현행 공식 Kiwoom reference gate를 닫는다. 이번 요청의 계획·fixture는 기존 로컬 형식을 검토한 것이며 protocol 수정/배포 완료가 아니다.

### 4.2 수신 경로·quiet 점검

N2 receipt의 기존 clock/sequence를 사용한다. 같은 실패 lease의 REG 요청·ACK·interval/epoch·first 0B/0D·raw receive→callback→normalized publish→native ingest→Main read를 연결한다.

- `route_snapshot_missing`: 물리 미전송·ACK 불명·확인 구독 후 첫 패킷 없음·publish 누락을 구분한다. 다른 route의 값이나 global 연결 상태로 정상 처리하지 않는다.
- `0B_missing`: fresh 0D와 실제 0B 발생 증거를 구분한다. 체결 희소/미입증을 API 오류로 확정하지 않는다.
- `0B_age_exceeded`: provider clock·receive·callback·native read 지연과 실제 마지막 체결 시각을 비교한다. 새 0D나 REST 현재가로 0B의 시각을 갱신하지 않는다.
- 메모리 원 packet은 있는데 normalized/native가 뒤처진 경우에만 해당 parser/queue/lock 경로의 최소 수리를 제안한다. 현재 API·recovery budget/worker concurrency를 올리지 않는다.
- Kiwoom request/parser/FID·REG/REMOVE/recovery 수정에 들어가면 당시 현행 공식 reference revision·관련 upstream 경로·조회 시각을 기록한다. 현재 문서/로컬 연구는 wire 변경이 아니다.

종료는 source first-gap과 bounded recovery/reader 결속으로 판단한다. 실제 체결 없는 종목에서 0B 0건을 없애는 목표를 두지 않는다. 정상 quiet와 원천 불명은 정직하게 유지한다.

## 5. R3 — 늦은 유효 신호·로컬 후처리·PASS 소비

1. native lifecycle의 `first_eligible_seen/main_first_visit/claim`와 원 5초를 exact signal로 묶는다. warm loop 최대 6.081초나 claim 최대 3.046초가 같은 사건을 늦췄는지 확인하고 독립 집계의 숫자만으로 원인을 추정하지 않는다.
2. completion wakeup은 이미 구현됐다. 동기 scanner/account/보호 작업 중 깨어날 수 없는 구간, 정책/입력 freeze·mandatory append·lock 경합을 비중첩 stage로 대조한다. 보호·COMMIT 우선순위와 전체 대상 수를 유지한다.
3. 실제 새 local clocks에서 pre-provider, HTTP, response processing, annotation/cache를 나눈다. 일부 PASS 사례의 response processing 약 .52~.65초를 특정 원장 함수 비용으로 전부 배정하지 않는다. 필수 응답 검증/원장 저장을 drop하지 않고 확인된 중복 graph/copy/index 작업만 줄인다.
4. `trace_dedup_prepare:OSError`는 해당 준비 호출의 file/root/errno·회전/lock/부분 파일 상태부터 확인한다. provider 장애로 집계하거나 전체 연구를 차단하지 않는다. 기존 준비/cache owner가 최초 결손을 소유한다.
5. PASS worker→Main `commit_allowed`→`real_weak_pullback_entry_block`·`blocked_ai_score`·sizing contract 등 실제 다음 stage를 연결한다. CAUTION/미평가와 PASS를 섞지 않는다. 이후 정상 자금·수량·가격·운영 guard는 별도 연구/owner에 인계한다. PASS를 강제 제출하는 변경은 없다.

동일 frozen 입력의 baseline/candidate 교대3회와 fixed5+probe5·COMMIT/exit·source/필수 append 부하로 비교한다. 기존 NS5/R2b 지연 목표를 재사용하며, 빠른 결과가 작업 누락·source freshness 완화 때문에 얻어지면 실패다. 새 자연 표본과 code/배포/PID·손익 수용은 분리한다.

### 5.1 R4 — probe ENTER→Main 편입의 첫 실패 증빙

18:30까지 [9개 exact capture의 인계 대사](../../tmp/main-machine-remediation-research-20261012/probe-enter-main-handoff-trace.json)는 편입 2건, `attach_or_db_finalize_failed` 7건이다. 원 파일 2.6GB 전수 재생 대신 시각 기반 offset과 각각 16MiB 상한으로 약148MB를 읽고 동일 `machine_observation_sha256`를 대조했다. 시각 순서의 완전성을 가정하지 않고 실제 결속된 9건만 해석한다.

현재 `_zero_base_finalize_candidate_record`의 False에는 target 부재, 원 PROBE_READY DB 행/서명 불일치, native handoff 미유효, expected native claim 없음과 DB 예외가 포함된다. emit되는 `attach_or_db_finalize_failed`만으로 DB 장애라고 결론내리지 않는다.

1. 기존 boolean 실행 결과는 호환성을 유지하고, 같은 lock/시각에서 얻은 작은 실패 receipt를 원 capture/lease/record/PID/start에 붙인다. `accepted`와 `finalized`를 분리하고 record 상태·expected/native event·원 deadline/remaining·실제 확인한 실패 조건을 보존한다. 주문·계좌 비밀값을 기록하지 않는다.
2. 중간 `return False`가 원인을 남기도록 보완하고, 실제 DB 예외는 exception 종류/단계로 구분한다. 확인되지 않은 native 변경을 DB 오류로 표시하거나 모든 실패를 재시도로 바꾸지 않는다.
3. generic 종료의 실제 소비 projection에 PID/start·lease·request/capture/record와 receipt ref를 전달한다. 진단 저장 실패는 원 reject·단일 ACK/cleanup을 보존하며 신규 native claim·주문 권한을 갖지 않는다.
4. 편입됐던 2건의 Main live 재판정은 BLOCK/RECHECK 캡처와 원 신원으로 대조한다. probe ENTER를 Main ENTER/PASS로 강제 승계하지 않는다. 유효 expected claim이 저장/전달 중 유실되는 재현이 나오면 그 구현 결함만 수리한다.
5. target/DB 정상·누락·state/source signature 변경, 미실행/physical uncertain lease, native 변경·원 기한 만료, claim 원자 취득·commit 실패 뒤 ack, duplicate/late 결과와 다른 successor를 기존 attach/queue/async 회귀로 검사한다. 실제 통합 caller가 same-event·same-source·single claim으로 닫히는지 검증한다.

R4는 인계·원인 증빙 수리다. Main capacity·bot state·source/quote·quantity·operator veto를 바꾸거나 7건 모두를 놓친 상승/주문 실패로 선언하는 작업이 아니다.

## 6. H1~H6 — 미식별 패턴의 유한 수동 가설

이번 연구는 **PRE NXT `_NX`와 AFTER SOR `_AL`의 모든 보유 종목**이다. 9/29·30, 10/2·6·7의 기존 frozen normalized source/label cache를 재사용하며, 현재처럼 PRE/AFTER에서 과거에 등록한 하락 중심 조건 밖의 유형을 조사한다. REGULAR은 기존 연구와 별도의 후속 범위이며 이번 결과를 복사하지 않는다. 다른 시각/epoch·source gap의 가격으로 현재 무신호를 상승이라고 확정하지 않는다.

| ID | 고정 확인 방식 | 실제 확인 시점의 유형 조건 | 질문 |
|---|---|---|---|
| H1 | 60초 momentum 0.1% 전환 | 종목 흐름 UP, 낙폭<0.2%, VWAP 이상, spread≤0.1% | 하락이 선행되지 않은 상승지속 |
| H2 | momentum 0.05% 전환 뒤 1초 유지 | 흐름 NEUTRAL/UP, 수익률 .05~.2%, 낙폭<.4%, VWAP 이상 | 작은 낙폭·느린 상승 |
| H3 | 직전 60초 고점 돌파 | 수익률 0~.4%, 낙폭≤.2%, 고저 동반 상승, spread≤.1% | 낮은 낙폭의 고점 갱신 |
| H4 | 첫 반전 가격 1초 유지 | 흐름 NEUTRAL/UP, 수익률 −.2~.2%, 낙폭<.4%, VWAP 이상 | 얕은 눌림 확인 |
| H5 | 저점 재시험 후 FIRST 회복, 30초·허용 .2% | 흐름 NEUTRAL, 수익률 0~.2%, VWAP 이상 | 정상 재시험을 독립 새 확인점으로 다룰 효과 |
| H6 | 첫 반전 가격 3초 유지 | 흐름 DOWN, 수익률 0~.2%, VWAP 이상·BUY10≥60 | 짧은 FIRST 무효화 후 지속 확인·체결 방향 |

UP/NEUTRAL/DOWN은 **첫 유효 관측가 대비 해당 종목 흐름**이며 외부 지수 국면을 의미하지 않는다. 기존 연구의 경계 UP>.4%, DOWN<−.4%, 중립은 사이를 포함한다. 조건의 숫자·포함/제외는 실행 전 manifest로 고정한다. H1~H6 이외의 임의 grid·수백만 가설·장후 자동 새 패턴 생성을 실행하지 않는다.

### 모집단·비교·선택

1. `source_date>=2026-09-29`와 해당 exact item/venue/session만 입력한다. pre-9/29 cache/result는 역사 audit이며 학습/순위/선택에 합산하지 않는다. input/source/cache/code/현재 정책 hash를 freeze한다.
2. 이미 식별된 기존 등록 조건과 후보를 비교하려고 현재 적용 portfolio의 정확 branch payload로 동일 normalized prefix를 native State에서 재생한다. current baseline을 이전 연구의 `incumbent` 필드로 대체하지 않는다. 실시간 Main 가용성·실제 submit/AI를 가정하지 않는 detector 비교다.
3. 신호는 과거 received prefix만 소비한다. known FALSE→TRUE·hold, 연속 epoch/sequence와 실제 확인 ask를 유지한다. root에 미래 WIN/가격 최고값을 넣지 않는다. 양방향 체결 unknown은 SELL로 대체하지 않는다.
4. 실제 확인 ask부터 새 1,800초, 비용률 .0023·순 목표 +.4%·soft −3%의 native label을 사용한다. 미도달은 충분한 경로의 FAIL_TIMEOUT, 불완전 경로는 UNRESOLVED다. 10분 이후 기존 동일 item 가격/완성 분봉의 보조는 기존 native label 계약에 맞을 때만 사용한다.
5. 삼성·나머지 네 상시종목·일반종목 및 가격대·market/route cell을 구분한다. 동일 `(date,item,epoch,sequence)`의 복수 hit는 OR union에서 한 기회이며 branch membership은 보존한다. 반복 WIN 확인점과 독립 가격 에피소드/목표 시각 집중도를 따로 공개한다.
6. 1차 learning은 9/29·30·10/2, comparison은 10/6·7이다. learning에서만 cell당 H1~H6 우선 후보를 고정하고 뒤 날짜에 재평가한다. 단계2·3의 날짜/사후 탐색은 아래에 별도 명시한다. 최종 등록 제안은 고정 learning 후보의 누적 기존/후보/OR 승률과 추가 기회를 기준으로 정리한다. **특정 새 날짜에 추가 WIN이 있어야 한다는 조건은 두지 않는다.** 무신호·미확정은 실제 성과 악화와 분리하고 독립 미래 검증의 유무를 공개한다. 지정 초기 채택에 새 대기일/표본/EV gate를 추가하지 않는다.
7. baseline 단독, 후보 단독, baseline OR 후보, 추가된 W/STOP/TIMEOUT/U와 일자/종목 집중을 모두 보고한다. baseline 확정 분모가 없으면 승률 null·우위 미입증이다. 기존 성공 100%/80% 보존을 후보 탈락 조건으로 두지 않는다.

### 자원·중단·검증

- 새 API/Provider 호출·수집 확대·운영 registry 쓰기는 0이다. temp offline 역할 폴더만 사용한다. 한 프로세스/한 계산 thread, nice19, 2GiB address space 상한, CPU 480초·wall 600초 상한으로 기존 source를 순차 처리한다. 자원 충돌/예산 초과이면 partial 결과와 미평가 범위를 보존한다.
- 현재 적용 코드와 frozen 입력 해시가 바뀌면 혼합 세대로 순위를 만들지 않는다. 중복·NaN·unknown·경계·source reset·future prefix 불변·native baseline 라벨의 표적 검증을 한다. current native confirmation이 기존 cache에 없으면 정확 원천에서 다시 라벨링하고 임의 index 이웃으로 join하지 않는다.
- label cache의 immutable hash와 source reference를 확인한다. 과거 캐시의 당시 kernel/source와 현행 label 의미가 충돌하면 그 행/partition을 제외하고 불명 상태로 둔다.
- 유효한 후보가 나오면 등록에 필요한 정의·필수 history/hold·role·source/result/code/parent hash를 제안 자료로 남긴다. 후보 없음이면 확인한 6개 가설의 한계와 미확정/후속 scope를 남긴다. live 정책 선택/배포 완료나 실현 수익으로 선언하지 않는다.

### 단계2·3의 고정 후속 범위

1차는 6개 가설의 최초 learning/comparison 분할을 그대로 보존한다. 일부 상시 종목은 10/6~7에 표본이 생겼으므로 단계2는 learning을 9/29~10/7의 실제 5개 날짜로 넓히고 기존 10/8 NXT PRE/SOR AFTER의 frozen source를 추가 비교한다. H7=H2+volume≥1, H8=H2+BUY10≥60, H9=H4+BUY10≥60, H10=H4+volume≥1, H11=H5+BUY10≥60, H12=H1+volume≥1을 실행 전 고정한다. 현재 baseline source_date도 10/8이므로 이 비교를 보지 않은 독립 미래 holdout이라고 부르지 않는다.

단계2의 source-feature 적격성은 별도 집계한다. 원 root 확인점에 WIN 라벨이 있더라도 ret/structure/VWAP/qty·side가 unknown이면 그 조건의 패턴 match로 만들지 않는다. 0건 match를 전체 패턴 부재로 읽지 않는다.

단계3은 이 결손을 소급 채우는 대신 서로 다른 입력 계약의 가격 경로 가설 네 개를 고정한다: H13=RETEST_FIRST_WAIT30_TOL0.2+spread≤.1%+DD .2~.8%, H14=FIRST_HOLD1+spread≤.1%+DD .4~1.2%, H15=BREAKOUT60+spread≤.1%+DD≤.2%, H16=MOMENTUM_0.05_HOLD1+spread≤.1%+DD .2~.8%. 실제 root·quote·연속성 및 전략 공통 source/guard는 그대로며 선택적 연구 특징을 요구하지 않는 **신규 정의**다. 단계3은 10/8 결과를 본 뒤의 사후 탐색임을 표시하고, 독립 미래 검증/실운영 성과로 포장하지 않는다. 입력 수집/API/운영 정책은 변경하지 않는다.

## 7. 인계·리뷰와 이번 요청의 종료

R1~R4는 기존 `NonfixedDispatchReadinessReview1012`·`MachineAuxiliarySignalDeliveryRepair1012`의 새 결함 범위로 연결한다. 특히 R4는 기존 queue/native Main 인계의 동일 owner에 결속한다. 역사 완료 기록과 현재 sealed checklist는 유지한다. 실제 구현 착수 시 해당 stable owner의 현재 실행/Acceptance로 결속하고 별도 중복 cron/자동 정책 producer를 만들지 않는다.

문서/격리 연구 구현→self review→수정보완→재리뷰→표적 검증을 닫는다. 문서 link/owner/authority·print-only parser·diff와 수정 임시 Python compile/표적 pytest를 실행한다. runtime source 수정·배포·Provider 호출·주문은 이 요청의 결과에 포함하지 않는다.

완료 산출물은 최신 원천의 원인별 상세 보완계획, 현재 policy/native 비교에 결속된 H1~H16 결과·검증·등록 제안과 미선정 근거다. 18:30 예약 결과는 별도 실제 시각의 표본으로 저장하며 이 연구의 과거 비교 날짜나 frozen 가설을 다시 바꾸지 않는다.

## 8. 누적 연구의 등록 제안과 후속 구현 상세

[최종 누적 비교](../../tmp/main-machine-remediation-research-20261012/cumulative-registration-proposals.json)는 6개 날짜·12개 파티션·636,041개 가격 행, 16개의 고정 가설을 검토한 결과다. 과거 단계의 `comparison_not_improved`에는 그날 신호가 없었던 경우가 포함돼 있으므로 그대로 후보 탈락에 사용하지 않는다. 100%/80% 성공 보존 또는 새 날짜 추가 WIN 조건 없이 정리한 **연구 등록 제안 6개 / 적용 범위 4개**는 다음과 같다. 실제 submit·거래·독립 episode 수가 아니다.

| 범위 | 후보 | 기존 → 후보 추가 누적 승률 | 추가 W / FAIL / U | 추가 목표 시각 |
|---|---|---|---|---:|
| 알테오젠 PRE NXT·10만원 이상 | H9: 얕은 FIRST 1초 유지+BUY10≥60 | 394/473=83.30% → 404/483=83.64% | 10 / 0 / 118 | 2 |
| 일반 AFTER SOR·2만원 미만 | H6: DOWN 흐름의 FIRST 3초 유지 | 10/50=20.00% → 12/54=22.22% | 2 / 2 / 2 | 1 |
| 일반 PRE NXT·10만원 이상 | H3: 고점 돌파·고저 동반 상승 | 6/6=100% → 8/8=100% | 2 / 0 / 10 | 2 |
| 같은 PRE 고가 범위 | H14: 가격만으로 FIRST 1초 유지 | 6/6=100% → 8/8=100% | 2 / 0 / 0 | 1 |
| 일반 PRE NXT·2만원 미만 | H6: DOWN 흐름의 FIRST 3초 유지 | 155/229=67.69% → 156/230=67.83% | 1 / 0 / 0 | 1 |
| 같은 PRE 저가 범위 | H14: 가격만으로 FIRST 1초 유지 | 155/229=67.69% → 162/238=68.07% | 7 / 2 / 4 | 5 |

개별 추가 수를 더해 4개 scope portfolio의 기회 수/승률을 만들지 않는다. PRE 고가의 H3/H14, PRE 저가의 H6/H14는 같은 확인점/목표 경로가 겹칠 수 있어 실제 합집합을 다시 계산해야 한다. 같은 raw 경로에서 탐색한 사후 후보이며 독립 미래 검증·운영 경제성·성과 보장은 없다. 특히 알테오젠의 새 확인점 10건은 두 목표 시각에 집중되고 미확정 118건을 실패나 성공으로 보충하지 않았다.

삼성 PRE/AFTER에서는 이번 가설들의 추가 확정 WIN이 확인되지 않았다. 이는 해당 6개 날짜/두 시장의 정의·원천에 한정하며 REGULAR·전체 누적 데이터에서 상승 패턴이 없다는 결론이 아니다. 데이터 미확정을 0수익/실제 손실로 해석하지 않는다.

### 등록·선택·소비를 구체화하는 순서

1. R1 혼합 branch 관측 배정과 R2 depth metadata를 먼저 구현·리뷰·회귀한다. 기존 source/quote 검증과 현재 정책 결과를 유지하면서 정확한 원천·branch coverage가 확보되는지를 확인한다. 이는 새 정책의 경제적 승인 gate가 아니라 기존 생산/소비 결함 수리다.
2. H3의 BREAKOUT60은 기존 독립 고점 root와 정의/필터를 대조한다. H6/H9/H14의 FIRST_PRICE_HOLD 1/3초는 현재 runtime이 정확히 지원하는지 확인하고, 연구 root와 실제 native State의 parity를 먼저 닫는다. 지원되지 않는 root를 유사한 MOMENTUM/NEXT_UP으로 바꾸어 같은 정책이라고 발행하지 않는다.
3. hold root의 계약은 원 native FIRST anchor, 동일 연속 source/epoch, 확인 가격 이상 유지, 그 뒤 최초 실제 수신 확인점, 그 확인점의 actual ask와 새 1,800초 label이다. 원 anchor 뒤 가격 하회·source interval 종료는 무효다. 확인 가능한 구간/보유 상태의 상한과 pending cap·session 종료를 실제 지원 계약으로 명시한다. 연구와 다른 최대 대기시간을 넣으면 source-only 재계산으로 차이를 확인한다. 원 신호의 5초를 갱신하지 않고 별도의 실제 확인 event를 새 branch 신원으로 생성한다.
4. 필요 입력은 H3의 60초 return/구조, H6/H9의 60초 return/VWAP 및 실제 signed BUY10, H14의 가격 경로·DD/quote로 분리한다. 최소 history/hold descriptor에 원 definition hash를 결속하고 cold source에서 fast branch가 있다고 긴 입력 branch를 영구 단기로 보내지 않는다. 가격만 사용하는 후보도 공통 source/preflight/계좌/주문/수량/custody/hard guard를 건너뛰지 않는다.
5. 등록 자료는 English ASCII의 정책 ID·definition version/hash·scope/item·root/필터·필수 feature·label/source/code/result hash·parent bundle을 갖춘 `manual_research_registration` 제안으로 만든다. fixed catalog에 새 정의를 넣어야 하면 해당 successor registry/실행 code pin을 함께 준비한다. frozen v3/v4 정의와 현재 소비 중 bundle은 유지한다.
6. scope별 baseline, 후보 단독, 명시 OR 조합을 장후 등록 후보로 비교한다. 새 패턴 탐색은 수동연구만 소유한다. 기존 성공 100%/80% 보존·특정 새 날짜 WIN·일수/표본/EV의 추가 gate는 없다. source·현재 operator 지정·same-scope/native publish/loader 계약은 유지한다.
7. 동일 확인 tick의 여러 후보는 한 canonical opportunity, 한 보조 요청, 한 intent로 소비한다. 서로 다른 확인점의 후보도 기존 pending/outbox·현재 보유/cooldown/cap이 실행 권한을 소유한다. 자연 신호·보조 PASS·Main 소비·실제 주문·체결/손익은 각각 측정한다.

현재 산출물은 **등록 제안**이다. 운영 registry 수정·정책 선택/발행·배포·재기동·Provider 호출은 수행하지 않았다. 이 단계에 없던 경제성 입증이나 새 날짜 대기를 구현자가 추가하지 않도록, 지정 초기 채택과 일반 장후 비교의 기존 owner 계약을 유지한다.

## 9. 18:30 실제 점검과 이번 작업의 검증

[18:30 실제 snapshot](../../tmp/main-machine-status-20261012-1830/result/snapshot.json)은 `native-readiness-20261012-v2` / PID1215171·start4182334의 동일 신원을 확인했다. 재기동 이후 상시 Main ENTER_NOW122, 별도 probe ENTER_NOW9/BLOCK1, 비상시 Main BLOCK1/RECHECK1이다. worker PASS31·CAUTION15·VETO1·미평가/불명95, async 요청142이다. PASS/worker 완료를 Main 정상 제출로 합산하지 않는다.

비상시 종료838=source715+required_feature113+assessed10이다. source715의 사유는 route snapshot370·0B 없음182·0B age157·준비 경계0B age4·0D age 관련2이다. 113은 window 미완료72와 no-match 표시41이며 0D 계측 결함을 해결하기 전 no-match 전부를 정상 source coverage라고 선언하지 않는다. 초반 warmup·반복 lease 관측 비용과 source quiet/실제 경로 결손을 구분한다.

최신 warm loop4005회의 p95 .907초·p99 2.307초·최대6.081초·5초 초과1회는 첫 loop와 분리된 receipt다. 단일 최대 지연의 causal event를 R3에서 연결하며 지금 이 수치만으로 임의 함수 최적화나 source 한도 완화는 하지 않는다.

리뷰에서 새 날짜 추가 WIN을 후보 탈락 조건으로 사용하던 집계를 수정하고 valid-empty/미확정/실제 악화를 구분했다. [원 연구의 라벨·신원·상한 검증](../../tmp/main-machine-remediation-research-20261012/validation.json)은 표적 pytest13건, native family validator, 실제 라벨120개 재계산 불일치0, source/code hash·원천 적격성, 혼합 residence 및 0D 메타데이터 격리 재현을 포함한다. 최종 source/code/cache 해시35개 일치, 문서 로컬 링크29개·owner/authority·공백 검사, print-only parser19항목, 임시 Python compile와 `git diff --check`를 통과했다. sealed 당일 checklist SHA는 원 `2a0602f3a98bee1da4b6865cdd9f289ffb70a2628c134d0e981cf8a851a12609`로 유지됐다. 실운영 성능 benchmark·경제성/실현 PnL·새 정책 배포는 검증한 것으로 표시하지 않는다.

사용자 실행용 표준 동기화 명령:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
