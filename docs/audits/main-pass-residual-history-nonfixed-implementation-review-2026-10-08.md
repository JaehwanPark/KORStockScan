# Main PASS 소비·잔여 병목·430봉·비상시감시 통합 구현 리뷰

2026-10-08 KST. 사용자 승인 범위는 네 계획의 구현·반복 리뷰·수정보완이다. **이번 작업의 배포·재기동은 별도 지시까지 보류한다.** 코드 검증은 실제 PID 소비·장중 지연 개선·주문 성공의 증거가 아니다.

## 1. 범위와 실행 경계

소유 문서는 [통합 R0~R5](../proposals/main-residual-capacity-budget-pass-history-bottleneck-implementation-plan-2026-10-08.md), [PASS PB0~PB4](../proposals/main-post-warmup-latency-rest-ws-bottleneck-remediation-implementation-plan-2026-10-08.md), [430봉 H0~H5](../proposals/main-430-bar-shared-history-and-incremental-refresh-implementation-plan-2026-10-08.md), [비상시감시 NS0~NS5](../proposals/main-nonfixed-native-signal-observation-and-consumption-remediation-plan-2026-10-08.md)다. 현행 OPEN owner는 `DirectFamilySourceRepairMainMechanisticEntry` 하나를 재사용한다.

새 모듈은 기존 역할에 맞춰 `src/engine/scalping/trace_dedup.py`, `src/trading/market/completed_history.py`, 회귀는 `src/tests/test_main_integrated_bottlenecks.py`에 둔다. engine root에 새 Python 모듈을 만들지 않았다. 기존 미커밋 문서 및 별도 장후 복구 작업의 변경은 보존했다.

원 native 5초와 epoch/perf 양쪽 만료, provider 중복/불확실 예약, 최종 quote/주문/계좌/수량/cooldown/manual veto는 유지했다. 기계 패턴·보조 프롬프트·정책 목록·승률 조건을 바꾸지 않았다. 퇴역 episode/widget를 재개하지 않는다. 실제 API/AI 호출, 운영 원장 삭제·복제, EOD/장후 재실행, 정책 발행, selector/env/systemd 변경은 이번 작업에서 수행하지 않았다.

## 2. 생산자에서 소비자까지의 변경

