# Main 430봉 공통 이력·분 단위 갱신·소비자별 WS 전환 구현계획 — 2026-10-08

**2026-10-08 후속 구현 상태:** PASS 소비·잔여 병목·430봉·비상시감시를 통합 구현하고 반복 리뷰·회귀를 수행했다. 10/8 구현 완료 때는 배포를 보류했으며, **10/9 후속 사용자 지시로 전체 미커밋 통합 배포가 승인됐다**. 현재 배포·준비 검증 상태는 [통합 배포 리뷰](../audits/main-integrated-uncommitted-deployment-review-2026-10-09.md)에서 확인한다. H4의 수정주가/WS 동등성 미입증 범위는 REST를 유지한다. [구현·검증·한계 기록](../audits/main-pass-residual-history-nonfixed-implementation-review-2026-10-08.md)을 현재 실행 결과로 사용하며 아래의 계획 작성 당시 승인·미실행 문구는 그 시점의 이력이다.

## 1. 목적과 실행 경계

430봉을 반복 조회하는 준비 경로를 **검증된 이력 복원 → 동일 원천 공유 → 새 완료봉 갱신 → 소비자별 WS 사용**으로 개선한다. 기존 판단에 필요한 이력·파생값·실시간 원천 조건을 보존하면서 수요당 REST 물리 전송과 신호 준비시간을 줄인다.

실행 owner는 [10/8 체크리스트](../checklists/2026-10-08-stage2-todo-checklist.md)의 `DirectFamilySourceRepairMainMechanisticEntry` 하나다. 사용자 후속 지시로 전체 병목을 다루는 [통합 개선계획](main-residual-capacity-budget-pass-history-bottleneck-implementation-plan-2026-10-08.md)을 우선 owner 문서로 두며, 이 문서는 그 R4 상세 명세다. H0~H5는 [B0~B7 계획](main-post-warmup-latency-rest-ws-bottleneck-remediation-implementation-plan-2026-10-08.md)의 B5 후속 단계이며 별도 전략·OPEN owner가 아니다. 현행 B5a의 짧은 cache/single-flight 구현은 보존하고 **새 완료봉 저장·소비 계약**을 추가한다. 이 문서는 계획이며 코드·설정·정책 발행·배포·재기동의 실행 영수증이 아니다.

Main-only, 기존 감시 대상·API 예산·원 claim의 5초 deadline·freshness·가격/수량/계좌/주문/custody/manual veto를 유지한다. 퇴역 위젯·에피소드 수집기나 worker를 복원하지 않는다. 분봉 수리에 경제적 입증·신규 AI 호출·정책 승률 조건을 추가하지 않는다. 기존 승인과 다른 세션 작업의 효력은 해당 owner에 남긴다.

## 2. 확인한 원인과 소비 범위

