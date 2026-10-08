# Main 시간외 등록·상태 보완 구현 검토 — 2026-10-08

## P0 경로 복구

사용자는 구현·반복 리뷰·배포·재기동을 승인했다. 원 계획의 연구 당시 미승인 문구는 당시 이력이다. 실행 owner는 `DirectFamilySourceRepairMainMechanisticEntry`를 유지한다.

- `p0-before.json`: 선택 v3의 기록 PID 1324165는 현재 `/proc`에 없다. 실제 launch cwd에서 활성 bundle의 `data/...` 원천 경로 결손을 재현했다. 과거 PID 영수증을 현재 가동으로 표시하지 않는다.
- 명시 data root의 context-local 경로 resolver를 공통 native reader에 적용했다. hash/cache/read/dependency는 같은 절대 lexical 경로를 사용하고 실제 symlink 목적지·stat 변경을 검출한다. 상대 탈출/미지원 접두/외부 링크·누락은 차단한다. 원 봉인 보고서는 수정하지 않는다.
- 정책 payload·bundle·18개 판정 code pin은 변경하지 않았다. 이 최소 수정에는 v5 same-day successor가 필요하지 않다. dispatcher/activation/PID 소비는 동일 anchor reader를 사용하며 새 source receipt는 절대경로로 기록한다.
- launcher는 실제 `src` cwd에서 native `--validate-current`를 실행한다. bootstrap 성공과 별개인 `launch_loader` 상태를 출력한다. provider/order 호출은 없다.
- 이미 종료된 이전 PID의 경우 명시 `--previous-stopped` 인계를 지원한다. 이전 동일 날짜의 소비 영수증·기동 원천·정책·이전 immutable release를 검증하고 PID 부재를 재검사한다. 이를 현재 PID 소비로 표시하지 않는다. 기존 살아 있는 PID 인계는 원 검사를 유지한다.

실제 동일 bundle `cdacf6eed9d77e95d0bdf1a417ec2549323ea2491b91e41b8f948b900434895f`의 4개 cwd 검증은 모두 통과했다. 첫 load 약 1.98초, 재사용 약 .06초이며 731개 dependency를 추적한다. [P0 원천 영수증](../../data/report/pre-after-remediation/2026-10-08/p0-before.json), [4개 cwd 검증](../../data/report/pre-after-remediation/2026-10-08/p0-four-cwd.json).

기존 native/운용/인계/보조 회귀 172 PASS, 추가 anchor 회귀 5 PASS. 후속 인계/기존 path 회귀 136 PASS, 종료 PID 인계 4 PASS, bootstrap/router 117 PASS. compile·bash -n·diff·문서 parser(현행 owner 1개) 통과. P0는 `40d27c58539f83864f8c35cfc621a0ec99094269` / `pre-after-source-anchor-20261008-v1`로 배포했고 08:59:31 PID 5364의 bootstrap·기계 128 scope 소비를 확인했다. 신규 13개는 아래의 별도 변경 단위다. 이 문서는 실제 주문·수익 또는 전체 구현 완료의 영수증이 아니다.


## 신규 등록·기여도·상태 소비 구현

