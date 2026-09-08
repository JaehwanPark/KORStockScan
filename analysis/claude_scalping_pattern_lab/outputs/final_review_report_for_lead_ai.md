# 스캘핑 패턴 분석 최종 리뷰 보고서 (for Lead AI)

생성일: 2026-09-08 21:40:44
분석 기간: 2026-06-05 ~ 2026-09-08

---

## 1. 판정

### 검증된 순이익·거래빈도 (실전 승인 아님)

- 경제성 상태: `no_valid_economic_outcomes`
- 실제 체결금액에서 대사된 수수료·세금을 차감. 체결가격에 반영된 슬리피지는 중복 차감하지 않음.
- 아래 기존 스냅샷 통계는 비용 미검증 참고치이며 실전 승인 근거가 아님.
- 상승/반등 조건과 대조군 대비 증분 EV는 기존 전략 owner가 검증. 양수 관측만으로 BUY/승격하지 않음.

| 창 | 코호트 | 완료수 | 순EV(금액가중 %) | 순익 KRW | 유효일당 거래수 | 유효일당 순익 KRW |
| --- | --- | ---: | ---: | ---: | ---: | ---: |

- 제외 원천 일수: 55
- 유지보수 재검토 필요: `False`

### 1-1. 스냅샷 참고 손익 (비용·체결 품질 미검증)

| 코호트 | 거래수 | 승률 | 손익 중앙값 | 기여손익 합 | 표본충분 |
|---|---:|---:|---:|---:|---|
| full_fill | 149 | 70.5% | +0.550% | +22.770% | ✓ |
| partial_fill | 134 | 61.9% | +0.310% | -36.720% | ✓ |
| unknown_fill | 18 | 22.2% | -0.080% | -6.720% | ⚠️부족 |

### 1-4. 튜닝 관찰축 요약

- `WAIT65~79 total_candidates=10`, `recovery_check=0`, `promoted=0`, `submitted=0`
- `blocked_ai_score_share=70.0%`, `gatekeeper_eval_ms_p95=0ms`, `budget_pass_to_submitted_rate=0.0%`

- `AI threshold dominance`: 경고 — `blocked_ai_score_share=70.0%`로 WAIT/BLOCK 비중이 높아 BUY drought 해석을 지지한다.
- `Budget pass without submit`: 경고 — `budget_pass=617`인데 `submitted=0`라 제출 전 병목이 기대값 회복을 끊고 있다.

### 1-2. 손실 패턴 Top 5

**#1** — 코호트: `partial_fill` / 청산규칙: `scalp_soft_stop_pct`
- 빈도: 24건 | 손익 중앙값: -3.470% | 기여손익: -86.870%
- 보유시간 중앙값: 1767.0초
- 선행 조건: multi_rebase_flag=8건(33.3%), partial_then_expand_flag=8건(33.3%), same_symbol_repeat_flag=24건(100.0%)

**#2** — 코호트: `full_fill` / 청산규칙: `scalp_soft_stop_pct`
- 빈도: 17건 | 손익 중앙값: -3.890% | 기여손익: -67.200%
- 보유시간 중앙값: 3439.0초
- 선행 조건: same_symbol_repeat_flag=17건(100.0%)

**#3** — 코호트: `full_fill` / 청산규칙: `scalp_hard_stop_pct`
- 빈도: 7건 | 손익 중앙값: -5.510% | 기여손익: -42.430%
- 보유시간 중앙값: 1821.0초
- 선행 조건: same_symbol_repeat_flag=1건(14.3%)

**#4** — 코호트: `partial_fill` / 청산규칙: `scalp_hard_stop_pct`
- 빈도: 4건 | 손익 중앙값: -5.485% | 기여손익: -22.000%
- 보유시간 중앙값: 1086.0초
- 선행 조건: multi_rebase_flag=3건(75.0%), partial_then_expand_flag=3건(75.0%)

**#5** — 코호트: `partial_fill` / 청산규칙: `scalp_trailing_take_profit`
- 빈도: 17건 | 손익 중앙값: -0.230% | 기여손익: -7.020%
- 보유시간 중앙값: 273.0초
- 선행 조건: multi_rebase_flag=3건(17.6%), partial_then_expand_flag=3건(17.6%), same_symbol_repeat_flag=1건(5.9%)

### 1-3. 수익 패턴 Top 5

**#1** — 코호트: `full_fill` / 청산규칙: `scalp_trailing_take_profit` / 진입모드: `normal`
- 빈도: 82건 | 손익 중앙값: +1.295% | 기여손익: +126.550%

**#2** — 코호트: `partial_fill` / 청산규칙: `scalp_trailing_take_profit` / 진입모드: `normal`
- 빈도: 75건 | 손익 중앙값: +0.730% | 기여손익: +73.910%

**#3** — 코호트: `full_fill` / 청산규칙: `scalp_low_profit_stagnation_hard_exit` / 진입모드: `normal`
- 빈도: 22건 | 손익 중앙값: +0.535% | 기여손익: +12.430%

**#4** — 코호트: `partial_fill` / 청산규칙: `scalp_low_profit_stagnation_hard_exit` / 진입모드: `normal`
- 빈도: 6건 | 손익 중앙값: +0.700% | 기여손익: +4.600%

**#5** — 코호트: `partial_fill` / 청산규칙: `scalp_profit_stagnation_time_exit` / 진입모드: `normal`
- 빈도: 1건 | 손익 중앙값: +1.480% | 기여손익: +1.480%

### 1-4. 기회비용 회수 후보 Top 5

**#1** — `AI threshold miss`
- 차단 건수 합계: 81890건 | 차단 비율: 99.4% | 관찰 일수: 48일

**#2** — `overbought gate miss`
- 차단 건수 합계: 11922건 | 차단 비율: 96.2% | 관찰 일수: 48일

**#3** — `latency guard miss`
- 차단 건수 합계: 11686건 | 차단 비율: 96.1% | 관찰 일수: 48일

---

## 2. 근거

### 2-1. split-entry 코호트 핵심 위험

- rebase_integrity_flag: 16건
- partial_then_expand_flag: 59건
- same_symbol_repeat_flag: 1305건
- same_ts_multi_rebase_flag: 24건

### 2-2. 전역 손절 강화 비권고 이유

- 관측 패턴만으로 손실 원인이나 임계값 변경 효과를 단정하지 않음.
- 동일 코호트의 이익·손실·누락 기회와 비용을 함께 평가해야 함.

---

## 3. 다음 액션

### 3-1. EV 개선 우선순위 (report-only observation 선행)

**report-only observation (즉시 시작 가능):**

- `split-entry rebase 수량 정합성 report-only 감사` — 검증지표: cum_filled_qty > requested_qty 비율, same_ts_multi_rebase_count 분포
- `partial fill quality source attribution` — 검증지표: partial_then_expand_flag count; exact partial/full net economics
- `same-symbol repeat source attribution` — 검증지표: same_symbol_repeat_flag count; exact lifecycle net economics

**canary-only candidate (workorder 구현 후):**

- 없음

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