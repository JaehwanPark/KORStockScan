# 복수정책·추가 8개 패턴과 공통 원장 구현 재점검

## 범위와 기준

사용자는 두 구현계획 대비 코드 점검·보완·반복 리뷰와 장후용 배포를 승인했다. 기준 HEAD는 `c9620dd1`이며 실제 장후 선택 release는 `shared-ai-ledger-20261007-v2` / `46292984`였다. Main PID 1074119는 `main-eight-typed-paths-20261007-v3`에서 실행 중이다. EOD 제외 장후 보류는 유지한다. 실 provider, 전수 장후 재생, 정책 활성화 또는 Main 재기동을 이번 검증에 포함하지 않는다.

- [전 종목 복수정책 계획](../proposals/main-all-scope-registered-multi-policy-implementation-plan-2026-10-07.md)
- [추가 8개 등록 계획](../proposals/main-additional-eight-pattern-registration-after-multi-policy-implementation-plan-2026-10-07.md)
- [공통 원장 구현·이관 기록](main-ai-comparison-ledger-implementation-review-2026-10-07.md)
- [이번 실제 기준 영수증](../../data/report/multi-policy-ledger-integration-review/2026-10-07/baseline.json)

별도 독립 탐지 successor 계획의 전체 운용 목록/복합 AI 입력/기여도 선택은 현재 범위에 넣지 않는다. v3/v4의 선택 portfolio·primary 1개·누적 raw 승률·동률 현행 유지 계약을 보존한다. 새로운 최소 표본/EV/성공 보존 gate를 추가하지 않는다.

## 계획 대비 구현 대조

| 계획 요건 | 실제 소유·점검 결과 |
| --- | --- |
| P1/R1 등록 정의·유한 조합 | `reversal_registered_catalog`의 10개 유형과 `reversal_path_catalog`의 정확 8개 definition SHA/고정 baseline 조합 유지. 기존 portfolio 목록 포함을 회귀한다. 매 장후 새 grid를 생성하지 않는다. |
| P2/R2 구버전 호환·전체 scope | v3/v4 native reader와 별도 catalog/runtime. 48셀·128경로, 5고정/일반 분리, PRE/REGULAR/AFTER 및 route coverage를 읽기 검증했다. 현재 family source 검증 PASS. |
| P2/R3 특징·확인 시점 | 공유 window, false→true momentum/breakout, 첫 1초 후 hold, 최대 120초 retest, HA FIRST. 기존 source/quote/TTL/경계·가격대 전환 회귀를 재실행한다. |
| P3/R5 기계 비교·선택 | native population에서 등록 단독/고정 조합·incumbent·consumed version을 비교한다. 30분·비용 후 +0.4%·soft -3% 선도달, Fraction W/(W+F), U 별도, 동률 현행 유지. 과거 전체 52 partition의 비교 hash `efebb567d8424f2212cc81f636abdd0cf14649653e73f3a25d27a28efa1eb5bb`를 동결 증거로 사용한다. 새 전수 재생을 실행하지 않았다. |
| R3/R4 typed phase·실제 입력 | 8개 각각의 확인점과 5개 arm의 요청을 원 `PC.request`와 공통 원장 재구성 결과로 대조한다. HA FIRST 포함 6 phase의 native stage/source 검증을 fixture에서 완료한다. 실제 전략 연구의 8/8 parity는 이전 고정 코드/증거이며 이번 작은 fixture 성과가 아니다. |
| P4/R5 보조 대상 | selected/baseline, v4의 consumed-version primary만 대상. U는 제외되고 미선택 branch는 호출 대상이 아니다. v3의 기존 selected/baseline 비교 분모를 보존한다. |
| P4/R5 공통 저장 | v3/v4 동일 요청의 실제 응답 1회 재사용, 비교 generation 별도. 새 날짜·label 정정·재준비는 요청 본문/응답 재복제 없이 참조 재사용. quota None/동시 4/불확실 예약 유지. |
| P4/R6 expected·발행 | 독립 population 예상 집합→입력 refs v2→DB owner/arm/request/outcome 대사→불변 응답 선택→기계·보조 쌍 발행. 아래 F1~F5를 보완했다. |
| P5/R6 장중 소비 | 버전 dispatcher→claim→typed input→provider 후 family/TTL 재검증→단일 intent/감시·native loader 연결 회귀. 이번 수정은 장후 adapter/공통 CLI에 한정하며 고정 runtime/kernel/catalog/prompt bytes를 보존한다. |
| P6/R7 반복 리뷰 | 데이터 동일성·partial/전 VETO·누락/치환·동시 재준비·구버전 reader·호출 없는 CLI 회귀와 compile/diff/문서 parser. 발견된 test 환경 결합도 수정했다. |
| P7/R8 운영 인계 | 장후 immutable release 선택까지 이번 작업. 장후 재개·새 정책 비교/선정·PREOPEN 준비/PID 소비는 보류 중이며 완료로 주장하지 않는다. |

