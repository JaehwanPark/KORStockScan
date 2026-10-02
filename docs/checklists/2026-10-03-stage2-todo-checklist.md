# 2026-10-03 Stage2 To-Do Checklist

## 오늘 목적

- 기존 작업본 통합 커밋·배포 후 깨끗한 기준선 확보. Main 기계·보조 정책 원천 보완은 별도 변경으로 계획·검증한다.

## 필수 규칙

- Plan Rebase §1–§8, 원천·비용·날짜·hash 및 기존 hard safety/owner 권한을 유지한다.
- 이번 기존 작업본 배포와 신규 보완분 배포 대기를 구분한다. 매매 재기동·주문·provider/threshold 변경을 추가하지 않는다.
- 10/6 자연 수용·PREOPEN stable ID는 해당 checklist에 남긴다. 출력은 검증과 실제 PID/경제성 증거를 구분한다.

## 실행 항목

- [x] `[IntegratedWorkspaceBaseline1003] 기존 작업본 통합 commit·release 배포 및 기준선 청결 확인` (`Due: 2026-10-03`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [통합 리뷰](../audits/integrated-workspace-baseline-review-2026-10-03.md).
  - Acceptance: 1945 tests PASS, compile/diff/parser PASS; immutable release HEAD/source/mount 검증, 공통 selector와 비활성 분석 service pin, cron/release-set PASS, 정책 hash 보존, trading PID 재기동 없음, git status 청결. 정확 commit/배포 결과는 `data/runtime/startup_readiness/2026-10-03/integrated_workspace_baseline/transition.json`에 보존한다.
  - 완료: 통합 commit `24a4658d`, 08:30 KST 공통 route·비활성 분석 service 2개 pin 배포 PASS, 541개 정책/override/bootstrap hash 보존, 배포 후 workspace clean. 실제 service 재기동 0. 미래 PREOPEN/PID는 이 항목의 완료 증거가 아니다. 신규 원천 보완분은 별도 diff·격리 재생성으로 진행하고 배포를 대기한다.
