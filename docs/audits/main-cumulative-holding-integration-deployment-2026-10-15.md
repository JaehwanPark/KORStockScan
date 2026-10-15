# 누적 정책·보유 계약 통합 배포 검토 — 2026-10-15

## 결정과 범위

사용자가 `7b2e421e339563d25d088558ce38cb27d711a246`와 보유·재생 수리를 통합하여 배포·재기동하도록 승인했다. 실제 선택본 `451b6c1ec84fafa563d95381e95c814ac2b2b18b`를 부모로 하는 `af2b8f99414f7b837779ac10bbe4d1cd1aef6b20`에 누적 정책 커밋을 병합한다. 격리 작업본은 `/home/ubuntu/KORStockScan-worktrees/cumulative-holding-integrated-20261015`다. 원 작업본의 동시 수정과 원천, 수동 custody는 보존한다.

누적 등록안의 publication은 10/15, target은 10/16이다. 오늘은 통합 코드를 재기동에 반영하고, 이 날짜 계약에 맞춘 등록과 장후/다음 PREOPEN 인계를 연결한다. 원 10/15 기계·보조 정책을 오늘 새 후보로 바꾸지 않는다. 자연 거래·완료 비용 성과는 기존 OPEN owner의 별도 수용이다.

## 리뷰와 보완

- 보조 튜닝 충돌은 기존 approved machine selection 검증과 새 cumulative manifest 검증을 모두 보존하여 해결했다. 재리뷰에서 승인 없는 cumulative marker가 manifest false 반환을 통해 membership 변경을 허용할 수 있는 경계를 발견했다. 명시적인 manifest 검증 성공을 요구하도록 보완하고 회귀를 추가했다.
- 보유 preset·ISO 비용 시각·실제 수동 이관 관측과 비상시 등록 완료 연결은 `af2b8f994`의 검증된 수리를 유지한다. 연구 손절 -3%와 실제 preset을 같은 값으로 덮지 않고 별도 계약으로 소비한다. 원 partial-fill/source-gap 및 비용 null을 보존한다.
- 원 PREOPEN→통합본의 정확한 source hash pair를 stop/delay/holding consumer gate에 추가했다. 기존 허용쌍, 정책값·원천·PID 검증을 유지한다. 무조건적인 code mismatch 무시는 없다.
- 변경된 네 family의 코드 capability를 독립적인 네트워크 차단 fixture로 검증한다. 기존 native 보고서는 재작성하지 않는다. 보조평가의 기존 fixture도 원 hash·경로·권한을 재검증하고, 후속 코드의 검증은 새 fixture로만 증명한다. 과거 미검증 계약을 native 검증 완료로 바꾸지 않는다.
- ordered 배포의 detector transition lock과 immutable operating checklist를 사용한다. 원 PREOPEN/env/정책 파일을 보존하며, 중지 전 전임 PID·원천·후속 코드 계약을 검증한다. 이전 오류를 삭제하거나 detector cursor를 초기화하지 않는다.

## 검증 및 수용

현재 정책의 기존 선택본/통합본 native 재생: 128 scopes, 76,800 rows, 607 hits, signal SHA 동일, mismatch 0. 누적 27 partition 재생, 통합 회귀, 독립 fixture와 compile/diff/parser의 최종 결과는 [배포 근거 디렉터리](../../tmp/cumulative-holding-deploy-20261015/)에 보존한다. 배포 전 진행 중인 검증을 PASS로 취급하지 않는다.

최종 배포는 ordered transition의 complete/pass, 새 PID/start/cwd의 native 소비, 다음 정규 observer/detector가 같은 selected commit을 소비하고 artifact_freshness 실패가 없는 것으로 수용한다. 관측 대기 warning은 성공 거래나 경제성으로 해석하지 않는다. 배포 후 실제 영수증은 이 문서에 후속 기록한다.