| 범위 | 구현과 소비 경로 | 남은 운영 확인 |
|---|---|---|
| R1 용량 준비 | 무신호 `waiting_native_signal`/미지원 `not_enabled`의 예약 제거. 유효 `ScannerAsyncEvalContext`의 request/generation/state/원 deadline으로 예약을 제한. 가격 변경은 동일 수요 안에서만 결합. `kt00011`의 `source_only/entry_capacity_prefetch`와 ENTER 경제성 observer도 원 budget을 전달. BLOCK/RECHECK는 reuse-only | 실제 claim 수와 필수 sizing 계좌 조회를 분리한 물리 요청량 |
| R2a/PB1 완료 소비 | coordinator의 원 ID 보존 → 완료 wakeup → Main 공통 WATCHING 소비 → 기존 실행/최종 guard. 신규 분석 cooldown/준비보다 먼저 완료 결과를 꺼냄. 종료·거절 뒤 같은 결과 재검증 없음 | 배포 후 exact PASS의 Main 소비율 및 실제 intent/submit |
| R3/PB2 원장 | 기존 준비 worker에서 최대 4MiB chunk로 6종 dedup index 준비. hot path는 준비 index와 최대 64KiB append suffix만 검증. inode/축소/mtime/인접 prefix fingerprint/불완전 행/ID 내용 충돌 검증. append·fsync 및 원문 보존 | 재기동/자정의 준비 완료 시간과 실제 lock/fsync 분포 |
| PB3 영수증 | 기존 `entry_async_disposition` pipeline → lossless compact → Sentinel slim cache → monitor. PID/start/request별 worker 완료와 accepted/rejected/terminal을 연결. 동일 event 중복 및 충돌 처리. writer 실패는 기존 bounded health counter에 남김 | 전체 raw PASS 모집단의 가용 범위, accepted 뒤 제출 guard 결과 |
| H0~H3 이력 | entry/probe/MTF의 세션 anchor·최근 연속 구간·MTF descriptor → 공통 ka10080 helper → 날짜별 SQLite. 완료 OHLCV 내용 해시와 불변 revision, 별도 forming receipt. 첫 REST 소비부터 원 revision pin. 작은 갱신은 이전 prefix를 보존하고 반환 overlap의 정정을 반영 | 운영에서 동일 cutoff 재사용과 fresh forming 때문에 필요한 추가 HTTP를 따로 계수 |
| H4 WS 선택 | 현재 `raw_same_day` writer와 `adjusted_1` REST의 가격 의미가 미입증이면 `price_basis_equivalence_unproven`으로 REST 유지. strict WS 모드는 원천 미충족을 명시 | 동등성 근거 없이는 자동 합성/전환하지 않음 |
| NS1~NS3 관측·인계 | 5 physical lease 이내, 장기 2개 최대150초/나머지60초. 같은 interval 재관측 시 시작점을 갱신하지 않음. native 비소비 peek → 원 event/branch subset 대조 → Main DB 입장 검증 후 claim. panel REST는 기존 제어 thread와 분리, Main inbox는 5개/회당2개 소비. 저장 실패 재시도에도 원 5초 유지 | 실제 ready→Main claim 지연, 원천 충족/자원 만료 분포 |
| NS 종료 | 결과 terminal과 physical cleanup 분리. RESULT 뒤 CLOSED 순서. REMOVE 미확인 시 슬롯 유지, 기존 준비 worker가 동일 lease 정리를 재시도. 최종 owner가 떠난 interval의 B/R state를 함께 무효화 | 자연 REMOVE/재연결·Main adoption 후 잔여 구독 확인 |
| NS4 진단 | lock/clock이 같은 observation receipt에 branch TRUE/FALSE/UNKNOWN·원 시각/epoch/sequence·선택 scope 기록. 기존 raw-ready는 유지하고 confirmation 가격대/backend/generation에 맞는 selected-ready 별도 집계 | process ingress 관측 밖의 기회를 전체 모집단으로 추정하지 않음 |

현재 `async_disposition_coverage`는 이미 읽은 증거의 PID/start별 집계다. 전체 원장을 추가 스캔하지 않으며 `coverage=loaded_evidence_only_full_denominator_unobservable`을 명시한다. terminal 없는 만료를 rejected로 합성하지 않는다. accepted는 Main 소비이고 broker 제출·체결은 기존 주문 원장으로 확인한다. 별도 heartbeat를 시장 freshness나 lease 연장의 근거로 사용하지 않는다.

SQLite는 일자당 128MiB/스코프당 2,048 revision/뷰당 최대900봉의 admission 상한을 둔다. 참조 중인 과거 revision을 삭제하지 않고 저장 한도/손상/경합 시 검증된 bounded REST 경로를 사용한다. 원천 hash는 **정규화한 provider 행**의 hash이며 raw wire body hash로 부르지 않는다. 같은 완료 cutoff는 재사용하지만 forming은 최대3초의 원 수신 기한을 넘겨 재사용하지 않는다. 임의 range/limit API 필드를 만들지 않았고, continuation은 필요한 고유 행이 확보되면 멈춘다. 기존 430 raw 호환 요청 자체를 전역 축소하지 않았다.

## 3. 리뷰에서 발견하고 수정한 경계 결함

