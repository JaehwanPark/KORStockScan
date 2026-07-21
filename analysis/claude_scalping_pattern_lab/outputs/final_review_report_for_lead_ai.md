# 스캘핑 패턴 분석 최종 리뷰 보고서 (for Lead AI)

생성일: 2026-07-21 21:17:00
분석 기간: 2026-06-04 ~ 2026-07-21

---

## 1. 판정

### 1-1. 코호트별 손익 요약

| 코호트 | 거래수 | 승률 | 손익 중앙값 | 기여손익 합 | 표본충분 |
|---|---:|---:|---:|---:|---|
| full_fill | 222 | 57.2% | +0.495% | -21.770% | ✓ |
| split-entry | 33 | 36.4% | -0.230% | -36.070% | ✓ |

### 1-4. 튜닝 관찰축 요약

- `WAIT65~79 total_candidates=0`, `recovery_check=0`, `promoted=0`, `submitted=0`
- `blocked_ai_score_share=0.0%`, `gatekeeper_eval_ms_p95=0ms`, `budget_pass_to_submitted_rate=3.0%`

- `No acute observability alert`: 중립 — 주요 관찰축에서 즉시 경고할 단일 병목이 두드러지지 않는다.

### 1-2. 손실 패턴 Top 5

**#1** — 코호트: `full_fill` / 청산규칙: `scalp_soft_stop_pct`
- 빈도: 39건 | 손익 중앙값: -3.140% | 기여손익: -119.280%
- 보유시간 중앙값: 2678.0초
- 선행 조건: 없음

**#2** — 코호트: `full_fill` / 청산규칙: `scalp_hard_stop_pct`
- 빈도: 21건 | 손익 중앙값: -3.220% | 기여손익: -84.500%
- 보유시간 중앙값: 1056.5초
- 선행 조건: 없음

**#3** — 코호트: `split-entry` / 청산규칙: `scalp_soft_stop_pct`
- 빈도: 11건 | 손익 중앙값: -3.160% | 기여손익: -33.990%
- 보유시간 중앙값: 1462.0초
- 선행 조건: 없음

**#4** — 코호트: `split-entry` / 청산규칙: `scalp_hard_stop_pct`
- 빈도: 5건 | 손익 중앙값: -5.340% | 기여손익: -19.200%
- 보유시간 중앙값: 144.0초
- 선행 조건: 없음

**#5** — 코호트: `full_fill` / 청산규칙: `scalp_preset_hard_stop_pct`
- 빈도: 7건 | 손익 중앙값: -1.030% | 기여손익: -11.220%
- 보유시간 중앙값: 67.0초
- 선행 조건: 없음

### 1-3. 수익 패턴 Top 5

**#1** — 코호트: `full_fill` / 청산규칙: `scalp_trailing_take_profit` / 진입모드: `normal`
- 빈도: 87건 | 손익 중앙값: +1.520% | 기여손익: +163.200%

**#2** — 코호트: `split-entry` / 청산규칙: `scalp_trailing_take_profit` / 진입모드: `normal`
- 빈도: 11건 | 손익 중앙값: +1.390% | 기여손익: +16.590%

**#3** — 코호트: `full_fill` / 청산규칙: `scalp_low_profit_stagnation_hard_exit` / 진입모드: `normal`
- 빈도: 22건 | 손익 중앙값: +0.565% | 기여손익: +13.110%

**#4** — 코호트: `full_fill` / 청산규칙: `scalp_hard_stop_pct` / 진입모드: `normal`
- 빈도: 5건 | 손익 중앙값: +1.350% | 기여손익: +9.450%

**#5** — 코호트: `full_fill` / 청산규칙: `scalp_profit_stagnation_time_exit` / 진입모드: `normal`
- 빈도: 2건 | 손익 중앙값: +1.305% | 기여손익: +2.610%

### 1-4. 기회비용 회수 후보 Top 5

**#1** — `AI threshold miss`
- 차단 건수 합계: 292441건 | 차단 비율: 99.8% | 관찰 일수: 33일

**#2** — `latency guard miss`
- 차단 건수 합계: 141741건 | 차단 비율: 99.6% | 관찰 일수: 33일

**#3** — `overbought gate miss`
- 차단 건수 합계: 16740건 | 차단 비율: 97.1% | 관찰 일수: 33일

**#4** — `liquidity gate miss`
- 차단 건수 합계: 0건 | 차단 비율: 0.0% | 관찰 일수: 33일

---

## 2. 근거

### 2-1. split-entry 코호트 핵심 위험

- rebase_integrity_flag: 16건
- partial_then_expand_flag: 47건
- same_symbol_repeat_flag: 1264건
- same_ts_multi_rebase_flag: 18건

### 2-2. 전역 손절 강화 비권고 이유

- 오늘 손절 표본에는 AI score 58~69처럼 낮지 않은 값도 포함됨.
- 문제의 핵심은 `틱 급변 + 확대 타이밍`이며, 전역 강화는 승자도 함께 절단함.
- 코호트 분리 없이 단일 임계값 강화 시 full_fill 수익 코호트에 부정적 영향.

---

## 3. 다음 액션

### 3-1. EV 개선 우선순위 (report-only observation 선행)

**report-only observation (즉시 시작 가능):**

- `split-entry rebase 수량 정합성 report-only 감사` — 검증지표: cum_filled_qty > requested_qty 비율, same_ts_multi_rebase_count 분포
- `partial → fallback 확대 직후 즉시 재평가 report-only` — 검증지표: 확대 후 90초 내 held_sec soft stop 비율 감소 여부
- `동일 종목 split-entry soft-stop 재진입 cooldown report-only` — 검증지표: same-symbol repeat soft stop 건수, cooldown 차단 후 10분 missed upside
- `partial-only 표류 전용 timeout report-only` — 검증지표: partial-only held_sec 중앙값, timeout 이후 실현손익 분포

**canary-only candidate (workorder 구현 후):**

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