| 확인 사항 | 현재 코드 | 개선 시 지킬 구분 |
|---|---|---|
| 공통 요청 하한 430 | [MTF 상수](../../src/engine/scalping/multi_timeframe_context.py), [entry fetch](../../src/engine/scalping/entry_candle_context.py)의 `max(limit, SOURCE_BAR_LIMIT)` | 조회 행 수와 실제 판단에 필요한 완료봉 수를 구분한다. forming 행 포함 여부도 따로 센다. |
| 한 세션 WS와 구조적 불일치 | [selector](../../src/trading/market/shared_ws_snapshot.py)는 `ws_when_ready`에서 PRE 50 / REGULAR 390 / AFTER 240의 코드상 capacity를 넘으면 `requested_history_exceeds_projection_scope` | 이 수치는 현재 projection의 한계다. 시장 전체의 공식 거래시간이나 모든 소비자의 필수 이력으로 일반화하지 않는다. |
| MTF는 당일·해당 세션을 사용 | [normalize/derive](../../src/engine/scalping/market_context_observation.py)는 다른 날짜·세션을 제외하고 3/5/15분봉·세션 VWAP·5/15분 opening range를 생성 | 모든 MTF에 전일 430봉 prefix가 필요하다는 가정부터 바로잡는다. 장초에 아직 없는 20개 15분봉을 새 필수 조건으로 만들지 않는다. |
| 서로 다른 길이의 진입 특징 | entry context의 연속성은 최근 20분+경계 봉, breakout·low 등은 각 lookback, MTF 공개 배열은 구간별 최대 20개 | 특징별 실제 입력·quality·optional 상태를 조사한다. 전역 430→390/20 단순 치환은 하지 않는다. |
| 짧은 재사용은 이미 존재 | [ka10080 helper](../../src/utils/kiwoom_utils.py)는 route/limit/date/minute·인증 범위 key, 기본 5초 정규화 cache와 최대 3초 transport cache, single-flight를 사용 | TTL만 60초로 늘려 forming 봉과 원 수신 시각을 재사용하는 변경은 금지한다. 완료봉 view와 현재 가격/tape/호가는 별도 계약이다. |
| REST와 WS 가격 기준 차이 | REST `adjusted_1`, [공유 완료봉 writer](../../src/engine/scalping/micro_reversion/completed_bars.py) `raw_same_day` | 동일성 입증 전 합치거나 같은 API 출처로 표시하지 않는다. |
| WS 범위 제한 | 현재 `completed_bar_mode`의 WS 대상은 지정 5종목의 `_AL`; `_NX`와 일반 probe는 REST 경로 | PRE는 `_NX`/NXT, REGULAR·통합 AFTER는 `_AL`/SOR를 유지한다. 캐시 공유가 WS 구독·시장 범위 확대 권한은 아니다. |

[19:30 관측](../audits/main-latest-release-post-warmup-rest-ws-monitoring-2026-10-08-1930.md)의 주 창은 워밍업 제외 19:05:06~19:29:19다. 물리 전송 1,849회 중 `ka10080`은 source-only probe 73회·runtime-required 14회다. `kt00011` 사전 조회 1,403회(75.88%)와 PASS 전달 지연은 별도 병목이다. 본 개선만으로 전체 REST·제출 지연이 해결된다고 선언하지 않는다.

## 3. 원천과 소비 계약

### 3.1 공유 저장과 소비 영수증

공유 단위는 동일 종목의 이름만이 아니라 `실/모의 환경·인증 범위 + exact request item/suffix + 시장 원천 route + 거래일/세션 + 1분 interval + adjustment/version + timestamp 의미`다. 인증 정보 원문은 저장하지 않는다. `_NX`와 `_AL`, venue-only와 통합봉을 섞지 않는다. REGULAR/AFTER의 같은 `_AL`도 세션 구획과 실제 row 시각을 보존한다.

저장 manifest는 schema/revision, 원 REST 응답/WS journal의 hash·위치·수신 시각, bar open/close·available-at, 최초/최종 완료봉·coverage·결손 구간, adjustment 근거, segment별 producer/transport epoch, 내용 hash를 가진다. 저장 위치는 `data/runtime` 아래 별도 Main 공통 이력 namespace로 정하고 기존 session seed를 덮지 않는다. 원 증빙은 참조하고 큰 raw journal을 consumer마다 복제하지 않는다.

소비 영수증은 `attempt/consumer/schema/feature version + required window/session anchor + requested completed cutoff + selected revision/hash + source method + original observed_at + selected_at + remaining deadline`을 가진다. 같은 봉 데이터는 공유하되 provider/주문 권한·계좌 용량 결과·서로 다른 원 claim은 공유하지 않는다. `selected_at`이나 cache hit가 원천 freshness를 갱신하지 않는다.

**저장 데이터 key와 진행 중 HTTP 병합 key는 구분한다.** 검증된 완료 데이터는 요청 class가 달라도 각각의 consumer 계약을 만족하면 읽을 수 있다. 진행 중 요청은 기존 request class/우선순위·admission 권한·timeout/continuation bound·deadline이 호환되는 경우에만 join한다. 저우선 source-only leader에 runtime-required 소비자를 무제한 묶거나 source-only를 필수 계좌 예산으로 승격하지 않는다. “leader 하나”의 범위는 이 호환 admission 구역이며, 정책상 분리된 물리 전송은 숨기지 않는다.