- 동결된 v4/v5 catalog·FSM·입력·코드 pin을 유지하고 `scalping` 소유의 v6 successor를 추가했다. 13개 정의는 PRE=NXT `_NX`, AFTER=SOR `_AL`의 연구 batch와 hash가 일치한다. FIRST 5, PEAK 2, MOMENTUM 3, RETEST_PEAK 1, RETEST_FIRST 2를 독립 탐지하며 30/120초·0/0.2% 경계를 각 정의로 검증한다.
- 공통 보조 입력은 정확한 확인 ask·native 순번·모든 매칭 신호를 결속한다. PEAK에 가짜 touch를 만들지 않는다. 기존 신호/원장 opportunity namespace와 영속 outbox는 유지하며 같은 지점의 두 번째 claim을 만들지 않는다. Kiwoom 파일 변경은 normalized callback dispatcher import 한 줄이며 API 요청·FID·응답 파서는 변경하지 않았다.
- PA11은 탐지기 당시의 `:missing` 결과와 root 상태에서 TRUE/FALSE/UNKNOWN을 직접 전달한다. 정상 조건 미충족을 UNKNOWN으로 재계산하지 않으며 원천 단절·필수 값 결손·과부하는 UNKNOWN으로 유지한다. 탐지 확인점과 승패 라벨을 수정하지 않는다.
- 명시 ADD intake는 정확 부모 CAS·13개 정의·원천 hash를 검증하고 멱등 소비한다. tmp의 작은 연구 코드·라벨·봉 입력은 content-addressed 보존하고 공유 누적 raw는 원 경로/hash 참조로 유지한다. 다음 장후 producer가 batch를 manifest에 반영한다. 정규 보조 arm 및 별도 등록된 보조 문구/독립 측정 scope를 승계한다.
- 신규 source-day 100회와 불확실 예약은 그대로다. v2 후보를 v3 입력에 재사용하지 않으며 비교 미완료는 초기 등록과 별도 표시한다. 후보 프롬프트를 자동 발명하거나 현재 날짜로 과거 호출 예산을 리셋하지 않는다. 등록 발행도 bounded campaign·call-freeze·실제 응답만 포함한 호환 출력으로 인계한다.
- 상태는 등록/채택 근거/비교/발행/준비/활성/검증/PID/hold를 구분한다. 계약 128 scope, 실제 운용 48 scope, PID가 로드한 수, 실제 판정 관측 수를 분리한다. PID 재사용·조회 도중 교체·준비 PASS+loader 오류를 정상 소비로 합치지 않는다. checklist marker는 과거 snapshot으로 보존한다.

리뷰에서 v6 후속 장후 분기, 증빙 scope 비교, 보조 rollback의 입력 버전, 기존 보조 문구 승계, 준비 상태와 PID 상태의 혼합을 찾아 보완했다. 관련 리뷰 범위의 미해결 코드 결함은 0이다. 기존 실제 주문·체결·실현 성과를 새 코드 검증으로 주장하지 않는다.

## 검증과 발행 경계

- [최종 혼합 누적 재생](../../data/report/pre-after-remediation/2026-10-08/extended-contribution-parity.json): 15개 frozen partition, 1,037,191행, 신규 확인점 7,641건, 13개 모두 missing/extra 0. 구 정책과 함께 만든 typed 요청도 검증했다. provider 호출 0.
- branch별 기여 집계에는 중복이 포함된다. 독점 입증 WIN 983 / FAIL_TIMEOUT 534 / U 2,847, 기존과 중복 WIN 51 / FAIL 23 / U 3,032, 독점 미입증 WIN 139 / FAIL 15 / U 17이다. UNKNOWN에서 발생한 139승을 독점 승리로 올리지 않았다. 이 수는 주문 수가 아니다.
- [부하 비교](../../data/report/pre-after-remediation/2026-10-08/load-check.json): 같은 삼성 AFTER 15,000행에서 Python tracing 포함 기존 9,264행/초, 확장 3,451행/초, p99 0.263→0.933ms, peak Python memory 632,446→540,853bytes. 확장 비용은 증가하므로 모든 실시간 종목의 최악 부하를 입증한 결과로 해석하지 않는다. callback에 디스크/provider 호출을 추가하지 않았다.
- 회귀 그룹: 판정/보조 전송/제출 증빙/원장 445 PASS; 확장/기존 path/운용/semantic/checklist 303 PASS; bootstrap/router/PREOPEN/handoff 195 PASS; summary/handoff 추가 170 PASS; 보조 승계·신규 34 PASS, 마지막 실제 callback/claim 신규 22 PASS. 그룹 간 중복이 있으므로 독립 테스트 수로 합산하지 않는다.
- compile, `bash -n`, `git diff --check`, print-only backlog parser를 검사한다. 외부 Project/Calendar 동기화·AI 실호출·EOD/전체 장후 재실행은 수행하지 않았다.
- [등록 intake 영수증](../../data/report/pre-after-remediation/2026-10-08/registration-intake.json): 기존 active bundle 유지, 신규 13개는 `pending_next_session_publication`, 대상 **2026-10-12**. 코드 배포/재기동이 신규 13개 정책의 당일 활성화를 뜻하지 않는다. 장후 발행·10/12 기동 시 정확 bundle/PID 소비는 현행 owner의 후속 확인이다.

통합 배포·기동의 최종 영수증은 `data/report/pre-after-remediation/2026-10-08/deployment-final.json`에 기록한다. 일일 owner는 유지하며 이번 문서의 최종 수정 후 immutable 인계를 준비한다.
