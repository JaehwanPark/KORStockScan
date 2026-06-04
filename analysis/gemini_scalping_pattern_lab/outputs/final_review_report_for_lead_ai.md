# Gemini Scalping Pattern Lab Final Review

- generated_at: `2026-06-04 18:02:11`
- analysis_period: `2026-04-21 ~ 2026-06-04`

## 1. 판정

> 표본 부족: valid_profit_rate=0건 < 30. 결론 확정 대신 방향성만 기록한다.

### 1-1. 코호트별 EV 요약

- 분석 대상 없음

### 1-2. Plan Rebase 관찰축 요약

- `WAIT65~79 total_candidates=2`, `recovery_check=0`, `promoted=0`, `submitted=0`
- `blocked_ai_score_share=50.0%`, `budget_pass_to_submitted_rate=0.0%`, `gatekeeper_eval_ms_p95=3431ms`

- `No acute observability alert`: 중립 — 주요 관찰축에서 즉시 경고할 단일 병목이 두드러지지 않는다.

### 1-3. 손실 패턴 Top 5

- 분석 대상 없음
### 1-4. 수익 패턴 Top 5

- 분석 대상 없음
### 1-5. 기회비용 회수 후보 Top 5

**#1** — `latency guard miss`
- 차단 건수 합계: 57022건 | 차단 비율: 99.9% | 관찰 일수: 3일

**#2** — `AI threshold miss`
- 차단 건수 합계: 51205건 | 차단 비율: 99.9% | 관찰 일수: 3일

**#3** — `overbought gate miss`
- 차단 건수 합계: 24200건 | 차단 비율: 99.8% | 관찰 일수: 3일

**#4** — `liquidity gate miss`
- 차단 건수 합계: 2766건 | 차단 비율: 98.4% | 관찰 일수: 3일

---

## 2. 근거

### 2-1. 코호트 분리 이유

- `full_fill`, `partial_fill`, `split-entry`는 손익 구조가 달라 합치면 EV 해석이 왜곡된다.
- Plan Rebase 관찰축은 EV 패턴의 원인을 설명하는 보조 증거로만 사용한다.
- 따라서 report의 중심은 실현 EV, 패턴 기여손익, 기회비용 순으로 유지한다.

### 2-2. sequence_fact 관찰

- rebase_integrity_flag: 0건
- partial_then_expand_flag: 0건
- same_symbol_repeat_flag: 0건
- same_ts_multi_rebase_flag: 0건

## 3. 다음 액션

### 3-1. EV 개선 우선순위

- `latency guard miss EV 회수 조건 점검`
  검증지표: 차단건수=57022, 차단비율=99.9%
- `AI threshold miss EV 회수 조건 점검`
  검증지표: 차단건수=51205, 차단비율=99.9%

### 3-2. Plan Rebase 연계 관찰

- HOLDING 발생 이후에는 `post_sell_feedback`과 `trade_review`를 함께 묶어 EV 해석을 보강한다.
- `WAIT65~79 -> submitted`가 끊겨 있으면 threshold 완화보다 제출 병목 원인 분리가 우선이다.
- `gatekeeper latency`는 EV 회수 실패 원인인지 성능 병목인지 분해 후 축 우선순위를 정한다.