새 완료봉 존재는 wall clock의 분 경계만으로 확정하지 않는다. provider 또는 WS의 완료·가용 watermark와 실제 coverage를 확인한다. 갱신되지 않은 prefix를 새로운 cutoff를 만족하는 자료처럼 반환하지 않는다. 저장봉 수정이 발견되면 revision을 바꾸고 해당 봉에 의존한 파생 cache를 무효화한다. 이미 남긴 판정 영수증은 원 revision에 고정한다.

독자는 평가 입력을 고정한 `as_of`와 원 revision으로 view를 pin한다. 나중에 도착한 봉·정정은 같은 bar timestamp여도 이전 판정에 소급 삽입하지 않는다. 이력 backfill의 관측/가용 시각과 가격이 발생한 시각을 분리하며, live refresh가 필요하면 기존 허용 경로에서 새 입력 snapshot으로 기록하고 원 claim deadline은 유지한다. 재생 검증도 당시 사용 가능했던 revision을 선택한다.

### 3.2 이력·현재 관측 분리

- **완료봉 이력:** 반복 사용 가능한 OHLCV와 검증된 구간. 원 관측 시각·coverage·수정 여부가 계약이다.
- **forming 봉:** 완료봉 저장에 포함하지 않는다. 기존 consumer가 필요로 하면 유효한 현재 REST/정확한 WS 관측으로 별도 view를 만들고 `forming/partial_volume`을 보존한다. 해당 자료를 확보하지 못하면 기존 bounded REST 또는 원천 미충족 처리로 간다. 오래된 forming 봉은 재사용하지 않는다.
- **실시간 가격·tape·호가:** 기존 fresh source와 route/epoch 검증을 그대로 통과해야 한다. 완료봉이 충분해도 stale 실시간 원천을 승인하지 않는다.
- **세션 누적 특징:** VWAP·opening range에 필요한 세션 시작 자료를 유지한다. rolling 430개만 남겨 시작 부분을 버리지 않는다. 압축 집계가 필요하면 분자/분모·bar 기반 계산법·원 revision·수정 시 재계산 경로까지 보존한다.

REST의 기존 bounded sparse-minute 해석과 WS의 관측 결손은 다른 계약이다. REST가 `ka10080`이라는 이유로 적용하는 최대 3분 gap 해석을 합성 WS 자료에 자동 승계하지 않는다. 휴장·세션 간격·입증된 무체결·미수신을 구분하고 관측하지 못한 분에 OHLC/volume=0을 만들지 않는다.

## 4. 단계별 구현

