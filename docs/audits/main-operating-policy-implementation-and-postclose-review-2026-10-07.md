# 운용 정책 독립 탐지·기여도 평가 구현과 장후 인계

사용자가 10/7 계획의 구현·반복 리뷰·배포 후 중단한 EOD 제외 장후 재개와 10/8 정상 기동 준비를 승인했다. source date는 자정 이후에도 `2026-10-07`, 준비 대상은 `2026-10-08`이다. 현재 owner는 10/8 체크리스트의 `DirectFamilySourceRepairMainMechanisticEntry`다. 10/8 자동 builder는 10/7 runtime summary 미생성으로 아직 실행 불가하여 승인 범위/Acceptance를 같은 stable ID로 명시 이관했다.

## 구현 경계

- 기존 v4의 정의/phase/코드 pin을 보존하고 `scalping` 패키지에 v5 실행 계약·dispatcher·runtime·복합 auxiliary·outbox·평가·장후 producer를 추가했다. 엔진 root 모듈을 늘리지 않았다.
- 최초 manifest는 실제 부모 목록+SA/SB/DA/HA/HB/AA/JA/GA이며 원 scope를 유지한다. 일일 평가 결과로 운용 목록을 자동 제외하지 않는다. explicit ADD/REPLACE/RETIRE는 부모와 변경 receipt를 요구한다.
- 실행 hash와 보고 세대를 분리한다. 같은 scope의 실행 의미가 같으면 FSM/claim을 보존하고, 다른 scope 변경만으로 무효화하지 않는다. 공통 5초·source/epoch 경계는 유지한다.
- 동일 tick의 모든 신호를 typed union으로 봉인한다. FIRST가 무효화되어도 같은 5초 안의 독립 돌파가 남으면 이를 재검증한다. 새 신호를 응답 뒤 추가하지 않는다. AI는 전체 signal ref와 실제 fact ID를 명시하고 공통 기회 PASS/VETO/CAUTION만 판정한다.
- live outbox는 공통 offline 원장과 별개다. 외부 전송 전에 canonical 확인점을 예약하고 기존 provider/parent intent registry를 연결한다. 불확실 전송은 새 세대/재기동으로 재전송하지 않는다. 정확히 한 번 전송을 보장한다고 주장하지 않는다.
- 누적 원천의 실제 ask·1,800초·비용률 .0023·순목표 +.4%·soft -3% native label을 재사용한다. 탐지 UNKNOWN과 결과 U, 독점 입증/미입증, 비교 공통 범위와 제외 baseline을 구분하고 coverage mask를 압축 객체로 보존한다.
- 비교안은 실제 native 현행, 같은 목록 union, 각 8개 추가, 일괄 추가로 고정한다. 공통 Store에 누락 exact request와 membership만 추가한다. quota=None이며 동시 4개·native stage deadline을 유지한다. arm 하나라도 응답/계약이 부족하면 해당 확인점은 모든 arm 순위에서 제외하고 incomplete를 공개한다.
- 미완료 scope는 원 v4 pair를 native backend로 승계한다. 새 union 준비/구 pair 승계/실제 PID 소비를 구분한다. 무표본 PRE/AFTER는 호환되는 동일 유형 REGULAR union binding을 승계하며 정책 ID를 정규장 목록으로 바꾸지 않는다.

## 리뷰·보완

1. legacy 기본 정책의 `definition_sha256` 부재: 원 정의 내용 hash로 안정적인 signal ref를 구성했다.
2. 삼성 native callback의 non-Samsung 가격대 조회: 별도 successor dispatcher에서 `samsung|시장|ALL` 주소를 사용한다. 동결 v4 파일은 바꾸지 않고 실제 normalized callback regression으로 확인한다.
3. 감시/장후 stage/native loader의 새 schema 누락: v5 envelope·48셀/128route·mixed backend·실제 요청 hash 검증을 연결했다.
4. code hash와 실행 세대 분리의 무결성: execution code digest를 실제 pin 목록에 결속하고, 현재 envelope는 매번 검증하면서 동일 scope만 보존한다.
5. 비교 원장: 5-arm exact membership 검증, invalid arm 전체 분모 격리, uncertain 재예약 거부, 재준비 중복0과 불변 source snapshot 소비를 검증한다.

