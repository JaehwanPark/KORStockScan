# EV 개선 후보 백로그 (for Ops)

생성일: 2026-06-05 18:05:25

---

## 1. latency canary tag 완화 1축 canary 승인

- **기대효과**: tag_not_allowed blocker 감소로 진입 기회 확대
- **리스크**: bugfix-only 실표본 관찰 전 추가 완화는 해석 가능성 저하
- **필요 표본**: bugfix-only canary_applied 건수 50건 이상 (현재 19건)
- **검증 지표**: latency_canary_applied 증가, low_signal / tag_not_allowed 감소
- **적용 단계**: `canary_only_candidate_after_workorder`