재점검 당시 공통 요청 579,442개, 완료 4,626개, planned 574,812개, reserved 4개, immutable 객체 921,407개였다. 신규 8개는 등록되어 있지만 활성 family의 선택 경로는 모두 0개다. 등록 실패나 구현 누락이 아니며 이번에 강제 OR하거나 추가 호출 대상으로 바꾸지 않는다.

## 발견·수정·재리뷰

| ID | 결함 | 수정과 회귀 |
| --- | --- | --- |
| F1 | 보조 비교 미완료여도 기존 branch 문구가 있으면 새 기계 조합/primary 순위를 발행 가능 | gap이 있는 선택 branch는 이전 기계 payload·branch/priority metric·보조 payload 전체를 carry. machine winner/publishable hash와 branch 사유를 기록한다. 과거 문구가 있는 부분 완료 반례를 재현했다. |
| F2 | count 대사만으로는 같은 개수의 다른 request/owner 연결을 호출 전에 식별하지 못함 | refs v2에 arm별 request ID를 보존하고 population expected 봉인 후 DB의 정확 comparison/opportunity/arm/request/outcome을 대사. 누락 및 같은 개수 치환은 예약·집계 전에 거부한다. 전체 본문은 복사하지 않는다. |
| F3 | 공통 CLI에 준비 전용 모드가 없고 `--evaluate-only`가 calls/machine에서 무시됨 | 공통 adapter의 `prepare-inputs`를 노출하고 비지원 evaluate-only 조합은 side effect 전에 명시 거부. 구 native DB 직접 writer는 tombstone으로 계속 막힌다. |
| F4 | 보고서가 실제 comparison이 없는 branch의 미선택/no-primary 상태를 생략 | 전체 등록/적용 branch를 scope별 상태 표로 출력. incomplete/completed-no-pass와 구분하며 provider 대상은 늘리지 않는다. |
| F5 | 응답 snapshot lock 종료 후 mutable census를 복사하면 다음 준비의 증빙과 혼합 가능 | census 읽기·연결 대사·snapshot·발행용 receipt 동결을 동일 lock 안으로 이동. 이후 census 변경에도 native source 검증을 통과하는 반례를 추가했다. |
| F6 | cron 로그 테스트 3개가 서버의 현재 중단된 실제 crontab을 읽어 설치되지 않은 것으로 판정 | 해당 로그/rotation/status fixture에 설치된 cron을 명시했다. 실제 cron/운영 detector 로직은 변경하지 않았다. |

신규 코드는 기존 `src/engine/scalping` adapter/CLI 안에 두고 테스트도 기존 `src/tests` 파일을 확장했다. `src/engine` root 신설, Kiwoom API 변경, 주문/수량/자본/hard safety 변경은 없다. 구 고정 family를 새 코드에 맞추려고 hash 검증을 느슨하게 하지 않는다.

## 실행·호환·후속 경계

운영 장후는 기존 handoff의 `scalping.continuous_reversal_postclose --mode machine|auxiliary`를 사용한다. 보조 단계는 common prepare→calls→report를 호출한다. 준비만 필요할 때 같은 CLI의 `--mode prepare-inputs`를 사용한다. `--evaluate-only`는 auxiliary 집계 전용이며 기계 격리 연구에는 별도 data root가 필요하다. 원 native v3/v4 CLI로 폐기 원장을 재생성하지 않는다.

구 shared 입력 refs v1은 이미 발행된 불변 증거로 보존한다. 재개 시 prepare가 작은 refs v2를 만들고 기존 DB 요청·응답·예약을 그대로 연결한다. v1만 있는 상태의 단독 calls는 `shared_input_refs_require_preparation`으로 거부한다. 이관/import를 다시 실행하거나 대형 v3/v4 SQLite를 다시 만들 필요가 없다. 입력 source의 세밀한 producer 봉인 segment가 없는 한 해당 native session partition의 보수적인 내용 해시/재투영 비용은 남는다.

