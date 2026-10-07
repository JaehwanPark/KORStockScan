# Main AI 비교 원장 중복 제거·증분 저장 구현 검토

원천일/작업일: 2026-10-07 KST. 소유: `DirectFamilySourceRepairMainMechanisticEntry`.

## 실행 범위

사용자가 완료 검증연구의 미사용 복제본 삭제, [공통 원장 계획](../proposals/main-ai-comparison-ledger-dedup-and-incremental-storage-plan-2026-10-07.md) 구현·반복 리뷰·보완과 장후작업용 배포를 승인했다. EOD 제외 장후 중단은 계속 유효하다. 이 작업에서는 실제 provider 호출, 장후 재생성, 신규 정책 채택, Main/episode 프로세스 재기동을 수행하지 않는다. 미래 독립 탐지/기여도 전략은 구현 범위 밖이다.

## 먼저 확보한 공간

완료된 두 rehearsal/review sandbox의 source JSON 복제본 305개를 canonical 원본과 전수 SHA 대조하고 삭제했다. 820,760,576 bytes(약 0.76GiB)를 확보했다. root 권한의 읽기 전용 FD/cwd census에서 참조와 관측불가가 0이었다. 두 완료 감사 문서가 sandbox 이름을 인용하므로 디렉터리 전체를 삭제하지 않고, 감사/정책/report와 canonical 원본을 보존했다.

- [삭제 전 manifest](../../data/report/ai_comparison_store_migration/2026-10-07/duplicate-copy-dry-run.json)
- [삭제 영수증](../../data/report/ai_comparison_store_migration/2026-10-07/duplicate-copy-removal.json)

## 구현

공통 저장 형식은 `data/ai_comparison_store/v1`이다. SQLite에는 작은 참조와 상태/owner index만 보관하고, 입력·프롬프트·schema·설정·응답은 내용 hash로 공유하는 불변 압축 pack에 저장한다. pack 최대 크기는 16MiB이며 fsync 뒤 metadata 참조를 commit한다. 정책 버전마다 원장 본문을 새로 복사하지 않는다. 새 디렉터리는 Git 산출물 제외에 추가했다.

공통 장후 CLI가 storage adapter로 prepare/calls/auxiliary를 전달한다. frozen v3/v4 전략·registry·runtime 코드 bytes는 유지했다. 원 적격 전수×5 arm, primary와 raw PASS 누적 승률·동률·scope carry가 유지된다. v3의 selected/baseline과 v4의 consumed-version 추가 비교 범위도 구분했다. 불변 요청 조립 closure, compact owner/input refs, 같은 partition의 projection/request refs 재사용, immutable response/label/validation revision과 partition 집계를 구현했다.

같은 내용의 source인지 내용 hash를 다시 확인하는 비용은 남는다. source 정정 시 더 좁은 segment 증거가 없는 native session partition은 보수적으로 재투영한다. 이를 전체 CPU/I/O 재생 비용 0으로 주장하지 않는다. 같은 전송 요청의 label-only 정정과 새 보고일은 실제 응답을 공유한다. 다른 prompt·model·phase·복합 입력은 다른 요청이며 quota는 `None`이다.

## 이관·전수 검증

| 항목 | 결과 |
| --- | ---: |
| 구 v3 요청/owner | 579,437 / 580,035 |
| 구 v4 요청/owner | 579,442 / 580,040 |
| 공통 고유 요청 | 579,442 |
| 완료 응답 보유 요청 | 4,626 |
| 미호출 요청 | 574,812 |
| 불확실 예약 | 4 |
| 검증한 불변 객체 | 921,407 |
| 실제 provider 호출 | 0 |

각 legacy request를 조립한 전체 본문과 원 envelope를 전수 대조했다. 원 ID/별칭·원 응답·outcome·owner를 보존했다. v3 reserved/v4 planned 4건은 공통 reserved로 유지했다. 29행의 legacy durable response journal도 대조했고, 실제 응답 ID 기준 attempt 4,626개와 불확실 attempt 4개를 분리했다. 전체 객체 hash와 SQLite integrity, alias·요청 객체·attempt·generation owner 참조를 검증했다.

- [이관 영수증](../../data/ai_comparison_store/v1/migration-receipt.json)
- [전수 검증](../../data/ai_comparison_store/v1/verification-receipt.json)
- [증분 시나리오 계측](../../data/report/ai_comparison_store_migration/2026-10-07/incremental-benchmark.json)
- [기존 적용 정책 검증](../../data/report/ai_comparison_store_migration/2026-10-07/active-policy-before.json)

격리 계측에서 동일 자료의 새 보고일은 request/member/partition 증가 0(작은 generation 영수증 1개), 신규 확인점은 5 arm 요청 5개만 증가, label-only 정정은 요청 증가 0이었다. prompt 변경과 복합 입력 변경은 각각 해당 요청 1개만 추가했다. 이는 저장 계약 fixture이며 후속 독립 탐지 정책 구현이나 실제 AI 결과를 뜻하지 않는다.

## 리뷰·수정·재검증