| 단계 | 작업 | 완료 증거 |
|---|---|---|
| H0 소비 목록 확정 | entry/probe/MTF 및 같은 helper를 쓰는 생존 holding consumer를 찾아 원 row→필터→필수 특징을 추적한다. 원 요청 수·forming·타 세션 제외 수·최종 소비 수를 분리한다. 지수 분봉은 별도 source owner로 둔다. | consumer별 `required/optional`, lookback, session anchor, 완료 cutoff, 부족 시 기존 동작 표. 430 raw row를 430 완료봉 새 gate로 바꾸지 않았다는 검토. |
| H1 동일 REST 이력 공유·복원 | 현재 `adjusted_1` 원천을 불변 revision으로 저장한다. 기존 worker에서 읽고 동일 데이터 요청을 병합한다. 현재 430 응답 adapter와 짧은 TTL 경로를 먼저 유지한다. | 기존 응답/파생값 parity, 서로 다른 요청 범위의 오염 0, 재기동 복원·손상 격리. 이 단계만으로 종일 재사용을 열지 않는다. |
| H2 완료 분 단위 증분 갱신 | 새 완료 cutoff 또는 correction/gap/adjustment invalidation에 대해서만 갱신한다. 과거 구간을 유지하고 검증된 겹침 구간과 새 봉을 merge한다. 완료봉 재사용과 fresh forming 조립을 별도 reader로 연결한다. | 같은 cutoff/revision의 준비된 완료봉 반복 수요는 추가 HTTP 0; 호환 admission 구역에서 한 논리 갱신으로 동시 수요 충족. forming·정정·우선순위 분리의 추가 전송은 별도 집계. |
| H3 실제 필요 이력 계약 적용 | H0에서 확인한 consumer descriptor를 selector에 연결한다. 해당 세션만 쓰는 소비자는 유효한 세션 coverage와 필요한 특징으로 준비 여부를 결정한다. 실제 교차 세션 이력이 필요한 소비자는 명시적인 prefix를 요청한다. | 동일 입력·시각·현 정책에서 필수 파생값과 기계 결과 parity. optional 부족을 신규 veto로 바꾸지 않음. 전역 상수만 줄이는 변경 없음. |
| H4 WS 완료봉 연결 | H3 계약과 가격/거래량 동등성을 모두 만족하는 현재 지원 `_AL` 구간부터 shared writer의 완료봉을 소비한다. 실제 prefix가 필요한 경우에만 검증된 REST prefix+WS tail view를 만든다. | overlap·경계·revision·source label 검증, 실제 reader 선택 영수증과 HTTP 회피. `_NX` 및 미지원 범위는 동일 REST 공유 경로 유지. |
| H5 통합 검증·인계 | 아래 회귀·제한된 replay·실제 launch 환경의 reader/code pin을 검증한다. 정책 목록·보조 binding·출처 계약 호환을 보존하는 기존 handoff로 인계한다. | 코드 검증/배포/PID/자연 성능을 별도 보고. 새 경제성 gate 없이 원천·소비 동등성으로 수리를 판단. |

H1/H2는 WS 합성 미지원과 독립하여 구현할 수 있다. H3는 완료된 B5a를 재실행하는 단계가 아니라 공통 430 요청과 실제 필요 window를 분리하는 변경이다. H4에서 raw/adjusted 의미가 미해결이면 해당 전환만 유지 보류하고 REST 절감 결과는 별도로 수용한다.

### 4.1 갱신 주기와 요청량

1. 최초 수요 시 같은 route/adjustment의 보존 이력을 복원하고 부족한 구간만 확보한다. 초기 확보는 하나의 논리 작업이며 continuation 때문에 물리 HTTP가 여러 번일 수 있다.
2. 같은 완료 cutoff 안에서는 immutable revision을 공유한다. 새 cutoff의 호환 수요가 생기면 한 갱신 leader를 두고 나머지는 각자의 원 deadline 안에서 기다린다. follower가 만료돼도 leader의 원 budget 안에서 다른 유효 수요를 충족할 수 있으나, follower가 leader의 timeout을 연장하거나 만료 claim이 평가·provider·주문으로 진행하지 않는다. 새 정정 revision은 같은 cutoff라도 새 검증 대상이다.
3. 5종목을 매분 무조건 사전 조회하는 scheduler를 만들지 않는다. 우선 기존 실제 수요와 existing prepare worker를 사용한다. 무신호 조회 증가, queue 적체, 계좌·주문용 예산 침범을 별도 계측한다. 새 daemon/cron은 만들지 않는다.
4. 최신 몇 개 봉만 요청하는 공식 API 인자가 있다고 가정하지 않는다. 현재 helper는 page size를 900으로 계산하며 `limit`은 호출 제한·로컬 slicing에도 쓰인다. 공식 API가 증분 범위를 지원하지 않으면 정상 첫 페이지와 필요한 continuation을 받아 로컬에서 중복 제거한다. **횟수 감소·응답 byte 감소·저장량 감소를 따로 측정**한다.
5. response empty/error/deferred/partial/continuation 결손은 완성 cache로 승격하지 않는다. 기존 budget 내 backoff와 coalescing으로 재시도 폭주를 막고 실패는 결손으로 기록한다. 새 완료봉 가용 전 1분 대기로 신호의 5초 예산을 소진하지 않는다.
6. 늦은 bar 수정은 증분 응답의 overlap 비교로 발견한다. overlap 밖 수정·일자/수정주가 변경은 검증된 revision 근거 또는 bounded 재대사로 감지한다. 구현 H0에서 공식 정정 의미와 저장 표본으로 재대사 대상·주기를 수치화하며, 원천 계약이 미정인 상태에서 종일 불변을 가정해 재사용하지 않는다. 추가 재대사도 같은 API 예산과 physical 분모에 포함한다.