6. final-refresh systemd의 v8 고정 pin: selected-release router 경로를 추가하고 기존 EOD gate installer가 서비스 비기동 상태에서 timer 보류를 보존하며 router drop-in을 설치하도록 보완했다. 재개 시 old code로 돌아가는 경로를 제거하고 자정 뒤 완료 원천일을 해석한다.
7. 동일 canonical 원천 충돌은 식별한 확인점만 격리하고 나머지 분석을 계속한다. 각 고정 추가안의 공통 비교 범위와 실제 native arm 대비 추가/제외 PASS, 기계·보조 tradeoff를 별도 집계한다.

## 검증·운영 상태

초기 관련 회귀 692 PASS, 후속 독립 콜백/혼합 신호 보완 포함 695 PASS, 확장 최종 회귀 699 PASS. consumer 인계 208 PASS와 router/실행 계약 107 PASS를 추가 검증했다. 최종 계약 검증·immutable release 검증과 실제 배포/재개/terminal/PREOPEN 결과는 아래에 이어 기록한다. 이 단계의 테스트 성공은 실제 정책 적용이나 자연 주문·경제성 개선이 아니다.

근거 디렉터리: `data/report/operating-policy-implementation/2026-10-07/`. N0 부모 bundle `69caaf00f2a0475e0290de0b239f28975333782429a62f4e238c8d0ae96f5d78`, family `ed50d100aef3d66361c83bea53441ae0b4461b8ac98fdbcb87346cc9790a324d`. 23:51 재조회에서 이전 Main PID 1074119는 이미 종료 상태였으며 이 작업이 종료시키지 않았다. 장후 배포와 다음 예약기동 준비를 별도로 검증한다.

실제 `capture_machine_observation` 생산자가 만든 union 판정 증빙을 감시 소비자가 검증하는 회귀도 PASS이며, 원 요청을 변조하면 거부한다(독립 운용 suite 16 PASS). 설치는 기존 `deploy/install_postclose_eod_gate_systemd.sh`를 사용하고 final-refresh 실행은 `deploy/run_runtime_release.sh machine-final-refresh`가 선택된 release와 완료 원천일을 해석한다.

8. 과거 v5 envelope와 내장 v4 부모의 원 commit이 다를 때 historical 검증을 새 envelope origin checkout의 실제 별도 Python reader로 수행하도록 수정했다. origin attestation만 fixture로 제공하고 실제 source reader를 실행한 회귀 포함 109 PASS다. 최초 immutable 검증 455 PASS 뒤 이 보완을 재검증한다.


## 배포와 재개

