# Main 추가 8개 패턴 구현·검증 기록

사용자는 추가 8개 패턴 계획의 구현, 반복 리뷰·보완, 완료 후 배포·재기동을 승인했다. 실행 owner는 `DirectFamilySourceRepairMainMechanisticEntry` 하나다. 기존 주문·보유·미체결·자금·수량·manual veto·hard safety는 유지한다.

## 구현 경계

- 선행 current는 v3 bundle `99c795dd19fc6ce30fb46956119bcc70b2a8b7fc8a1a19cb138bef9f95d67b6e`, family `aa4c55d2d0de71ddca0b548100c7b435ab254548dc0963ffc373bbb9c91fb721`, release `c1343c2584d75e33de4ab6c68432810e34abbff6`, PID 1021822다. R0에서 확인한 8개 v3 계약 소스의 bytes를 보존한다.
- 새 catalog/runtime/auxiliary/native policy/postclose는 `src/engine/scalping`에 둔다. `src/engine` 루트에 파일을 추가하지 않는다. 기존 v3의 내용 hash 계약 때문에 별도 v4 구현이 필요하며, 버전 dispatch는 고정 v3 파일 밖의 adapter가 소유한다.
- 8개 원 연구 definition/branch ID/hash를 그대로 등록한다. 신규 범위는 정확한 `symbol_AL`의 SOR REGULAR뿐이다. 기존 48셀·128경로 및 명시된 유한 비교 목록을 유지한다.
- 지속 root는 반전 없이 모든 유효 틱에서 known false→known true를 검사한다. 유지 확인은 첫 실제 1초 이후 틱, 재시험은 최대 120초의 원 저점·고점/FIRST 가격을 사용한다. HA의 원 FIRST 입력·문구와 기존 FIRST/CONFIRMED 요청 bytes는 유지한다.
- 신규 phase는 `machine_signal_confirmed`·`signal_kind`로 표현하며 가짜 low/drop/price reversal 사실을 생성하지 않는다. provider 후 current bundle·claim generation·5초 TTL·연속 경로를 다시 검증한다.
- 신규 ledger 및 비교 run은 v4에 격리한다. 기존 v3의 날짜별 비교와 WAL은 변경하지 않는다. 원장 예약 전 expected 입력/arm manifest와 실제 응답 snapshot을 봉인한다. raw PASS 승률로만 비교하며 미완료·무 PASS·무 primary 표본을 구분한다. 미준비 scope는 검증된 기존 기계·보조 쌍을 함께 carry한다.
- Kiwoom 요청·응답 parser/FID·REG/REMOVE·recovery/API 동작은 변경하지 않았다. 기존 normalized callback의 내부 policy backend 소비자만 바뀐다.

## 반복 리뷰와 보완

1. 알려지지 않은 schema/backend가 구 정책으로 fall back할 위험을 명시 거부로 보완했다.
2. 가격대 이동 중 root 추적은 해당 family의 실제 선택 정의 합집합으로 유지하고 claim에는 실제 확인 가격대의 선택 branch만 남긴다.
3. family 전환 시 새 root의 준비 구간을 초기화해 과거 warmup을 새 신호로 사용하지 않는다. 같은 프로세스에서 복원된 native session anchor는 재사용한다.
4. 신규·기존 pending의 운영 용량을 함께 계산하고, offline replay는 live pending/ready 표본 상한을 사용하지 않는다. 첫 확인점의 quote 결손은 계측하며 다음 유리한 틱으로 이동하지 않는다.
5. 과거 기계 확인점은 불변 재생 snapshot에서 가져오되 같은 현재 frozen tick/bar generation으로 라벨을 재계산한다. 신규와 과거가 같은 확인점에서 다른 ask/라벨이면 명시 실패한다.
6. 신규 input/proof/feature와 의미적 감시의 재생 판정을 결속했다. 새 signal을 첫 반전으로 오인하거나 prompt 변경 전 응답을 재사용하지 않는다.

## 검증 상태

신규 phase/전송기/claim/감시/compose/입력 누락 회귀 37개 PASS. 최종 기계·보조/native/장후/감시·handoff/router/cron/location 대상 17개 suite에서 865개 PASS, 기존 pandas 경고 1개다. compileall, restart/router bash 문법, diff 공백 검사 PASS. 테스트 전송기의 가짜 응답은 실제 AI 응답으로 집계하지 않는다.

누적 native 재생·연구 parity는 완료했다. 실제 AI 비교 원장 준비와 immutable 배포/PID/자연 수신은 아래 인계 기록으로 별도 종결한다. 근거 작업 디렉터리는 [R0~R8 자료](../../tmp/main-additional-eight-implementation-20261007/)다.


## 최종 리뷰에서 추가로 보완한 결함

7. 다른 branch가 같은 틱에 먼저 만들어진 경우, 대표 지속 신호에 그 branch의 low/drop 사실이 남지 않도록 대표 event를 해당 신호로 다시 구성했다.
8. 기존 frozen FIRST와 새 typed 신호를 합칠 때 원 FIRST의 low/drop/입력 원천이 사라질 수 있는 경로를 보완했다. SB/AA의 120초 경계·엄격 하회와 GA의 추가 TTL 없는 유지 확인도 회귀했다.
9. 예상 owner 집합을 입력 파일에서 거꾸로 계산하는 결함을 보완했다. frozen population에서 예상 canonical/branch/owner/outcome 집합을 먼저 봉인하고, 입력 집합 digest·비교별 개수와 대사한 뒤 ledger를 연다. 입력 누락 및 같은 개수의 다른 ID는 ledger 준비 전에 거부한다.
10. 입력 생성 코드를 별도 snapshot/hash로 묶고 cache generation에 포함했다. 코드가 바뀐 이전 입력을 파일 존재만으로 재사용하지 않는다. 실제 provider 동시 in-flight는 최대 4로 검증하고 호출 수 상한은 None이다.