fresh forming 봉이 실제 필수이고 현재 WS로 공급되지 않는 consumer는 기존 유효 REST 조회가 계속 필요할 수 있다. 완료봉 cache hit를 해당 호출 전체의 HTTP 회피로 보고하지 않는다. H0에서 `완료봉만 필요 / forming 필요 / session anchor 필요`를 구분하고, 다른 종목·세션의 forming으로 대체하거나 forming 필수값을 제거해 절감 목표를 맞추지 않는다.

### 4.2 경쟁·복구·디스크

한 source key의 writer/refresh owner를 하나로 두고 기존 cross-process 조정 방식을 재사용한다. revision CAS와 원자 교체로 늦게 온 REST 응답이 최신 WS/REST revision을 덮지 못하게 한다. 독자는 한 revision을 고정해 읽으며 읽는 도중 파일 교체·truncate·hash 불일치는 해당 snapshot만 무효로 처리한다. 디스크 I/O·전체 history hash·HTTP를 Main loop/WS callback lock 안에서 수행하지 않는다.

재기동 시 manifest와 source hash를 검증한다. 폐기된 PID의 생존 여부를 역사 완료봉의 유효 조건으로 요구하지 않되, 현재 WS tail은 현재 producer/transport epoch와 연결 상태를 반드시 검증한다. reconnect의 첫 tick으로 빈 구간 전체를 덮어 정상 처리하지 않는다. 시계 역행·새 거래일·route/adjustment 변경·수정 봉은 새 revision/필요 구간 복구로 처리한다.

manifest 경로는 실제 선택 release의 canonical data root를 기준으로 해석한다. launch cwd가 `release/src`여도 같은 source를 읽어야 한다. raw 절대경로를 다른 release로 치환해 출처를 바꾸지 않으며, 허용된 공통 data 경로의 symlink·동시 교체·schema 호환을 검증한다. 새 reader는 구 manifest를 검증 가능한 범위에서만 읽고 구 reader가 새 composition을 homogeneous REST로 오인하지 못하게 한다.

메모리·디스크는 실제 consumer가 요구하는 rolling 구간과 세션 누적 상태를 기준으로 상한을 둔다. 활성 manifest·진행 중 reader·보존 대상 판정 영수증이 참조하는 revision은 유지한다. 기존 raw 원천은 이번 개선의 삭제 대상이 아니며 reference 없는 파생 cache만 검증 후 회수한다. consumer마다 430봉 전체 파일을 중복 저장하지 않는다.

## 5. 코드 위치와 공식 원천 검증

