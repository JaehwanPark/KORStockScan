# Gemini EV Pattern Analysis Report

## 1. EV 관점 핵심 판정

- 목적: EV 성과를 극대화하기 위한 튜닝 포인트를 코호트/패턴/기회비용 기준으로 점검한다.
- 보조 관찰축: Plan Rebase 이후 `WAIT65~79`, `blocked_ai_score`, `gatekeeper latency`, `submitted` 단절을 함께 본다.

## 2. Plan Rebase 관찰축 요약

- `WAIT65~79 total_candidates=163`
- `recovery_check=0`, `promoted=0`, `submitted=0`
- `blocked_ai_score_share=79.8%`, `gatekeeper_eval_ms_p95=5831ms`

## 3. 손실 패턴 (Top 5)

- 분석 대상 없음
## 4. 수익 패턴 (Top 5)

- 분석 대상 없음
## 5. 기회비용 분해

### 1. AI threshold miss
- 판정: EV 회수 우선 후보
- 근거: 차단건수 4658574건, 차단비율 100.0%, 관찰일수 31일
- 다음 액션: blocker 성격을 관찰축과 연결해 원인 귀속

### 2. overbought gate miss
- 판정: EV 회수 우선 후보
- 근거: 차단건수 1516814건, 차단비율 100.0%, 관찰일수 31일
- 다음 액션: blocker 성격을 관찰축과 연결해 원인 귀속

### 3. liquidity gate miss
- 판정: EV 회수 우선 후보
- 근거: 차단건수 89290건, 차단비율 99.6%, 관찰일수 31일
- 다음 액션: blocker 성격을 관찰축과 연결해 원인 귀속

### 4. latency guard miss
- 판정: EV 회수 우선 후보
- 근거: 차단건수 64641건, 차단비율 99.5%, 관찰일수 31일
- 다음 액션: blocker 성격을 관찰축과 연결해 원인 귀속
