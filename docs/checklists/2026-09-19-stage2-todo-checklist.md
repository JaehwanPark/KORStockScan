# 2026-09-19 Stage2 To-Do Checklist

## 오늘 목적

- Compact AI 장후 원천·평가·정책·최종 소비를 기존 owner로 통합하고 승인된 source9/17의 다음 장전 정책을 생성한다.

## 오늘 강제 규칙

- 사용자 승인 범위는 통합 구현·리뷰·검증·커밋푸시·immutable 배포·제한 장후 재생성이다. 주문·bot 재기동·조기 PREOPEN·provider/수량/cap/hard safety 변경은 포함하지 않는다.
- clean baseline2026-06-05 이후 유효 원천만 사용하고 비용·terminal 결손은 null이다. 실제 실적과 CF, 코드 closure와 자연 경제성을 분리한다.
- 기존 frozen raw·checkpoint·정책·custody와 다른 세션 변경을 보존한다. 원천 결손21건을 개선 실패 또는 정상 무거래0으로 표시하지 않는다.

## 승인된 통합 구현

- [ ] `[CompactAIPostcloseIntegration0919] Compact AI 장후 공통 조정·날짜별 정책·최종 handoff 구현` (`Due: 2026-09-19`, `Slot: POSTCLOSE`, `TimeWindow: 00:00~23:59`, `Track: AIPrompt`)
  - Review: [구현 리뷰](../audit-reports/2026-09-19-compact-ai-postclose-integration-implementation-review.md).
  - Source: [통합 계획](../proposals/compact-ai-postclose-source-paired-evaluation-and-preopen-consumer-integration-plan-2026-09-19.md).
  - Acceptance: CI0–CI4 code review/fix/re-review·영향 검증·immutable 배포·source9/17의 명시 publication successor→effective9/21 정책·scoped strict 소비 해시 확인. 유효 비교0은 경제성 closure가 아니며 CI5 자연 수용은9/21의 기존 `KiwoomCommonHealthOpportunityCostAcceptance0917`로 인계한다. 전체 chain DONE·PID·양수EV를 fixture/배포로 대체하지 않는다.
