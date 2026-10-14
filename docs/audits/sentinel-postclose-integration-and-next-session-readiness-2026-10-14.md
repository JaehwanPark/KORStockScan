# 장후 종료 후 계산 수정본 통합 및 다음날 준비

현재 상태는 **통합 코드 검증 완료, 장후 전체 종료 대기, 미배포**다. 사용자가 승인한 순서는 다른 세션의 장후 작업 완전 종료 → 최종 계산 수정본 `a179bb42d` 통합배포 → 다음 영업일 정상 기동 준비다. 추가 승인 대기가 아니다. 이 기록의 source/publication은 `2026-10-14`, 다음 영업일은 `2026-10-15`다.

## 통합 범위와 코드 검증

첫 통합본 `4c4996d2aa44686f18aab19b0ecc7601be1cd15f`는 장후 복구본 `8a252a6e9`와 계산 수정본의 문서 종결 commit `96076385b`를 병합했다. `a179bb42d`의 Sentinel 계산/정확한 parser-owner migration 및 시험 4파일을 byte 동일하게 보존하고, 다른 세션의 native ancestry·보조 membership·최종 handoff 복구 6파일도 보존했다. 문서 충돌은 원 계산 수정 인계와 장후 복구 인계를 모두 유지해 해소했다. 이후 다른 세션이 선택한 `bdf6ffe6a`의 문서·activation-origin 인계도 통합한다. 최종 build와 실제 선택은 각각 새 영수증으로 구분한다.

12개 관련 suite의 최초 실행은 1,102 PASS와 격리 worktree의 불변 fixture 부재 3건이었다. 필요한 5개 fixture의 원 bytes를 검증·복사한 뒤 해당 3건이 PASS했다. 따라서 서로 다른 1,105개 시험이 모두 통과했다. 원 실패 로그를 보존하며 최초 명령이 성공했다고 기록하지 않는다. 별도 독립 리뷰 4개 suite의 297 PASS는 중복 수이므로 합산하지 않는다. Python compile, wrapper `bash -n`, diff 검사와 코드 리뷰의 미해결 결함은 없다. 실제 provider·주문·Telegram을 호출하지 않았다.

증거는 [통합 build](../../tmp/sentinel-integrated-postclose-20261014/integration-build.json), [통합 검증](../../tmp/sentinel-integrated-postclose-20261014/integration-static-validation.json), [독립 코드 리뷰](../../tmp/sentinel-integrated-postclose-20261014/source-integration-independent-review.json)에 보존한다. Main/manual custody, 매매 가드, 기계/보조 판단값, native 5초 계약은 변경하지 않는다.

## 배포와 정책 준비의 경계

다른 세션이 소유한 정확일자 Main 성공·전체 strict PASS·독립 producer를 요구하는 controller DONE·tuning 성공·다음날 준비와 실제 actor/lock 종료를 확인하기 전에는 selector를 전환하지 않는다. 이후에도 현재 selector가 후보의 Git 조상인지 재검증한다. 장후 owner가 추가 수리를 배포했다면 그 코드를 먼저 통합·리뷰한다.

전환은 검토된 정지 배포 도구로 기존 selector의 원 bytes와 정책·종료 영수증을 보존한 뒤 수행한다. 새 selector의 과거 PID/transition 필드를 현재 소비 증거로 재사용하지 않는다. Main은 정지 상태를 유지하며 새 릴리스의 `actual_pid_consumed=false`를 기록한다. 관련 도구의 [입력 계약](../../tmp/sentinel-integrated-postclose-20261014/stopped-selector-input-contract.md)과 [root 검증](../../tmp/sentinel-integrated-postclose-20261014/selector-publisher-root-review.json)을 따르며 실제 발행 결과는 별도 영수증으로 확인한다.

다음날 후보의 코드 결속만 새 릴리스로 갱신하고 기계 membership·threshold·보조 입력/응답·선택값과 현재 정책 pointer를 보존한다. 원 current 정책 `99c894cb...`의 33개 native 파일과 정확히 일치하는 불변 `bd40c7f12`를 full parent validator로 검증했다. 이 검증은 code-handoff 파일 읽기를 차단한 상태에서도 통과했다. 새 후보의 명시적 activation-parent proof가 정상 PREOPEN에서 동일 원 정책 조상을 검증한다.

필요한 직접 downstream은 source14 prompt consumer → summary handoff → 전체 controller/strict → target15 prepare/verify다. 완료된 기계·보조 정책 계산을 다시 실행하지 않는다. 원 source·정책·실패 이력과 원 producer 영수증을 보존한다. [재결속 절차 리뷰](../../tmp/sentinel-integrated-postclose-20261014/rebind-helper-independent-review.json)는 20개 격리 mock을 통과했으며 실제 실행 증거를 대신하지 않는다.

