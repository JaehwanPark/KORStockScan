# EV 개선 후보 백로그 (for Ops)

생성일: 2026-06-08 17:09:22

---

## 1. 동일 종목 split-entry soft-stop 재진입 cooldown report-only

- **기대효과**: 같은 날 동일 종목 반복 손절 누수 차단
- **리스크**: cooldown 중 missed upside 발생 가능 — 차단 건수와 missed upside를 함께 추적해야 함
- **필요 표본**: same_symbol_repeat_flag 케이스 10건 이상
- **검증 지표**: same-symbol repeat soft stop 건수, cooldown 차단 후 10분 missed upside
- **적용 단계**: `report_only_observation`

## 2. latency canary tag 완화 1축 canary 승인

- **기대효과**: tag_not_allowed blocker 감소로 진입 기회 확대
- **리스크**: bugfix-only 실표본 관찰 전 추가 완화는 해석 가능성 저하
- **필요 표본**: bugfix-only canary_applied 건수 50건 이상 (현재 19건)
- **검증 지표**: latency_canary_applied 증가, low_signal / tag_not_allowed 감소
- **적용 단계**: `canary_only_candidate_after_workorder`