실행 owner는 `DirectFamilyPreopenPolicyHandoff`, `CumulativePolicyAdoptionDeployment1015`, `HoldingProfitExitSourceContractRepair`, `NonfixedDispatchReadinessReview1012`를 재사용한다. 원 날짜별 Acceptance/History를 유지하며, 외부 Project/Calendar sync와 수동 주문·provider 호출은 실행하지 않는다.

통합 배포 경계 회귀 1,614개와 holding/등록/기계/freshness 회귀 846개 PASS(기존 pandas 경고1). Python compile, diff 및 두 작업본의 print-only parser와 단일 owner 확인 PASS. 누적 native 전수 재생은 별도 진행 중이며 실행 완료 뒤 등록 준비를 봉인한다.

## 실제 배포·다음 날짜 인계

- 15:55:22 ordered transition `complete/pass`: 코드 `cfa070c1e1dab125170b08aaef6b3583a7b50ae8`, PID2407222/start11119497, cwd `/home/ubuntu/KORStockScan-runtime-releases/cumulative-holding-integrated-20261015-v1/src`. 전임 PID2276473은 정상 종료됐다. 원 bootstrap JSON/env·current policy·수동 제외 파일 hash가 보존됐다.
- 통합 native 누적 재생 27 partitions/5,587,427 rows, confirmation236,597·선정9,502·불일치0. 네트워크 차단 fixture는 entry93/rising86/holding91/auxiliary83, 총353개 PASS. [최종 리뷰](../../tmp/cumulative-holding-deploy-20261015/review-result.json).
- 10/16 등록을 durable intake했다: publication10/15, target10/16, receipt `c15491190e72030fabeb7e2eea8027d0e744f2775c0d7dcc5ec629ce77d3b62a`. 기존 기계 policy pointer는 불변이며 새 후보 활성/PID 소비는 false다. [등록 영수증](../../tmp/cumulative-holding-deploy-20261015/cumulative-intake.json). 정상 장후 machine→auxiliary→stage와 다음 PREOPEN 소비는 기존 OPEN owner가 계속 소유한다.
- 다음 정규 observer/detector 및 새 PID의 WebSocket snapshot은 관측 대기다. 배포 직전 15:52:41 정규 탐지의 artifact_freshness=warning, 실패0은 이전 PID 결과로 보존한다. 새 선택본의 탐지 수용은 [후속 확인](../../tmp/cumulative-holding-deploy-20261015/postdeploy-verification.json)의 실제 세대가 소유한다.

## 배포 후 수용

[배포 후 확인](../../tmp/cumulative-holding-deploy-20261015/postdeploy-verification.json)의 15개 조건 PASS: 현재 commit/PID/start/cwd, 원 정책/수동 제외 hash, native bootstrap·소비, 새 PID의 WebSocket 연결/게시, 현재 observer/detector 동일 run과 health projection을 확인했다. `artifact_freshness`는 관측 대기 warning이며 실패는 없다. 새 후보는 여전히 target10/16 등록 대기로, 오늘 실제 PID의 코드 소비와 분리된다.

15:57:08에 기동 직후 resource_usage의 I/O wait40.22%≥35% 경보1회가 발생했다. 이후15:58:17·15:59:25 정규 탐지의 resource_usage/process_health/log_scanner는 PASS다. [재기동 이후 오류 관측](../../tmp/cumulative-holding-deploy-20261015/postrestart-error-observations.json)에 최초 경보를 보존하며 임계값·cursor를 변경하지 않았다. 기존 holding_exit_sentinel 이력과 06:50 이후 최종화 복구 warning은 남아 있다. 전체 무경고·경제성 완료를 주장하지 않는다.

16:00:37 정규 탐지에서도 현재 commit·observer 동일 run/health projection 및 실패0을 확인했고 16:01:01 WebSocket producer는 PID2407222/cfa070c1e다. AFTER 개장 후 holding_exit_sentinel_aftermarket_report의 기존 stale(9,020초>600초)와 observer coverage partial warning이 명시됐다. 이는 새 배포의 정책/원천 결속 실패와 구분하며 기존 `HoldingProfitExitSourceContractRepair`·관측 owner의 source acceptance를 유지한다.