- 코드 `64ed75ef52c9b8ddfbe048fc67c00a3afc282fff`, 불변 release `operating-union-20261008-v2`를 선택했다. 기존 native v4 source 검증 PASS, 독립 서비스 inventory 63개와 기존 policy pin 보존을 확인했다. 실제 Main은 비가동이며 다음 예약 시작 전이다.
- 00:25 KST에 원 보류 cron 5개만 원문 CAS로 복원하고 final-refresh timer를 복원했다. router는 10/7 완료 원천일과 새 release를 읽는다. postclose/controller/tuning을 각각 10/7로 재개했다. EOD 완료 receipt hash `747c766b5cba01a597dbe9d3249a433083523bd26ecf8e63c061cfaa356af7d3`는 보존한다.
- archive의 첫 수동 호출은 날짜 환경변수가 없어 10/8 EOD 대기에 들어갔다. 실제 압축 실행 전 이 작업의 해당 process group만 중단하고 기존 `TARGET_DATE=2026-10-07` 인터페이스로 다시 실행하여 00:26:11 DONE을 확인했다.
- 최초 research capacity는 자정 후 과거 계좌 원천을 새로 수집할 수 없어 invalid였다. exact-date episode OFF receipt와 공동 allocation OFF 소비 경계를 확인하고 기존 stage `--off`로 미사용 capacity를 종결했다. 과거 현금/재고를 합성하거나 계좌 API를 추가 호출하지 않았다. 근거 `capacity-disposition.json`.
- 이번 작업의 완료된 pytest 임시 복제본 12개에서 4.79 GiB를 회수했다. `/proc` 열린 참조가 없음을 확인했고 테스트 로그는 보존했다. 디스크 사용률 75%→72%, 가용 약 41 GiB. 운영 원장/원천은 삭제하지 않았다.
- 최초 summary_handoff 실패는 진행 중인 선행 단계에 의한 것이다. 최신 generation의 최종 strict/controller/finalization/PREOPEN은 아직 검증 중이며 이 기록으로 완료를 주장하지 않는다.


## 재개 중 발견한 후속 결함 수리

- 초기 분할수량 분석이 `execution_partition_decoded_byte_budget_exceeded`로 중단됐다. 449개 shard, 579,780,400 decoded bytes의 당일 원천 1,221건을 원본 행 참조로 순차 재읽도록 보완한다. 메모리 materialization 경계 256 MiB, shard decoded 64 MiB, 전체 IO 4 GiB를 분리하고 census/hash·파일 변경 검증을 유지한다. 원장 복제·seed 절단·승패 재라벨링은 없다. 실제 당일 검증은 producer expected/observed 단계 건수와 식별 hash 모두 일치했다(`entry-stream-source-validation.json`).
- 현재 유효 episode OFF receipt가 있으면 공동 배분뿐 아니라 그 전용 capacity도 자동 OFF 승계하도록 dispatcher를 보완한다. missing/tampered receipt는 OFF 권한이 아니다.
- archive router가 명시 원천일을 기존 wrapper의 `TARGET_DATE` 인터페이스에 전달한다. 재개 wrapper는 원천·코드·dependency 검증이 통과한 preflight를 재사용한다. 검증 실패인데 해당 세대를 읽는 machine child가 살아 있으면 재생성을 보류한다. 실행 중 원천 교체로 불필요한 전체 재계산이 발생하지 않도록 한다.
- 테스트에서 기존 finalizer의 PREOPEN/최종 detector 순서를 반대로 기대하던 오래된 문자열 assertion 1건을 발견했다. 실제 현행 계약인 prepared→실제 detector→final generation 재검증 순서로 갱신했다. 신규 재개 셸 회귀는 reusable/live-reader/missing 3경로를 실행한다.

후속 보완 재리뷰와 wrapper/수량/인계/router/finalization 회귀 **455 PASS**, compile·bash 문법·diff 검증 PASS. 현재 실행 중인 누적 기계 분석은 원 불변 v2 코드·원 preflight를 계속 소비한다. 보완 배포는 이를 교체하지 않고 이후 재개 경로만 새 release로 선택한다.