현행 `stage_code_refresh`의 미래 target 계약은 보존한다. 장후 종료가 자정을 넘겨 기존 [준비 자동화](../../src/engine/automation/next_preopen_readiness.py)에 `stopped_postclose_candidate_rebind`를 추가했다. 실제 대상 거래일의 07:35 전, source/publication 전일, 정확한 다음 거래일, Main/supervisor 정지·정상 장후 격리·미시도 PREOPEN·현재 정책 미활성·전체 controller/strict/stage 종료를 모두 요구한다. release/PREOPEN/producer/publisher 잠금의 inode와 선택/원 후보/현재 pointer/원천의 해시를 재검증하고 기존 native 불변 builder·원 정책 조상 full validation·판단값 equality만 사용한다. 원 후보의 기존 code-refresh 조상도 보존한다. 발행 후 검사 실패는 이미 발행된 successor를 명시하며 원 파일을 덮어써 되돌리지 않는다.

native 정책 33파일은 그대로이며, 기존 준비 자동화 15개 top-level 정의의 AST도 보존했다. 새 API는 현재 pointer·활성화·기동·provider·주문을 수행하지 않는다. 기계/보조 producer의 dependency에 준비 자동화 파일이 포함되지 않으므로 정책 계산을 재실행할 source 변경을 도입하지 않는다. retained immutable release의 원 단계 코드를 검증하는 기존 계약은 계속 적용한다. 표적 67개 및 독립 3-suite **130개** 시험이 통과했으며 67은 130에 포함되므로 합산하지 않는다. [자체 리뷰](../../tmp/sentinel-integrated-postclose-20261014/stopped-postclose-same-day-rebind-self-review.json), [root 리뷰](../../tmp/sentinel-integrated-postclose-20261014/same-day-rebind-root-source-review.json), [독립 리뷰](../../tmp/sentinel-integrated-postclose-20261014/stopped-readiness-independent-review.json)에 source/시험 해시를 보존한다. 날짜 경계는 [원 진단](../../tmp/sentinel-integrated-postclose-20261014/same-day-rebind-boundary-readonly-review.json)과 구분하며, 이 코드 검증은 실제 후보 발행이나 준비 성공을 뜻하지 않는다.

## 원천 세대와 성능 수용

20:59의 승인된 raw-row 제외는 식별된 결함 15행을 제거하면서 10/14 raw 파일을 교체했다. 기존 summary/cache는 그 이전 inode/offset을 가리키므로 source-prefix 검증 실패가 정당하다. 이를 빈 입력이나 성공으로 바꾸지 않는다. 원 derived artifacts를 보존하고 기존 native API로 정확일자 summary/cache를 명시적으로 재구축하는 절차를 검토했다. 이 작업은 다른 세션 종료 후 수행하며 실제 보고서 계산과 별도다.

[원천 세대 분석](../../tmp/sentinel-integrated-postclose-20261014/postclose-source-generation-review.json), [제한된 재구축 계획](../../tmp/sentinel-integrated-postclose-20261014/source-rebuild-plan.json), [독립 절차 리뷰](../../tmp/sentinel-integrated-postclose-20261014/scoped-source-rebuild-independent-review.json)를 보존한다. 원 source bytes·삭제행 제외 manifest·코드·선택 해시를 고정하고 native lock과 총 600초 한도를 사용한다. 실제 CLI 130초, observer 40초, 전체 180초의 수용 한도와 자연 3슬롯 검증은 늘리지 않는다.

## 최종 수용과 남은 자연 실행

설치된 예약은 10/15 **05:35 finalization, 07:35 PREOPEN, 07:55 Main 정상 기동**이다. 현재의 배포 준비와 `prepared_verified`는 향후 PREOPEN 적용, 새 PID 소비, 자연 주문/체결/terminal 또는 비용 후 손익을 대신하지 않는다. 미래 예약 실행은 due 전까지 `not_yet_due`다.

최종 결과에는 선택 commit/root, 원 정책 보존, 정확 source14/target15 준비 및 독립 verify, 설치 cron/router, Main 정지·startup custody를 함께 기록한다. 기존 `DirectFamilyPreopenPolicyHandoff`, `NonfixedDispatchReadinessReview1012`, `AuxiliaryCircuitRecoveryRepair1012`의 소유권과 Acceptance/History를 보존한다. 문서는 print-only parser만 검증하고 외부 Project/Calendar 동기화는 실행하지 않는다.