1. 완료 시점의 trigger/last-AI 재계산으로 원 결과를 못 찾거나 generation 제거 후 결과가 남는 문제: 원 request/generation/cache key로 꺼내고 현재 generation을 별도로 검증한다.
2. 이전 결과의 정리가 새 요청/claim을 지울 수 있는 문제: `ENTRY_LOCK` 안에서 generation/cache/token을 대조한다.
3. 유효하지 않은 DB 등록이 native claim을 먼저 소비하는 문제: DB 입장 검증 후 claim하며 commit 실패는 그 claim의 명시 종료로 기록한다.
4. queue fsync 실패가 아직 시작하지 않은 probe를 in-flight로 남기는 문제: 미발행 admission을 원 상태로 복원한다. 결과 저장 실패 후에는 동일 promotion을 보존하되 재발행 직전 원 deadline을 재검증한다.
5. REMOVE 실패/예외인데 CLOSED를 발행하고 슬롯을 반환하는 문제: 미확인 정리를 같은 lease의 bounded retry 집합에 남긴다. 완료 callback이 RESULT보다 먼저 끝나도 CLOSED는 RESULT 이후에만 발행한다.
6. 완료봉 수정으로 이전 판정 입력이 바뀌거나 짧은 갱신이 이전 prefix를 버리는 문제: 내용 hash와 불변 revision, as-of 가용시각, overlap 정정 및 prefix 연결을 검증한다. overlap 안의 빠진 봉을 합성하지 않는다.
7. 형성 중인 봉의 normalized cache가 원 수신 기한보다 길어지는 문제: cache expiry도 최초 REST 수신+3초로 제한한다. cache hit의 caller HTTP는 0으로 기록한다.
8. 준비 worker의 file lease→writer mutex와 기록 경로의 writer mutex→file lease가 만드는 역순 잠금: 준비 경로는 file lease를 반환한 뒤 writer mutex로 캐시 참조를 갱신한다. 전용 동시성 반례를 추가했다.
9. PASS projection에서 malformed clock/결손 ID·동일 event의 verdict 충돌을 놓치는 문제: 불량 신원은 제외하고 충돌은 unobservable로 남긴다. raw/compact 실패를 성공으로 간주하지 않는다.

## 4. 공식 Kiwoom 원천과 정책 호환

2026-10-08 20:43~20:47 KST에 공식 `Kiwoom-Securities/Kiwoom-REST-API` HEAD를 조회하고 commit **953e5dbff123f437ab4d11a78a95191a685eb51f**의 다음 파일을 대조했다.

- `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/realtime/packets.py`
- `kiwoom/_data/kiwoom_api_spec.json`의 ka10080/kt00011/0B/0D
- `postman/kiwoom-openapi.postman_collection.json`의 실전/모의 및 요청 변환

해당 upstream tree에는 `kiwoom_docs` 디렉터리가 없었다. ka10080은 `stk_cd/tic_scope/upd_stkpc_tp/base_dt`, continuation 및 signed KRW OHLC·주식 수량·KST timestamp를 유지한다. `_AL`은 통합 SOR, `_NX`는 NXT exact 경로다. 코드의 `minimum_rows`는 로컬 continuation 종료 조건이고 wire 필드가 아니다. 주문 샘플을 실행하지 않았다.

현재 정책을 작업본에서 읽기 전용 `load_effective`로 검증한 결과 PASS다. bundle `40fb3ec7d5f44e2e34044f2a14e2d0d06dd6ea264f69b5f1481be899f2a4a689`, schema `continuous_reversal_policy_v6`, pinned module **27개 불일치 0개**다. native kernel/정책 pin 파일을 수정하지 않고 unpinned orchestration/diagnostics를 변경했다. 이 결과는 새 release/PID 소비 영수증이 아니다.

## 5. 검증과 성능의 범위

- 통합 회귀 **1,135 passed**: async coordinator/bridge, capacity, AI trace, probe/Main attach/queue/runtime, candle/MTF/market data, pipeline/Sentinel monitor, watching, v4/v5/v6 정책, WS/fixed watch/machine observation. pandas 설정 deprecated 경고와 기존 fork 테스트의 multithread 경고 2개가 있었다.
- 보완 회귀 **153 passed**: generation 교체/제거, provider dispatcher, fixed-watch 제출 계약, 원장/결과 경계. 앞선 통합 검사와 겹치므로 합계를 고유 테스트 수로 사용하지 않는다.
- 역순 잠금 수정 뒤 최종 관련 회귀와 compile/diff/parser 결과는 아래 최종 검증 기록으로 보완한다.

