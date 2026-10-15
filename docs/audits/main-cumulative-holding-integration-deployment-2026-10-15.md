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