- 응답 수신 후 metadata commit 전 중단: transport thread가 응답을 durable landing으로 먼저 저장하고, pack→journal→metadata 순서로 회복한다.
- 불확실 예약의 미호출 역행: 공통+v3+v4 OS lock과 CAS 예약으로 방지했다. timeout의 오류 record를 선택된 실제 응답으로 저장하지 않는다.
- 늦은 응답·복수 응답: 모든 기록을 보존하며 첫 durable 실제 응답을 유지한다. 과거 snapshot은 바꾸지 않는다. 기존 legacy 선택은 owner별 참조로 보존한다.
- 준비 분모 축소: 입력 생성 이전에 native population에서 독립 expected census를 봉인한다. 누락·변경된 입력은 호출/발행 전에 실패한다.
- v3 비교 범위 확대 결함: v4 consumed-version 규칙을 v3 fallback에 넣지 않도록 수정했다.
- 중복 native point: native의 첫 canonical point 처리와 동일하게 중복을 제거하고 예상 5 arm을 유지한다.
- 구 worker 재진입: cutover pointer만으로 호출을 열지 않는다. 구 SQLite 경로를 tombstone 디렉터리로 막은 뒤 공통 writer를 허용한다.
- rollback 상태 유실: 현재 공통 원장에서 최신 응답/예약을 구 native 형식으로 export하고 reader로 확인했다. 과거 DB를 되살려 재호출하지 않는다.
- 검증 결과와 호출 완료 혼동: validator version별 별도 validation 객체와 comparison revision을 보존한다. owner/고유 request/실제 attempt 계수를 분리한다.

작업본 관련 회귀 148건, 후속 저장/adapter 대상 21건, 최종 immutable 배포본의 전체 관련 회귀 **150건**이 통과했다(중복 포함, 합산하지 않음). compile 및 diff 검사를 통과했다. 실제 v4 publication fixture를 native loader로 검증하고 이후 mutable census 변화에도 frozen publication이 유지됨을 확인했다. 검토한 범위의 미해결 코드 결함은 없다. immutable 배포본 검증과 실제 구 본문 회수 결과는 아래와 같다.

## 배포·공간 회수 인계

L0~L6를 완료했다. 배포 릴리스는 `/home/ubuntu/KORStockScan-runtime-releases/shared-ai-ledger-20261007-v1`, 코드 commit은 `1cfb0fa41be840b033f8c82706472556a86aa18b`이다. 최종 immutable 회귀 150 PASS 후 selector를 전환했고 router의 10/7 postclose print-plan도 이 릴리스를 가리킨다. common pointer의 writer 전환과 두 legacy DB 경로의 tombstone 차단을 확인했다. 실제 provider 호출은 0이다.

삭제 직전 전체 DB 해시·inode와 root FD census를 재검증했다. 대상 참조/관측불가는 0이었고, 구 DB 2개와 WAL/SHM 4개에서 11,755,053,056 bytes를 회수했다. 기존 frozen actual-response export·원 tick/분봉·정책 자료는 보존했다. 새 store의 실제 할당은 1,418,067,968 bytes(1.32GiB)로, 구 DB 10.95GiB 대비 **87.936% 감소**했다.

이번 실행에서 완료된 pytest 격리 환경 3개도 참조 확인 후 제거했다(2,657파일, 421,920,768 bytes). 과거 pytest 환경은 건드리지 않았다. 최종 `df`는 **72% 사용, 가용 44,699,258,880 bytes(41.6GiB)**이며, 조사 시작 시 79%·가용 33,614,016,512 bytes 대비 실측 순증은 약 10.3GiB다. 이 값은 공통 store·릴리스 신규 생성과 동시 writer의 증가까지 반영한 filesystem 수치다.

Main PID `1074119`와 기존 적용 bundle/family hash는 동일하다. 새 릴리스는 장후용으로 선택했으며 현재 Main PID가 새 코드를 소비했다고 표시하지 않았다. 보류한 cron 5개 hash와 disabled/inactive 최종 갱신 timer를 재확인했다. **L7 장후 재개는 실행하지 않았고 사용자 별도 지시를 기다린다.** 장후 전체 완료나 내일 정책 준비 완료로 표시하지 않는다.

- [최종 인계 영수증](../../data/report/ai_comparison_store_migration/2026-10-07/completion-receipt.json)
- [immutable 검증 로그](../../data/report/ai_comparison_store_migration/2026-10-07/immutable-tests.log)
- [구 DB 삭제 전 census](../../data/ai_comparison_store/v1/legacy-retirement-dry-run.json), [회수 영수증](../../data/ai_comparison_store/v1/legacy-retirement-removal.json)
- [완료 검증 임시환경 삭제](../../data/report/ai_comparison_store_migration/2026-10-07/validation-temp-cleanup-removal.json)

문서의 기존 실행 owner는 한 개이며 print-only parser를 통과했다. 외부 Project/Calendar sync, 장후 replay, 실제 provider 비교, 봇 재기동은 이 검증에 포함하지 않았다. 새 adapter의 자연 장후 소비와 실제 신규 응답 축적은 별도 재개 후 확인할 사항이다.