- 재개 후 `entry_cancel_wait_tuning`이 원본 참조 iterable을 list와 더하는 간접 소비자 결함을 발견했다. `itertools.chain`으로 선행/현재 원천을 합치며 기존 dedup·미분류 이력 보존을 검증했다. 첫 간접 소비자 회귀 413건 중 12건에서 별도 오프라인 초기화 결함도 드러났다.
- 보유/청산 전용 재현 interpreter가 AI 객체 초기화 중 현행 진입 정책 파일을 읽던 문제는 `initialize_entry_policy=False`를 해당 두 오프라인 경로에 명시하여 보완했다. 실시간 기본값은 그대로 True이며 보유/청산 의사결정을 대체하지 않는다. 실제 full-policy fixture 42 PASS다.
- 새 dispatcher의 keyword-only 인자를 기존 AI 초기화/상시감시 호출자가 위치 인자로 전달해 TypeError가 무시될 수 있던 연결을 수정했다. 실제 두 caller AST를 함수 signature에 bind하는 회귀를 추가했다. 동결 v4 및 실행 중 누적 분석의 계약 모듈 bytes는 보존한다.
- v5의 next_session 후보를 구 intraday v2 활성화로 넘기지 않도록 명시 거부를 추가했다. 정규 PREOPEN 활성화 경로는 그대로 유지한다. 관련 장중 인계 회귀 62 PASS, 후속 consumer/runtime/holding/분할/자동화 통합 395 PASS, compile/diff PASS다.
- 격리된 5종목 normalized callback 10,000회 부하검증에서 union p99 92.087µs, native p99 26.877µs였다. 실제 provider·주문 호출은 없으며 자연 운영 성능이나 수익 결과를 주장하지 않는다(`callback-benchmark.json`).

## 확인점 투영 성능 보완

v4 배포(`8f015957`)의 immutable 188 PASS 후 재개했으나 코드 의존성이 바뀐 preflight는 기존 기계 reader와 교체할 수 없어 wrapper가 안전하게 보류됐다. 분석 snapshot profiler에서 20개 확인점 3.816초 중 3.758초가 snapshot, 3.082초가 과거 특징 전체 재계산이었다. 단순 콜백 수집 benchmark와 실제 확인점 투영 비용은 별개다.

successor runtime/장후 공통 projector에서 native와 같은 접두·누적 배열·연산 순서로 마지막 특징만 계산하고 같은 tick의 정책들이 공유하도록 보완했다. native v4 코드/정의는 불변이다. 실제 9/22·10/7의 삼성·두산·주성·052690 총 120개 확인점 snapshot bytes가 완전히 같았고, 측정 합계 native 8.888초→successor 0.733초였다. provider/주문 호출 0회. 결손 수량/side/경계/epoch 회귀 포함 24 PASS, 계약·원장·native parity 확장 135 PASS다. 변경 코드 세대의 원천 재계산은 필요하지만 같은 내용 객체와 기존 실제 응답을 삭제/복제하지 않는다. 원 reader를 정상 중단한 후 새 preflight/선택 코드로 재개한다.

01:19에 immutable 53 PASS와 native parent/63 owner 검증 후 `5846d0c7ece047a894656452ea1fffaa89ba5314` / `operating-union-20261008-v5`를 선택했다. exact PID/start-ticks로 원 supervisor 1114905만 SIGTERM하여 committed checkpoint를 보존했다. 01:21 새 preflight와 machine child 1129893 기동을 확인했다. 완료된 자체 pytest 임시 복제본 추가 2.49 GiB를 삭제했으며 실제 원천/AI 원장/응답/로그는 보존했다. 최종 chain·기동 준비는 아직 진행 중이다.

01:22 후행 entry-split 재개 실패의 직접 원인은 정상 생성된 221 MiB JSON 보고서에 raw shard와 같은 64 MiB 상한을 적용한 reader였다(`bounded_entry_split_predecessor_required`). native 보고서 IO 경계를 512 MiB로 분리하고 읽는 중 inode/크기/mtime 변경 및 쓰기 전 전체 hash CAS를 검증한다. 중첩 refresh 전 이전 파싱 객체를 해제하고 원본 bytes의 중복 보존을 제거했다. 원천 행·경제성·수량·정책 선택/승격 조건은 변경하지 않았다. 64 MiB 초과 정상 JSON 회귀와 제한 초과 명시 실패 포함 관련 244 PASS, compile/diff PASS다.