11. 합쳐진 과거 partition의 canonical 정렬은 종목 순서가 아니므로, 특징 cache가 매 점 전체 원천을 재계산하는 지연을 발견했다. 입력 재구성을 임시 SQLite로 종목/item별 disk grouping하고 예상 owner digest는 정렬된 내용으로 대사한다. 혼합 순서 fixture에서 원 point/값/owner 집합 보존과 임시 파일 정리를 검증했다. 표본이나 caller 목록을 줄이지 않았다.

12. 재개 시 갱신되는 input census/expected manifest를 발행 family가 직접 참조하는 위험을 보완했다. 발행 직전에 내용 hash별 immutable snapshot으로 옮겨 참조한다. producer의 완료 개수가 바뀌어도 발행된 과거 family의 source 검증은 유지된다. snapshot tamper 거부를 회귀했다.

## 원 연구와 native 대조

원 연구의 오늘 prefix는 15:20까지이고 선행 v3 snapshot은 14:13까지다. 처음 대조의 삼성 SB 4점 차이는 이 접두 차이였다. 원 연구의 전체 오늘 bytes SHA `ea95439a2406e6c42855174ee19e2f83e08434a1b8641475f1f7c2e1d0f2a3c9`를 영속 custody에 옮긴 뒤 다시 대조했다. 최종 확인 index/epoch/ask/필터 특징/라벨은 8개 모두 missing/extra/value/feature mismatch 0이다. 불변 run은 `f35a8ae57520f9871f232ba02dd4ec0cc7d356869e541d2cf078127518b4efd0`, registry는 `43ee7f1a7fed2a7d05c9ad4f5c78416c3016fa1a779a3aaef71e04ad7caece70`이다.

| 패턴 | WIN | FAIL | U | 원 연구 확인점/native |
| --- | ---: | ---: | ---: | ---: |
| 삼성 SA | 22 | 0 | 1 | 23/23 |
| 삼성 SB | 53 | 0 | 135 | 188/188 |
| 두산 DA | 13 | 0 | 10 | 23/23 |
| HPSP HA | 30 | 0 | 15 | 45/45 |
| HPSP HB | 6 | 0 | 11 | 17/17 |
| 알테오젠 AA | 20 | 0 | 0 | 20/20 |
| 주성 JA | 44 | 0 | 0 | 44/44 |
| 일반 GA | 36 | 4 | 43 | 83/83 |

승패는 비용 후 +0.4%를 30분 안에 소프트손절 -3%보다 먼저 넘는 native 라벨이다. U는 성공/실패 분모에서 제외하며 실현 거래 승률로 표시하지 않는다. 반복 확인점과 날짜 집중도는 원 연구 자료에 남긴다. 새 8개 중 기계 winner로 선택된 것은 0개다. raw 분수 동률은 현행 우선, 이후 고정 순서이므로 표본 수를 tie breaker로 더하거나 초기 지정하지 않았다. 미선택 8개는 실제 primary AI 호출 대상이 아니며 `not_requested_machine_unselected`다.

52개 native source partition에서 기존 모든 유한 조합·신규 단독/명시 조합·현행/장중 실제 적용 버전을 같은 source/bar generation으로 비교했다. 비교 보고 SHA는 `efebb567d8424f2212cc81f636abdd0cf14649653e73f3a25d27a28efa1eb5bb`. machine winner와 publishable pair를 분리한다. 새 branch나 다른 기존 branch의 AI 비교가 미완료이면 검증된 이전 기계·보조 쌍을 carry한다.

## 성능 및 운영 인계 경계

같은 frozen 최대 첫 25,000틱씩 고정 5종목, 합계 113,306틱에서 callback 처리 p99는 기존 31~169us, v4 현행 목록 37~242us, 신규 root 병행 목록 131~276us다. 관측 max는 1.089ms 이하였고 기존 신호 census는 5종목 모두 같았다. 이는 같은 서버의 offline CPU 실측이며 실제 WS 전달 지연이나 5초 claim 통과를 보장하지 않는다. natural snapshot의 backlog/source latency는 배포 후 별도 확인한다. 독립 episode PID 785938 및 pinned service release는 재기동 대상에서 제외한다.

기존 finalization은 read-only 확인에서 `recovered_late`, generation basis `consumed_intraday_preserved_historical_generation`였다. 경고를 억제하지 않고 10/6 원 완료/다음 PREOPEN bytes를 유지하며 현재 checklist/release를 새 장중 handoff로 봉인한 뒤 기동한다. 배포 전 13개 보호 파일 hash와 기존 PID bootstrap/parent CAS를 다시 확인한다.

추가 구버전 parity: 같은 113,306틱에서 기존 5,876개 확인점의 branch_signals와 보조 input이 모두 같았다. 삼성 이 접두의 현행 신호는 0개였으므로 삼성 자연 신호 입증으로 확대하지 않는다. 근거는 작업 디렉터리 `legacy-parity.json`이다.
