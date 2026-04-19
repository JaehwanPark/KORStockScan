# 스캘핑 패턴 분석 최종 리뷰 보고서 (for Lead AI)

생성일: 2026-04-17 14:06:25
분석 기간: 2026-04-01 ~ 2026-04-17

---

## 1. 판정

### 1-1. 코호트별 손익 요약

| 코호트 | 거래수 | 승률 | 손익 중앙값 | 기여손익 합 | 표본충분 |
|---|---:|---:|---:|---:|---|
| full_fill | 98 | 38.8% | -0.230% | -20.030% | ✓ |
| partial_fill | 4 | 0.0% | -0.425% | -2.590% | ⚠️부족 |
| split-entry | 46 | 43.5% | -0.680% | -13.180% | ✓ |

### 1-2. 손실 패턴 Top 5

**#1** — 코호트: `split-entry` / 청산규칙: `scalp_soft_stop_pct`
- 빈도: 14건 | 손익 중앙값: -1.575% | 기여손익: -23.330%
- 보유시간 중앙값: 110.5초
- 선행 조건: 없음

**#2** — 코호트: `full_fill` / 청산규칙: `scalp_soft_stop_pct`
- 빈도: 6건 | 손익 중앙값: -1.625% | 기여손익: -9.760%
- 보유시간 중앙값: 267.5초
- 선행 조건: 없음

**#3** — 코호트: `full_fill` / 청산규칙: `scalp_ai_early_exit`
- 빈도: 6건 | 손익 중앙값: -0.890% | 기여손익: -5.490%
- 보유시간 중앙값: 630.5초
- 선행 조건: 없음

**#4** — 코호트: `full_fill` / 청산규칙: `scalp_preset_hard_stop_pct`
- 빈도: 6건 | 손익 중앙값: -0.670% | 기여손익: -3.660%
- 보유시간 중앙값: 633.5초
- 선행 조건: 없음

**#5** — 코호트: `partial_fill` / 청산규칙: `scalp_soft_stop_pct`
- 빈도: 1건 | 손익 중앙값: -1.510% | 기여손익: -1.510%
- 보유시간 중앙값: 6093.0초
- 선행 조건: 없음

### 1-3. 수익 패턴 Top 5

**#1** — 코호트: `full_fill` / 청산규칙: `scalp_trailing_take_profit` / 진입모드: `normal`
- 빈도: 11건 | 손익 중앙값: +1.040% | 기여손익: +13.190%

**#2** — 코호트: `split-entry` / 청산규칙: `scalp_trailing_take_profit` / 진입모드: `normal`
- 빈도: 10건 | 손익 중앙값: +0.785% | 기여손익: +8.450%

**#3** — 코호트: `full_fill` / 청산규칙: `scalp_ai_momentum_decay` / 진입모드: `normal`
- 빈도: 1건 | 손익 중앙값: +0.660% | 기여손익: +0.660%

**#4** — 코호트: `split-entry` / 청산규칙: `scalp_preset_protect_profit` / 진입모드: `normal`
- 빈도: 2건 | 손익 중앙값: +0.300% | 기여손익: +0.600%

**#5** — 코호트: `split-entry` / 청산규칙: `scalp_ai_momentum_decay` / 진입모드: `normal`
- 빈도: 1건 | 손익 중앙값: +0.580% | 기여손익: +0.580%

### 1-4. 기회비용 회수 후보 Top 5

**#1** — `AI threshold miss`
- 차단 건수 합계: 1031746건 | 차단 비율: 100.0% | 관찰 일수: 12일

**#2** — `overbought gate miss`
- 차단 건수 합계: 379124건 | 차단 비율: 100.0% | 관찰 일수: 12일

**#3** — `latency guard miss`
- 차단 건수 합계: 12298건 | 차단 비율: 99.1% | 관찰 일수: 12일

**#4** — `liquidity gate miss`
- 차단 건수 합계: 0건 | 차단 비율: 0.0% | 관찰 일수: 12일

---

## 2. 근거

### 2-1. split-entry 코호트 핵심 위험

- rebase_integrity_flag: 19건
- partial_then_expand_flag: 57건
- same_symbol_repeat_flag: 59건
- same_ts_multi_rebase_flag: 21건

### 2-2. 전역 손절 강화 비권고 이유

- 오늘 손절 표본에는 AI score 58~69처럼 낮지 않은 값도 포함됨.
- 문제의 핵심은 `틱 급변 + 확대 타이밍`이며, 전역 강화는 승자도 함께 절단함.
- 코호트 분리 없이 단일 임계값 강화 시 full_fill 수익 코호트에 부정적 영향.

---

## 3. 다음 액션

### 3-1. EV 개선 우선순위 (shadow-only 선행)

**shadow-only (즉시 시작 가능):**

- `split-entry rebase 수량 정합성 shadow 감사` — 검증지표: cum_filled_qty > requested_qty 비율, same_ts_multi_rebase_count 분포
- `partial → fallback 확대 직후 즉시 재평가 shadow` — 검증지표: 확대 후 90초 내 held_sec soft stop 비율 감소 여부
- `동일 종목 split-entry soft-stop 재진입 cooldown shadow` — 검증지표: same-symbol repeat soft stop 건수, cooldown 차단 후 10분 missed upside
- `partial-only 표류 전용 timeout shadow` — 검증지표: partial-only held_sec 중앙값, timeout 이후 실현손익 분포

**canary (shadow 결과 확인 후):**

- `latency canary tag 완화 1축 canary 승인` — 필요표본: bugfix-only canary_applied 건수 50건 이상 (현재 19건)

**승격 후보 (canary 통과 후):**

- 없음

### 3-2. 금지 사항

- `full_fill / partial_fill / split-entry` 혼합 결론 금지
- 운영 코드 즉시 변경 지시 금지
- 전역 soft_stop 강화 같은 단일축 일반화 결론 금지

---

## 4. 참고 문서

- [data_quality_report.md](data_quality_report.md)
- [ev_improvement_backlog_for_ops.md](ev_improvement_backlog_for_ops.md)
- [claude_payload_summary.json](claude_payload_summary.json)
- [claude_payload_cases.json](claude_payload_cases.json)