v6(`b48093de`)의 실제 재개에서 분할수량·취소대기·initial quantity refresh가 완료됐다. 이후 병렬 Main 계산 중 wrapper의 final audit가 같은 preflight 경로를 교체하는 순서 결함을 확인했다(기계 pin `eef545...`, final `bcdc36...`). Main-only 단일 단계 대기와 terminal 검증 뒤에 final audit를 발행하도록 barrier를 추가했다. 대기 자체는 실패를 성공으로 바꾸지 않으며 별도 `--check`가 성공해야 발행한다. dispatcher·wrapper·finalization 149 PASS, compile/bash/diff PASS. 이미 교체된 현재 실행은 계산 체크포인트를 완료한 뒤 검증된 final audit를 통한 기존 closed-date recovery로 인계한다. source hash 검사를 생략하거나 실행 중 원천을 되돌리지 않는다.

01:42에 `66fce0a98b40be922bb206124489b4413dd9df67` / `operating-union-20261008-v7` 선택을 완료했다(immutable 회귀 149 PASS, 63 owner 검증). 01:44 원 machine 계산은 완료됐으나 예상한 `source_quality_preflight_changed_during_consumption`으로 실패했다. 검증된 final audit를 사용한 native closed-date recovery는 저장된 체크포인트를 재사용하여 01:46:35에 21초 만에 succeeded/issue 0으로 종료했다. 원천 manifest 62개 중 route 대상 58개 partition, 확인점 117,763건, 확정 77,903건, U 39,860건이며 주문/실제 AI 응답 수가 아니다. dispatcher 수정 전 receipt도 관리된 불변 release 코드와 원 output/input/prerequisite hash가 모두 맞을 때만 native validator에서 호환 검증한다.

v6 전체 wrapper는 rising-missed classifier의 메모리 보호 대기 300초 만료로 01:42 종료됐다. 보호조건을 완화하지 않고 v7 wrapper를 01:47에 재개했다. EOD는 원 2,626행 completed_with_warnings를 재사용했다. 아직 전체 장후·실제 보조 비교·controller/finalization/PREOPEN 완료를 주장하지 않는다. 후속 실제 AI producer는 선택된 v7에서만 발행하여 release provenance를 맞춘다.

02:04 원장 입력 전수 준비는 234,389 owner 확인점·1,171,945 owner-arm 요청, 결손 0으로 완료됐다. 내용 중복을 합친 고유 요청 777,890개 중 기존 completed 3,369·planned 774,517·reserved 4였으며 새 DB 복제 없이 공유 원장에 증분 추가했다. 이어 실제 nano 호출에서 CAUTION의 위험 근거를 `supporting_fact_ids`에 기록하는 응답을 확인했다. 기존 문구가 위험 인용의 필드를 명시하지 않아 '판정을 지지하는 사실'과 '진입을 지지하는 사실'이 혼동되는 전송 계약 결함이다. validator는 이를 그대로 제외했고 결과/예약은 원장에 보존했다.

정확한 v7 보조 supervisor PID/start-ticks/cwd를 검증하여 중단한 뒤, union 보조 v2에 supporting=ENTRY 지원, non-PASS 위험별 binding 인용=contradicting 필드, 배열 중복 금지·nonempty risk code를 명시했다. 임의 citation 이동이나 validator 완화는 하지 않았다. 전송/input/schema/binding hash가 바뀌므로 구 응답을 새 응답으로 재분류하지 않는다. 원래 `union_nonpass_risk_unbound`였던 실제 입력 12건의 새 요청을 같은 공유 원장에서 영속 예약·실제 호출·응답 보존한 결과 12/12 계약 유효(PASS 3·CAUTION 8·VETO 1)였다. 이는 응답 계약 검증이며 정책 우월/승률 증명이 아니다. `prompt-field-real-validation.json`이 원/신 request ID와 결과를 보존한다. unit 25·확장 98 PASS, compile/diff PASS 후 새 불변 배포 및 정확한 새 세대로 장후를 이어간다.