| 책임 | 기존 소유 위치 / 예정 변경 |
|---|---|
| 데이터 저장·revision·공유 source view | `src/trading/market/` 소유. 새 모듈이 필요하면 이 package에서 기존 snapshot helper와 경계를 정한다. `src/engine` root에 만들지 않는다. |
| 요청·완료봉 선택·forming/route binding | [entry_candle_context.py](../../src/engine/scalping/entry_candle_context.py), [shared_ws_snapshot.py](../../src/trading/market/shared_ws_snapshot.py) |
| 정확한 소비 window·파생 cache | [multi_timeframe_context.py](../../src/engine/scalping/multi_timeframe_context.py), [market_context_observation.py](../../src/engine/scalping/market_context_observation.py), [zero_base_probe.py](../../src/engine/scalping/zero_base_probe.py) |
| 원 REST 요청·연속조회·계수 | [kiwoom_utils.py](../../src/utils/kiwoom_utils.py), 기존 transport telemetry/read coordinator |
| WS 완료봉 생산 | [completed_bars.py](../../src/engine/scalping/micro_reversion/completed_bars.py)의 생존 Main 공유 writer. package 이름을 근거로 퇴역 runtime을 복원하지 않는다. |
| async 준비와 결과 소비 | [sniper_state_handlers.py](../../src/engine/sniper_state_handlers.py)의 기존 worker/claim/단일 Main commit. 별도 신호·주문 owner를 만들지 않는다. |

요청·parser·FID·continuation·recovery를 변경하기 **전에** [Kiwoom 공식 gate](../kiwoom-api-data-contract.md)의 절차로 공식 저장소 최신 revision을 확인한다. upstream SHA·조회 KST·`kiwoom_docs`의 ka10080/0B 관련 경로 및 SDK/core/realtime/Postman 대조 경로를 구현 리뷰에 남긴다. 현재 계획은 upstream 의미를 새로 검증했다는 주장이 아니다.

특히 봉 timestamp가 시작/종료 중 무엇인지, adjusted price와 raw tick의 비교 가능 조건, 거래량 부호/누적량과 분별량, `_NX`/`_AL` item 의미, 연속조회·정정·무체결 의미를 확인한다. 미정이면 해당 WS 합성/종일 재사용 범위만 계약 미지원으로 유지한다. PRE `_NX`를 `_AL`로 변환하거나 `api_id=ka10080`을 WS 합성 자료에 붙여 parser 허용을 얻지 않는다.

## 6. 검증과 수용 기준

### 6.0 REST 복귀와 원천 거절의 구분

현 `selected_completed_bar_payload`는 정상적인 이력 미충족은 REST로 돌리지만 live binding 등 의미/무결성 오류는 예외로 거절한다. 새 reader가 모든 오류를 `None`으로 바꿔 REST를 조회하는 방식으로 이 경계를 완화하지 않는다.

| 상태 | 처리 |
|---|---|
| 현재 계약의 정상 미지원·이력 부족·아직 없는 projection | 허용된 same-route homogeneous REST 경로를 원 예산 안에서 사용 |
| 만료/없는 파생 cache | 검증된 원본으로 재생성하거나 기존 bounded REST; 원 source identity를 새로 입증 |
| live item/route/epoch 충돌·권위 있는 source hash 변조·producer 신원 무효 | 현재 attempt의 source gate 거절과 실제 사유 유지. REST 응답 존재만으로 source identity 오류를 지우지 않음 |
| raw/adjusted 의미 동등성 미입증 | 해당 composition 선택을 열지 않고 원래 검증된 source 계약 사용. conflict를 동등성 PASS로 바꾸지 않음 |
| deadline 소진·우선순위/admission 불가 | 추가 전송 없이 해당 준비 상태 종료; stale cache 반환·quota 추가 없음 |

기존 미지원/무결성 거절별 fixture에 새 reader를 통과시켜 fallback 범위가 넓어지지 않았는지 확인한다.

### 6.1 표적 회귀

기존 [entry 테스트](../../src/tests/test_entry_candle_context.py), [REST/WS 지연 테스트](../../src/tests/test_main_rest_ws_latency.py), [MTF 테스트](../../src/tests/test_multi_timeframe_context.py), [시장 특징 테스트](../../src/tests/test_market_context_observation.py), [완료봉 테스트](../../src/tests/test_micro_reversion_completed_bars.py), [Kiwoom 원천 계약 테스트](../../src/tests/test_kiwoom_market_data_contract.py)를 영향 범위로 확장한다. 새 저장소 테스트가 필요하면 `src/tests/`에 둔다.

