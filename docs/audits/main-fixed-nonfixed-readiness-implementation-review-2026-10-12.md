# 상시·비상시 신호 준비·전달 구현 리뷰 — 2026-10-12

[계획](../proposals/main-fixed-nonfixed-signal-readiness-and-latency-remediation-plan-2026-10-12.md)을 리뷰·보완하고 선행 native claim 작업본에 통합했다. 이번 요청은 구현·리뷰이며 배포·재기동은 실행하지 않았다. 정책·원 5초·source freshness·관측 5슬롯/긴 슬롯 2개·60/150초·주문/보호/custody 조건을 유지한다.

## 수정과 실제 연결

| 범위 | 수정 | 소비 경로 |
|---|---|---|
| N0 | subscriber만 아니라 WS/AI/token 존재, REST/WS 환경 설정, session/epoch/family 및 프로세스 준비 세대를 확인 | EventBus readiness → scanner admission → callback → executor worker. 상태 교체 시 물리 REG 전 종료 |
| N1 | registry/branch hash에 묶인 history/hold/표본/side/qty descriptor, 최초 긴 슬롯 대기 시각, 실제 native 가격대의 scope 재검증 | 기존 discovery queue → 원 claim → first-data/terminal branch readiness |
| N2 | 0B/0D packet/dispatch/normalization/read 시계·sequence 분리, native 호출 반환과 실제 수용 분리 | 기존 normalized WS snapshot → probe → lossless execution projection |
| S2 | 같은 유효 신호의 최초 eligible 관측만 기존 Main completion Event에 통지 | native 관측 → 기존 coordinator wait → Main 재검사. tick마다 알리지 않음 |
| S3 연결 | `zero_base_probe_result`가 기존 분 단위 execution partition에 전달되지 않던 결함 수정 | 원본 JSONL → `entry_mechanical_momentum/part-execution-*`; 상세 capsule 텍스트 중복 제외 |

actual-price descriptor는 현재 native detector의 scalar와 coverage를 읽는다. root 현재 조건 TRUE는 FALSE→TRUE 전환/hold 완료가 아니며, feature 가용성과 detector 판정을 구분한다. 없는 시각·raw 참조·정의되지 않은 0D provider 시각을 채우지 않는다. 첫 수신은 retained interval 내 최초 행이라는 범위를 명시한다. 오래된 마지막 tick의 FALSE를 현재 정상 음성으로 표시하지 않는다.

admission의 과거 prefix 재사용은 허용하지 않았다. 기존 shared-owner의 연속 interval을 admission에서 검증하지 못하는 상황에서 이력을 재사용하면 짧은 슬롯에 잘못 배정할 수 있다. 현재 관측 interval의 coverage는 분석에 보존하며, 검증 가능한 prefix 재사용 최적화는 후속 범위다.

## 리뷰·수정 반복

1. 준비 확인 후 reconnect/정책·객체 교체가 가능한 경계를 확인하고 worker 실행 직전 재검증을 추가했다. 불명확한 physical lease는 기존 cleanup/ACK가 닫으며 미전송 증거와 혼동하지 않는다.
2. 정의의 설명 문자열로 거래량 조건을 추측하던 부분을 실제 legacy rule ID/명시 필드로 연결했다. descriptor cache는 registry hash+branch ID, 반환은 복사본으로 격리한다.
3. current native state의 실제 가격대와 generation을 검증하고, stale tick·source reset은 UNKNOWN으로 보존한다. 미래 전환을 관측 길이만으로 보장하지 않는다.
4. 0B/0D 집계에서 다른 route·epoch·미래/비유한 receive clock을 제외했다. 전체 정렬 대신 최초 5개 시각만 보유하며 총수·signed 수는 모두 집계한다.
5. 실제 writer→reader 회귀에서 probe execution partition 누락을 발견해 family/stage 연결을 수리했다. 원본과 projection의 execution identity를 유지한다.
6. terminal 진단에서 이미 읽은 exact snapshot을 다시 조회하는 비용을 제거했다. 원 시각을 보존한 pre-machine 관측을 재사용하고, 그 이전 실패만 terminal memory read를 수행한다. 진단 실패가 원 결과나 물리 cleanup을 덮지 않는다.

## Lock와 권한

