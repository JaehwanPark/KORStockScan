# 장후작업 현행 활성 목록

## 현행 Main-only 계약

자동 주문 owner는 Main이다. 에피소드·위젯과 독립 IPO 자동실행은 영구 퇴역한다. 과거 체결 잔여는 사용자 수동관리하며 전용 exit/cancel/알림/연구/PREOPEN을 요구하지 않는다. 공통 journal/DB, Main 원천·정책 부모·보호조건은 보존한다. 현행 owner와 수용은 [현재 체크리스트](../checklists/2026-10-08-stage2-todo-checklist.md), 원칙은 [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md)를 따른다.

| stage | producer / dependency |
| --- | --- |
| main_machine_policy | Main registered reversal research/publisher |
| legacy_machine_report | Main compatibility report |
| outcome_labels | Main outcome labels |
| main_auxiliary_policy | Main machine policy; pre-cutover labels/report compatibility |
| pre_submit_delay | Main source-only timing research |
| summary_handoff | summary/tower/checklist/strict/controller |

공통 cron은 runtime selector로 EOD 20:05, postclose/controller/tuning 20:10, archive 20:50, finalization 05:00, PREOPEN 07:35, Main start 07:55를 실행한다. 삼성 frozen validation은 기존 Main wrapper의 선택적 report-only sidecar이며 정책 발행·startup gate가 아니다. 전용 episode final-refresh/auto-apply/fill notifier/확장 timer와 IPO cron은 제거한다. 10/8 이전 sealed stage 원 바이트는 과거 최종화 검증에 필요한 최소 증거로만 보존하며 새 stage나 미래 복구 owner를 만들지 않는다.

실행 근거와 삭제/배포 영수증은 [구현 검토](../audits/main-only-widget-episode-full-retirement-implementation-review-2026-10-08.md)에 기록한다. 과거 구성은 Git 이력이며 현행 설치 명령으로 사용하지 않는다.