- 같은 cutoff의 반복/동시·다른 limit·다른 request class 요청: 허용된 데이터 공유, 원 우선순위·deadline 보존, 물리 page/retry 중복 없음. source-only 작업이 runtime-required 예산을 대신 소비하지 않는다.
- 새 분 경계·forming 포함 430행/완료 429행·장초 부족·PRE/REGULAR/AFTER 전환·타 날짜 필터: 기존 required/optional 동작 보존, 미래 봉 0.
- 세션 VWAP/OR·3/5/15분봉·최근 연속성·breakout 등의 실제 필요 구간, 430개를 넘어선 세션 시작 자료, 분모/반올림: 값·quality·missing reason parity.
- `_NX`/`_AL` 및 실/모의/인증 범위 격리, REST 수정주가와 WS raw 불일치, sparse 무체결/누락 구분, 중복 timestamp 값 충돌: 잘못된 재사용 0.
- provider 오류·빈 응답·불완전 continuation·clock rollback·refresh timeout·만료 follower·재접속 gap·뒤늦은 수정·CAS 경합·손상 manifest·죽은 이전 PID: false fresh/완성 승격 0, bounded 복구.
- active reader가 잡은 revision의 수명·증빙 참조·원자 교체·메모리/디스크 상한·프로세스 재기동: 미완성 view 노출 0, 무제한 누적 0.
- 저장 데이터 공유와 source-only/runtime-required inflight 분리·leader/follower별 deadline·release/src cwd·미래 가용 정정·source binding 오류: 예산 승격/연장 0, 과거 판정 소급 변경 0, 무결성 거절의 REST 우회 0.

기존 저장 원천의 같은 시각·같은 정책으로 제한된 replay를 수행한다. 외부 provider 재호출 없이 bar/필수 파생값·기계 결과와 보조 입력의 의미를 비교한다. source metadata의 의도된 schema 차이는 목록화하고 값 차이·quality 변화와 분리한다. 수리로 결손이 해소된 사례는 기존 유효 입력의 parity 분모와 분리해 보고한다.

### 6.2 성능·운영 결과

| 지표 | 수용/보고 기준 |
|---|---|
| 동일 입력 동등성 | 유효 비교 가능한 필수 OHLCV/파생값/기계 결과 불일치 0; 의도된 provenance 변경만 별도 표시 |
| 정확한 재사용 | 동일 key/cutoff/revision의 준비된 반복 수요에 추가 HTTP 0. 미준비·정정·forming fallback은 이유와 횟수 분리 |
| 신규 갱신 | 호환 admission 구역의 같은 key/cutoff/revision에 정상 leader 하나. 실제 page/retry·forming·우선순위 분리·fallback/재대사·defer를 모두 physical 분모에 포함 |
| 자연 호출 효과 | release/PID·워밍업 제외 창·종목/session·수요수를 고정해 physical attempts/logical demand, bytes, hit/miss, 갱신 수 비교. 수요 축소를 절감으로 세지 않음 |
| 준비 지연 | candle 준비 및 전체 signal→prepare p50/p95/p99·원 5초 내 완료율. loop·WS lock·계좌 요청 대기 악화 여부를 함께 보고 |
| 안전·결손 | stale/미래/혼합 route/변조된 provenance 수용 0; 새 원천결손과 지원되지 않는 scope를 분리 |
| 자원 | writer queue·cache 크기·동시 reader·disk write/retained bytes를 계측하고 설정한 상한 준수 |

이 지표의 역할은 `source_quality_gate` 또는 성능 진단이며 주문/전략 선택 권한은 없다. 비교 가능한 수요가 없으면 미관측으로 남기고 새 최소 거래·수익 gate를 만들지 않는다. API 제한 확대나 감시 범위 축소는 절감 수단에 포함하지 않는다.

## 7. 적용·복구 인계

