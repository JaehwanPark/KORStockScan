# 2026-09-19 Stage2 To-Do Checklist

## 오늘 목적

- Compact AI 통합을 보존하며 WS 품질 마감·scanner 선택 실행 경제성·다음 장전 정책 소비의 구조 결손을 기존 owner로 닫는다.

## 오늘 강제 규칙

- 사용자 승인 범위는 통합 구현·리뷰·검증·커밋푸시·immutable 배포·제한 장후 재생성이다. 주문·bot 재기동·조기 PREOPEN·provider/수량/cap/hard safety 변경은 포함하지 않는다.
- clean baseline2026-06-05 이후 유효 원천만 사용하고 비용·terminal 결손은 null이다. 실제 실적과 CF, 코드 closure와 자연 경제성을 분리한다.
- 기존 frozen raw·checkpoint·정책·custody와 다른 세션 변경을 보존한다. 원천 결손21건을 개선 실패 또는 정상 무거래0으로 표시하지 않는다.

## 승인된 통합 구현

- [x] `[CompactAIPostcloseIntegration0919] Compact AI 장후 공통 조정·날짜별 정책·최종 handoff 구현` (`Due: 2026-09-19`, `Slot: POSTCLOSE`, `TimeWindow: 00:00~23:59`, `Track: AIPrompt`)
  - Review: [구현 리뷰](../audit-reports/2026-09-19-compact-ai-postclose-integration-implementation-review.md).
  - Source: [통합 계획](../proposals/compact-ai-postclose-source-paired-evaluation-and-preopen-consumer-integration-plan-2026-09-19.md).
  - Acceptance: CI0–CI4 code review/fix/re-review·영향 검증·immutable 배포·source9/17의 명시 publication successor→effective9/21 정책·scoped strict 소비 해시 확인. 유효 비교0은 경제성 closure가 아니며 CI5 자연 수용은9/21의 기존 `KiwoomCommonHealthOpportunityCostAcceptance0917`로 인계한다. 전체 chain DONE·PID·양수EV를 fixture/배포로 대체하지 않는다.

  - Code/인계 Closure: source `0e86f5d20` main/review push, selected `compact-ai-integrated-reviewed-20260919`, source9/17→publication9/19→effective9/21 정책·consumer·scoped strict PASS. 기존 machine/AI9scope 보존·provider 호출0·보호 raw 변경0. Receipt: `tmp/compact-ai-integration-20260919/`. 비교0·EV/일별 순익null·모델 holdout missing과 실제 PID 미소비는 미완료 자연 owner로 인계하며 전체 chain DONE/경제 개선 완료가 아니다.

## Limit-down 폐기 배포 완료

- Limit-down 후속 리뷰·관련 커밋/푸시·immutable 배포: `fcfd7b8e5`. 검토 범위 결함0·통합1,531 passed(기존 wrapper 실패5/제외1은 baseline 재현)·물리 release6 passed·전용 산출물 잔여0. [최종 증거](../audit-reports/2026-09-19-limit-down-watch-retirement-review.md). main 정기 cron target 부재는 기존 상태이며 선택/route 검증과 분리한다. 독립 unit pin·공유 원천/guard 보존; 기동/주문/조기 PREOPEN 미실행·PID 소비 미확인.

- Compact 후속 경제성 리뷰: label hash-only cache의 admission stale 결함 보완·cohort 격리,244+최종7 targeted PASS. 실제21건 label 불일치0/비교0/EV null 및9/21 carry 보존. [후속 리뷰·다음 WS 분석](../audit-reports/2026-09-19-compact-ai-postclose-integration-implementation-review.md). 미래 자연 owner·거래 권한 변경 없음.
- [x] `[CompactAIEconomicOptimization0919] Compact 응답 blocker·bounded projection migration·경제성 연구값·phase 상태 보완` (`Due: 2026-09-19`, `Slot: POSTCLOSE`, `TimeWindow: 00:00~23:59`, `Track: AIPrompt`)
  - Source: [통합 계획 §11–§19](../proposals/compact-ai-postclose-source-paired-evaluation-and-preopen-consumer-integration-plan-2026-09-19.md). Review: [구현·배포 리뷰](../audit-reports/2026-09-19-compact-economic-optimization-implementation-review.md).
  - Acceptance: commit `411ec0efdf993ec11e36b3fc79b78a5a7a36a6e1`, immutable release 선택·route print-plan·영향/물리 release 회귀 PASS. source9/17 제한 재생성은 source gap21(stop10/transport8/semantic1/identity2), provider0/raw rescan0, 비교0·EV null·승격0이다. effective9/21 bundle `fb4870b8ab479897c7580d79a92acb2595889c2d7c95b75087bcef6cfb6f74c5` incumbent carry·machine/비compact scope 보존·scoped strict PASS. 실제 PID/완료 손익은 기존 자연 owner OPEN이며 양수EV 주장이 아니다.
  - 후속 재리뷰: 영향333 PASS, 현재 consumer handoff를 Git checklist에 재결속. 미참조 generation·중복 임시물25개/411,256 bytes 삭제 후 scoped strict·consumer PASS. commit `8143121b6`, immutable release `compact-economic-cleanup-reviewed-20260919-8143121b6` 선택·route PASS. 원천·정책·직계 v4–v6 lineage·rollback/검증 증거는 보존했다.

## WS 품질·조건부 경제성 전달 구현 이력

- `[CodeImprovementWorkorderReview0918] WS evaluator·차단 정책·장전 전달 구현 이력` (`Due: 2026-09-19`, `Slot: POSTCLOSE`, `TimeWindow: 00:00~23:59`, `Track: ScalpingLogic`)
  - Source: [구현 계획](../proposals/ws-freshness-postclose-quality-consolidation-and-conditional-economic-policy-consumer-improvement-plan-2026-09-19.md), [구현 리뷰](../audit-reports/2026-09-19-ws-freshness-conditional-economics-implementation-review.md).
  - 구현 범위: 기존 입력의 evaluator·fail-closed policy·source17/publication19/policy18/effective21 전달·Daily/EV/runtime/tower/checklist/scoped strict 동일 hash·immutable future release. 실제 비교0/null은 경제성 closure가 아니다.
  - Result: 최초 WS release `411ec0efd`, 현재 이를 포함한 selected release `8143121b6`; source section `02afcf30577e8fa290e00fe9d62e1e624adcb8ce2217dbfaec418a010ece49d2`; policy `5cb82631ef6674c80a5154737ccdca70b6d6ac75fad0194d2cc883e5ef45bf51`; `source_gap/source_contract_blocked`, bonus0, strict PASS. Primary EV·일별 순익은 원 plan/quantity/guard·양측 terminal 결손으로 null이다.
  - 정정: capacity-pruned incoming 후보는 자연 compact AI/entry recipe/quantity/guard/terminal을 생산하지 않는다. source9/17은 복구 불가이며 시간 경과로 해소되지 않는다. [재점검 계획 §12](../proposals/ws-freshness-postclose-quality-consolidation-and-conditional-economic-policy-consumer-improvement-plan-2026-09-19.md)는 미래 pair의 source-only opportunity EV와 기존 marginal slot의 사전 배정 canary를 분리한다. 구조 공급·실제 비교는 9/21의 동일 stable ID OPEN owner로 이관하며 이 항목은 완료 checkbox가 아니다.
  - 권한: source-only CF와 same-tier bounded bonus뿐이다. 새 주문·재기동·조기 PREOPEN·provider/quantity/cap/tier/slot/quota/hard guard 변경 없음. fixture 양수값은 구현 검증이며 자연 EV가 아니다.