- EventBus subscriber lock은 callback/readiness 실행 전에 해제한다.
- readiness owner는 메모리의 dependency tuple과 단일 generation만 자신의 lock에서 갱신한다. token/계좌/키 및 그 digest를 출력하지 않는다. 환경 일치는 설정의 real/demo 일치이며 토큰의 유효성 증명으로 확대하지 않는다.
- native 관측은 backend → carried backend → diagnostics 순서를 유지한다. Main wake는 native/diagnostic lock을 놓은 뒤 Event만 설정한다. WS caller의 기존 외부 lock 아래에서도 disk/DB/provider 호출을 추가하지 않는다.
- branch 상태는 native lock에서 scalar만 복사한다. definition deepcopy/hash/cache와 보고서 투영은 lock 밖에서 수행한다.
- 필수 queue persistence가 callback보다 먼저다. 준비 실패도 기존 result/ACK/expiry 처리를 중지시키지 않는다. callback/worker 시작 경합과 long-slot 대기/cleanup은 동일 lease 신원을 사용한다.
- 새 engine-root 모듈·worker·provider 호출·정책 파일·대형 원장을 추가하지 않았다. native v6 code-pin 대상은 변경하지 않았다.

## 공식 Kiwoom 참조

이번 실행에서 upstream HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`를 재조회했다. SDK `kiwoom/core/auth.py`, `core/client.py`, `realtime/packets.py`, `realtime/stream.py`, `kiwoom/specs.py`, Postman PRD/MOCK 설정을 확인했다. 해당 commit tree에는 `kiwoom_docs`가 없다. 변경은 기존 환경 설정의 일치 확인과 normalized 0B/0D 처리 시각의 투영이다. wire request·FID/sign/unit/time 해석·REG/REMOVE·인증 발급/refresh·계좌/주문 요청을 변경하지 않았다. [조회 시각·파일 해시](../../tmp/fixed-nonfixed-readiness-20261012/official-reference.json).

## 검증과 성능의 범위

**최종 24개 테스트 파일 1,462 passed**, compile·print-only parser·로컬 링크·diff 검사 PASS. 검증 수와 코드 해시는 [완료 영수증](../../tmp/fixed-nonfixed-readiness-20261012/completion.json)에 기록한다. [통합 pytest](../../tmp/fixed-nonfixed-readiness-20261012/pytest-final.txt)는 native/branch parity, 원 deadline, source/route/epoch, exact lease, async 단일 소비, Main guard, bootstrap/ordered deployment 호환을 포함한다. [수정 후 표적 회귀](../../tmp/fixed-nonfixed-readiness-20261012/pytest-final-fixes.txt)는 382건 통과했다. 기존 pandas_ta의 pandas Copy-on-Write deprecation warning은 별도다.

[component 비교](../../tmp/fixed-nonfixed-readiness-20261012/component-benchmark.json)는 동일 5 fixed+5 nonfixed stream, 각 run 150개 opportunity/Main 방문, 로컬 필수 append 60개, 교대 3회다. 실제 coordinator wait를 사용했으며 native 상태는 소비하지 않는다.

- ready→Main 방문 p95: baseline **46.925~46.947ms**, candidate **0.306~0.315ms**.
- callback p95: baseline **0.101~0.107ms**, candidate **0.086~0.108ms**. 150개 관측/방문·60개 append를 유지했다.
- CPU 0.011~0.013초/run, 최대 thread 2개. 실행 파일에 wall/RSS/loop 값과 원 코드 해시를 보존했다. OS fsync 변동이 있으므로 loop tail 전체 개선은 확정하지 않는다.

이는 Main 대기 연결의 component 결과다. COMMIT/holding/exit/account는 로컬 대역이며 물리 WS lease/REST/provider는 0회다. 실제 full Main 부하·signal→claim/capture·자연 p95/p99·실현 손익을 검증한 결과가 아니다. 물리 5슬롯/긴2·cleanup 경쟁은 별도 기존/추가 회귀로 확인하며 component의 10stream을 실제 구독 실적으로 세지 않는다.

## 인계

착수 기준 selected release는 `auxiliary-consumption-attestation-20261012-v1`, 실제 PID `1020707`/start `3378564`였다. [기준 해시](../../tmp/fixed-nonfixed-readiness-20261012/baseline.json)는 작업본/현재 PID와 역사 조사 PID를 구분한다. 운영 정책 발행·selector 변경·재기동·장후 재생성·Provider/broker 호출은 수행하지 않았다.

현행 sealed checklist 바이트는 유지했다. [후보 checklist](../../tmp/fixed-nonfixed-readiness-20261012/2026-10-12-stage2-todo-checklist.md)는 선행 native/auth 보완을 이어받고 `MachineAuxiliarySignalDeliveryRepair1012`·`NonfixedDispatchReadinessReview1012`를 각각 한 번 유지한다. 최종 배포/PID 소비와 자연 신호 수용은 해당 owner의 후속 증거이며 이번 작업본 리뷰 완료와 구분한다.

## 배포 후 추가 코드리뷰·결과 수신 보완

위 구현 당시의 미배포 기록은 역사 증빙이다. 후속 `native-readiness-20261012-v1` 배포는 [통합 리뷰](main-native-readiness-deployment-review-2026-10-12.md)에서 확인한다. 이번 재리뷰는 해당 릴리스/PID `1171338`을 기준으로 시작했으며 사용자가 결함 보완·배포·재기동을 승인했다.

- 추가 결함: 결과 inbox의 중복 제거가 claim 횟수·source hash만 확인했다. 원 claim 시각/scope·lease·candidate·판정 형식이 잘못된 응답이 먼저 들어오면 뒤의 정상 결과를 버렸다. 다른 lease의 해제 ACK가 먼저 들어오는 경우도 정상 ACK가 유실돼 슬롯이 남았다. 운영에서 이 순서가 발생했다고 추정하지 않으며, [6개 실패 재현](../../tmp/native-readiness-rereview-20261012/reproduction.txt)으로 코드 결함을 확인했다.
- 보완: queue의 원 claim 매칭을 공유하고 inbox 저장 전에 해당 신원·결과 형식·명시된 lease를 검증한다. 해제 소비자도 동일 원 claim을 대조한다. 기존 pre-worker/legacy 무lease 응답은 보존하며 실제 lease가 있는 정상 결과는 정확한 해제 ACK까지 슬롯을 반환하지 않는다. 잘못된 자료가 정상 응답의 중복 키를 선점할 수 없게 한다.
- 재리뷰: 신규 discovery가 진행 중 claim을 바꾸지 않는지, malformed payload/다른 claim/다른 lease 배제, 중복 정상 응답 단일 소비, 원 기한·persist 실패 재시도·물리 cleanup을 확인했다. 관련 10개 파일 **595 passed**, 기존 pandas_ta 경고 1개. [검증 로그](../../tmp/native-readiness-rereview-20261012/pytest-final.txt).
- 적용 경계: Kiwoom 요청/응답·WS FID/REG/REMOVE/auth, 정책 선택·threshold·provider/model·5초·5슬롯/긴2·60/150초·Main/manual custody는 변경하지 않았다. 새 worker/원장/관측 범위를 만들지 않았다.

배포는 기존 ordered 경로의 사전검증 → 원 PID/supervisor 정상 종료 → selector/checklist → native 인계·bootstrap·보조 호환성 → 새 PID 소비 확인으로 진행한다. 기존 `NonfixedDispatchReadinessReview1012`와 `OrderedIntradayDeploymentRepair1012`에 연결하고 원 최종화/PREOPEN/정책 바이트를 보존한다. 실제 완료 여부는 [최종 증빙](../../tmp/native-readiness-rereview-20261012/completion.json)으로 분리한다. 자연 신호·AI·주문 표본과 성능/경제성은 코드 회귀로 대신하지 않는다.

17:08:11 KST 배포·재기동 완료. `native-readiness-20261012-v2` / `cf650549e7a07ed470cd95a500af43336d31232c`, ubuntu PID `1215171`/start `4182334`의 bootstrap·원 준비·장중 인계·기계/보조 소비 및 **128경로** 호환성 PASS. 불변 릴리스의 수신/queue 회귀 **43 passed**로 원 작업본과 대조했다(595건과 중복이므로 합산하지 않음). 17:08:25 자연 감시가 새 릴리스 소비를 확인했고 신규 log 오류·최종화 세대 오류는 없다. 이전 야간 최종화/log rotation의 `recovered_late`는 역사 사실로 남긴다. 판정·주문 효과나 성능 개선은 이번 재기동 검증 결과가 아니다.