구현→자체 리뷰→결함 보완→재리뷰→표적 pytest/compile/`git diff --check`를 완료한 뒤 기존 승인 범위의 handoff로 진행한다. 영향을 받는 policy code pin·source schema·보조 input reader·실제 launch cwd를 검사하고 필요한 호환 산출물만 생성한다. 완료된 연구·전체 장후 보고서를 재생성하지 않는다.

배포 후에는 selected release, 실제 PID의 reader/source version, 준비된 정책, 자연 cache/WS 선택, 성능을 따로 증빙한다. 신규 view의 정상 미지원/이력 부족은 §6.0에서 허용한 bounded homogeneous REST 경로로 복귀한다. live identity·무결성 충돌은 해당 attempt를 거절하고 유효 원천이 복구되기 전 REST로 우회하지 않는다. stale 자료나 원 deadline을 늘려 복구하지 않는다. 퇴역 consumer를 포함한 과거 release로 회귀하지 않는다.

이번 문서 작업은 기존 OPEN owner의 B0~B7 문서에서 연결하며 봉인된 체크리스트 바이트·AUTO 블록은 변경하지 않는다. 후속 실제 실행 일정/Acceptance 인계로 체크리스트를 변경할 경우 최종 바이트에 대한 strict/필요한 다음 PREOPEN 준비는 기존 owner가 검증한다. 이전 PASS를 현재 세대의 PASS로 표시하지 않는다.

## 8. 계획 리뷰에서 보완한 사항

1. 430을 모든 정책의 실질 필수 완료봉 수로 오인하지 않도록 raw/완료/최종 소비 수와 당일·세션 필터를 명시했다.
2. 기존 짧은 TTL 개선과 새 이력 계약을 구분하고 forming 봉·실시간 freshness를 분리했다.
3. WS 없이 먼저 가능한 동일 REST 공유를 선행 단계로 두고, 실제 필요한 prefix만 합성하도록 했다.
4. PRE `_NX`의 현재 WS 미지원, 수정주가/거래량·sparse gap 해석 차이를 명시했다.
5. 증분 조회의 공식 지원을 가정하지 않고 continuation·correction·실제 물리 전송을 포함했다.
6. 세션 집계 유실·수정·재기동·오래된 PID·동시 갱신·증빙 보존·수요 없는 사전 조회 증가를 검증 항목으로 추가했다.
7. 재리뷰에서 데이터 key와 inflight 우선순위를 구분하고, caller 예산 연장·미래 revision 소비·forming 조회의 절감 오인·무결성 오류의 REST 우회를 방지했다. 실제 launch cwd와 schema 호환도 추가했다.

잔여 구현 조사 항목은 H0의 소비 목록 및 공식 정정 의미/재대사 주기 확정이다. 이는 계획 완료와 구분하며, 구현 시 원천 계약을 확인한 뒤 수치와 테스트를 고정한다.

## 9. H0~H5 구현·원천 경계

H0/H3 descriptor는 세션 anchor·완료 cutoff·최근 61분/MTF(3·5·15분 각 최대20개)의 실제 수요를 명시하고 430 raw 요청을 새 430 완료봉 진입조건으로 만들지 않는다. H1/H2는 날짜별 SQLite에서 OHLCV를 내용 해시로 중복 제거하고 불변 revision과 별도 forming 영수증을 저장한다. 짧은 갱신은 이전 prefix와 검증된 새 overlap을 결합하며 overlap 안의 결손을 합성하지 않는다. 수정 시 이전 revision을 보존한다. H4는 raw_same_day와 adjusted_1의 동등성 미입증으로 자동 전환을 유보하고 기존 REST를 선택한다. H5의 운영 HTTP 절감/자연 소비는 미관측이다.

검증 수치·수정한 반례·공식 API SHA·배포 보류 경계는 [통합 실행 리뷰](../audits/main-pass-residual-history-nonfixed-implementation-review-2026-10-08.md)에 한 번 기록한다. 실행 owner는 기존 `DirectFamilySourceRepairMainMechanisticEntry`를 유지하며 이번 작업은 checklist 봉인/현행 정책을 재발행하지 않는다.