현재 root/등록/family 고정 모듈 변경은 없으며 source validator가 읽는 기존 코드 hash 전부를 보존한다. 선택 release와 실제 Main PID는 분리해 기록한다. 10/7 보류 cron 5개와 최종 갱신 timer를 복원하지 않는다. EOD도 재실행하지 않는다. 이번 검증의 provider transport는 전부 fixture이고 실제 호출은 0회다.

최종 검증·배포 결과는 아래에 추가한다. 자연 장후 완료와 새로운 운영 성과는 이 코드 리뷰로 대체하지 않는다.

## 코드 검증 종결

1차 확장 회귀는 681 PASS/3 FAIL이었다. 세 실패는 F6의 설치된 cron fixture 결손이며, 운영 중단 설정을 고치지 않고 테스트를 격리한 뒤 해당 60개 회귀를 통과했다. 재리뷰 후 최종 16개 suite **684 PASS**. 신규 공통 원장 연결 suite는 29 PASS이며 이 수는 684에 포함된다. 원 요청 bytes의 8개 유형별 5 arm 대조, v3/v4 고유 요청 5개/실제 fixture 호출 5회 공유, timeout 미재호출, 누락/동일 개수 치환의 예약 0회, 전 VETO·partial carry·snapshot 변경/label revision·native reader를 검증했다.

compileall·`git diff --check` PASS, 문서 53개 로컬 링크 유효, print-only parser에서 current owner 1개를 확인했다. [최종 workspace 테스트](../../data/report/multi-policy-ledger-integration-review/2026-10-07/final-workspace-tests.log)와 [cron 재검증](../../data/report/multi-policy-ledger-integration-review/2026-10-07/cron-regression.log)을 보존한다. 검토 범위 내 미해결 finding은 없다. 실제 AI/장후 재생 및 자연 신호·수익 검증을 실행하지 않은 한계는 유지한다.

## 배포 완료

코드 `1cb82b0278223ebce3e7cd88dc1a28880dd0b6f8`를 `multi-policy-ledger-review-20261007-v1` 불변 release로 배포했다. 해당 release에서 동일 16개 suite **684 PASS**, 기존 활성 bundle `69caaf00f2a0475e0290de0b239f28975333782429a62f4e238c8d0ae96f5d78`의 native source 검증 PASS. 별도 서비스 정책 pin 186개도 유효하다. selected router의 postclose 10/7 계획이 새 release를 가리키는 것을 read-only `--print-plan`으로 확인했다.

Main PID 1074119/cwd와 활성 family `ed50d100aef3d66361c83bea53441ae0b4461b8ac98fdbcb87346cc9790a324d`는 그대로다. 새 release의 Main PID 소비는 false로 표시했다. 공통 requests/members/attempts/objects/generations와 writer epoch는 기준 영수증과 같으며 실제 추가 호출은 0회다. cron 5개 보류 및 timer disabled/inactive를 유지했고 장후를 재개하지 않았다.

이번 완료된 테스트 디렉터리 3개에서 8,476파일·할당 **1,105,022,976 bytes(1.03GiB)**를 정리했다. root 권한의 읽기 전용 `/proc` 참조 검사에서 사용 중/관측 불가 0, 삭제 전 파일 hash를 대사했다. 원천·연구·실제 응답과 오래된 별도 테스트 디렉터리는 보존했다. 최종 디스크 사용률은 약 72%, 여유 약 41.5GiB다.

[배포 선택](../../data/report/multi-policy-ledger-integration-review/2026-10-07/deployment-selection.json), [immutable 테스트](../../data/report/multi-policy-ledger-integration-review/2026-10-07/immutable-tests.log), [장후 경로](../../data/report/multi-policy-ledger-integration-review/2026-10-07/postclose-route.json), [최종 검증·중단 유지 영수증](../../data/report/multi-policy-ledger-integration-review/2026-10-07/completion.json)이 현재 증거다. 재개 후 새 생성물/선정/strict-controller-PREOPEN 검증은 남아 있으며 배포 성공과 구분한다.
