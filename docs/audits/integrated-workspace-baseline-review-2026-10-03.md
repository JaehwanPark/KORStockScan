# 2026-10-03 기존 작업본 통합 기준선 리뷰 및 배포

## 목적과 권한

사용자는 기존 작업본을 먼저 커밋·배포하고 깨끗한 기준선에서 Main 기계·보조 정책 원천 보완을 시작하도록 지시했다. 이번 통합 대상은 시작 manifest에 기록한 기존 변경 전부다. 신규 정책 결함 보완은 후속 변경으로 분리하고 배포를 대기한다. 매매 프로세스 재기동은 이번 배포에 포함하지 않는다.

기준 HEAD: `1930ac82393a6c5e02fa7aeaf8e569eb01f5d576`. 시작 파일별 SHA256 및 diff: `tmp/integrated-workspace-baseline-20261003/{start-manifest.json,start-diff.patch}`. 현재 KST 10/3 checklist가 없어 아래 신규 당일 checklist에 이번 작업만 등록했다. 10/6 자연 수용·PREOPEN 항목은 미래 소유자로 보존한다.

## 리뷰 범위와 결과

- Cancel wait: 과거 날짜별 원천·registry·terminal·비용 대사, 미분류/격리 항목의 null·source_gap 유지, summary/tower/checklist 직접 소비. 과거 0건을 원천 없는 완결로 바꾸지 않는다.
- Entry capacity: 원래 deposit 시계·scope·generation 유지, bounded preparation join, cache-only non-entry, 실제 sizing/submit fresh read 유지. 진단 payload는 whitelist이며 token/account/raw 오류를 기록하지 않는다. 중첩 cache lock은 RLock이다.
- 장후 source/automation: raw 재구성은 원본 backup·generation·identity 검증 후 봉인한다. Main 후보 재사용은 같은 고정 학습 모수와 동등 전략에 한정한다. terminal predecessor와 병렬 producer 완료를 기다린다.
- Episode/Widget: 원천 sequence·predecessor chain과 exact owner anchor, 소비 schema를 검토했다. 원천 결손은 새 체결·수익 증거로 간주하지 않는다. 실행 service의 별도 code/policy pin은 보존한다.
- 가격/일봉: pre-submit 가격 진단과 실행 EV를 구분한다. 일봉 저장은 수신 key upsert로 바꾸어 미수신 과거행을 보존하고 대상일 무자료를 실패 처리한다. recommendation 실패를 체인 성공으로 처리하지 않는다.
- detector/archive: 날짜별 receipt·전제 원천 검증과 보존 조건을 확인했다. 이번 작업은 삭제·압축·report wrapper를 실행하지 않는다.

기존 변경의 영향 producer/consumer 및 신규 회귀를 검토해 배포를 막는 추가 결함은 발견하지 않았다. 별도 조사에서 확인한 opportunity placeholder, v7 완료 cursor 재개, pre-AI probe 관측/stop·비용 원천 결손은 후속 보완 대상이다. 이 기준선이 해당 결손을 해결했다는 의미는 아니다.

Kiwoom 관련 기존 변경의 공식 근거는 [capacity 리뷰](entry-capacity-source-read-budget-implementation-review-2026-10-02.md)에 기록한 upstream `953e5dbff123f437ab4d11a78a95191a685eb51f` 및 inspected paths/조회시각을 따른다. 이번 통합은 새 broker request나 프로토콜 의미 변경을 추가하지 않는다.

## 검증

- 수정된 test 모듈 24개: **1798 PASS**, 202.15초.
- 영향 scale-in 용량·cash-budget·수량 owner: **11 PASS**, 901 deselected, 1.28초.
- immutable router·restart race·native handoff·bootstrap: **136 PASS**, 4.61초. pandas 기존 deprecation warning 1개.
- 총 **1945 PASS**. Python AST/compile, diff whitespace, 문서 print-only parser를 확인한다. 검증 로그는 `tmp/integrated-workspace-baseline-20261003/`에 보존한다.
- 배포 전 release-set routing PASS: 124 owners, Episode 122 units/366 policy pins. 기존 failed unit 3개는 기능 정상으로 판정하지 않는다. cron 8 routes PASS.

## 배포 경계와 영수증

통합 commit의 detached managed worktree를 준비하고 runtime source 청결·공유 mount를 검증한 뒤 공통 selector를 기존 release-set/selection lock 아래 원자적으로 변경한다. 비활성 Widget 평가·machine 최종 분석 service는 현재 최우선 drop-in의 release 경로·commit 좌표만 갱신한다. 현재 200개 z prefix의 override가 기존 installer의 180개 z prefix보다 우선하므로 낮은 drop-in 추가로 배포했다고 판단하지 않았다. 두 최우선 파일을 백업하고 selection과 함께 기존 배포 lock 아래 갱신했으며 실패 시 원래 bytes를 복구하도록 처리했다. timer schedule과 매매 service pin/PID는 보존한다. 실제 transition/selector/route/service/policy hash 증거는 `data/runtime/startup_readiness/2026-10-03/integrated_workspace_baseline/`에 기록하며, 그 JSON의 commit/root가 배포의 정확한 소유자다.

Selector 변경은 기동 중인 Widget PID 소비나 Main의 다음 PREOPEN 성공을 증명하지 않는다. selector·code 변경으로 이전 준비본의 release binding이 달라질 수 있으며, 다음 거래일 준비/검증은 기존 finalization/PREOPEN 소유자와 구분한다. 원천 결함 보완 후 재생성은 격리 출력에서 검증하고 신규 보완분 배포는 별도 지시까지 대기한다.

## 실행 완료

- 통합 commit: `24a4658db3ded4106446b30a954f33217af9042d`, 66 files.
- 배포: 2026-10-03 08:30:10 KST, `integrated-workspace-baseline-20261003-24a4658d`.
- immutable 동일 source의 배포 계약 재검증: **136 PASS / 6.19초**. 앞선 1945개 고유 tests와 중복이므로 합산해 새 표본으로 표시하지 않는다.
- 공통 cron 8 routes·release-set PASS. 비활성 분석 service 2개 새 WorkingDirectory/ExecStart/commit pin 검증, timer active 유지. 정책/override/bootstrap 파일 **541개 SHA256 보존**.
- Main PID 미소비, Widget PID **2744482**는 기존 `integrated-postclose-startup-20261001-0a8fa0a0` 유지. 매매 service 재기동 0회. 기존 failed Episode unit 3개는 별도 상태다.
- 통합 commit 직후와 배포 직후 default workspace clean 확인. 이 완료 기록의 후속 문서 commit은 `src/deploy/restart.sh`를 변경하지 않으며, source release 선택 commit은 24a4658d로 유지한다. shared docs mount에 완료 기록이 반영된다.
- 정확 영수증: [transition.json](/home/ubuntu/KORStockScan/data/runtime/startup_readiness/2026-10-03/integrated_workspace_baseline/transition.json), [acceptance.json](/home/ubuntu/KORStockScan/data/runtime/startup_readiness/2026-10-03/integrated_workspace_baseline/acceptance.json).