모든 테스트는 격리된 데이터 경로·가짜 broker/provider 응답을 사용했다. 운영 연구 호출이나 과거 대형 원장을 복제하지 않았다. 합성 벤치마크 임시 디렉터리는 완료 후 삭제했다.

| 격리 측정 | 결과 | 해석 |
|---|---|---|
| 80,000행, 420,388,890 bytes 합성 원장의 이전 full-prefix 읽기 | 3회 중앙값670.140ms, 최대671.590ms | 원장 읽기 비용만의 기준값 |
| 같은 원장의 background index 준비 | 최대4MiB씩101회, chunk p95 14.668ms/최대14.959ms | 비용이 사라진 것이 아니라 기존 준비 worker로 이동 |
| 준비된 index에서 durable append | 25회 중앙값3.098ms/p95 4.206ms/최대345.618ms | 첫 합성 파일의 미동기화 쓰기를 포함한 fsync outlier가 있음. 최악 지연이나 모든 늦은 PASS 해소를 보장하지 않음 |
| 완료봉 60개, 같은 cutoff 50회 읽기 | 중앙값1.083ms/p95 1.189ms, caller HTTP 합계0 | 고립 store 재사용 측정. forming 필요 시 HTTP가 계속 필요할 수 있음 |
| 형성 중인 봉, 최초 수신+30초 | 재사용 거절 | 이력 재사용으로 실시간 freshness를 연장하지 않음 |

38,788,890-byte 소형 비교에서는 hot append p95 4.476ms/최대24.433ms였다. 이들 수치를 실장 p95나 REST 감소율로 전용하지 않는다. 배포 후에는 동일 watch/session/claim 수와 필수 계좌 조회·추가 forming 요청을 함께 비교해야 한다.

## 6. 인계

이번 작업은 배포하지 않았다. 작업 도중 별도 장후 복구 owner가 selector/checklist를 변경한 사실은 관측했으나 본 변경의 배포 증거로 사용하지 않는다. 현재 checklist objective/mandatory 규칙을 다시 확인했고, 본 작업은 그 파일과 AUTO 봉인 블록을 쓰지 않았다.

후속 배포 지시 시 최신 작업본/선택 release/기동 대상일을 다시 대조하고 기존 handoff로 검증해야 한다. 과거 prepared/PID 영수증을 재사용해 새 PID 정상가동으로 표시하지 않는다. 자연 지연·actual submit/fill·장후·다음 예약기동은 이번 미배포 코드 검증과 별도다. H4 source equivalence 미입증 범위는 계속 REST를 사용한다.

## 7. 최종 작업본 검증

- 역순 잠금·orphan 결과·진단 writer 실패 보완 후 관련 회귀 **244 passed / 4.99초**. 통합 1,135개 및 앞선 153개와 중복되는 재검사이므로 고유 테스트 수로 합산하지 않는다.
- 영향 Python 모듈 20개 compile 통과, `git diff --check` 통과. 이번 변경에는 shell/cron/systemd 수정이 없어 shell 실행 검증은 하지 않았다.
- 네 계획+이 리뷰의 로컬 링크 143개, 누락 0. print-only backlog parser 22개 항목, 현재 Main stable owner 1개, 경고 0. 외부 Project/Calendar sync는 실행하지 않았다.
- 검토 범위에서 발견한 결함은 수정·표적 반례·재리뷰를 마쳤다. 자연 시장 성능과 H4의 원천 동등성은 미입증이며, 이를 코드 테스트 통과로 대체하지 않는다.

세부 출력은 `/tmp/main-integrated-final-regression-20261008.txt`, `/tmp/main-final-lock-review.txt`, `/tmp/main-integrated-policy-verification.json`, `/tmp/main-integrated-benchmark-20261008.json`, `/tmp/main-integrated-large-benchmark-20261008.json`, `/tmp/main-integrated-print-backlog-20261008.txt`에 있다. 이 임시 출력이 사라져도 위 표의 핵심 결과와 저장된 회귀 코드로 검토 경계를 확인할 수 있다.
