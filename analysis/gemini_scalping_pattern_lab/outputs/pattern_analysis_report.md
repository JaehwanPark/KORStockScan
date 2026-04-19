# Pattern Analysis Report

## 1. 손실 패턴 (Loss Patterns)

### 1) Fallback 진입 후 Soft Stop 손실 (`fallback_scalp_soft_stop_pct`)
- 판정: 가장 빈번하고 타격이 큰 최악의 손실 패턴.
- 근거: 발생 25건, 평균 수익률 -1.647%, 총 기여손익 -41.18%. 지연 진입(Fallback) 후 돌파에 실패하고 가격이 질질 흐르다 손절됨.
- 다음 액션: Fallback 진입 로직에서 체결강도/모멘텀이 이미 꺾인 경우 진입을 아예 포기하도록 필터 강화.

### 2) Partial Fill 후 Soft Stop 손실 (`partial_scalp_soft_stop_pct`)
- 판정: 유동성 부족으로 인한 가짜 돌파(Fake Breakout) 패턴.
- 근거: 발생 10건, 평균 수익률 -1.671%, 총 기여손익 -16.71%. 지정가에 물량이 충분히 체결되지 못했다는 것은 매수세가 약하다는 증거임. 이후 하락 반전하며 손절.
- 다음 액션: Partial Fill 직후 특정 시간(예: 3초) 내에 추가 매수세가 안 붙으면 즉시 본절/약손절 탈출(Trailing Stop 타이트하게 조정)하는 로직 적용.

### 3) Full Fill 후 Soft Stop 손실 (`full_scalp_soft_stop_pct`)
- 판정: 고점 매수(추격 매수) 실패 패턴.
- 근거: 발생 7건, 평균 수익률 -1.66%, 총 기여손익 -11.62%. 거래량은 터졌으나 고점 저항에 막히는 케이스.
- 다음 액션: 호가창 매도 잔량(Resistance)과 현재가의 거리를 고려해 Overbought 게이트 임계값 세부 조정.

### 4) Partial Fill 후 Hard Stop 타격 (`partial_scalp_preset_hard_stop_pct`)
- 판정: 급락장(Flash Crash) 대피 지연 패턴.
- 근거: 발생 12건, 평균 수익률 -0.713%, 총 기여손익 -8.55%. 부분 체결 직후 시장가로 던지는 매도세에 휩쓸려 기계적 손절에 도달.
- 다음 액션: Partial Fill 이후 호가 잔량 비율(매도잔량 급증) 모니터링을 통한 선제적 Hard Stop 발동.

### 5) Fallback 진입 후 Hard Stop 타격 (`fallback_scalp_preset_hard_stop_pct`)
- 판정: 뒤늦은 추격 매수가 급락을 맞는 패턴.
- 근거: 발생 7건, 평균 수익률 -0.733%, 총 기여손익 -5.13%. 
- 다음 액션: Fallback 모드 진입 자체를 허용하는 최대 지연시간(Latency) 기준을 더 보수적으로 단축.


## 2. 수익 패턴 (Profit Patterns)

### 1) Fallback 진입 후 Trailing Take Profit (`fallback_scalp_trailing_take_profit`)
- 판정: 눌림목 지연 진입이 주효한 최고 기여 수익 패턴.
- 근거: 발생 21건, 평균 수익률 1.1%, 기여손익 23.09%. Fallback이 무조건 나쁜 것이 아니라, 지연 진입 시 하락하지 않고 버티면 큰 추세를 먹음.
- 다음 액션: Fallback 진입 직후의 틱 모멘텀을 분석하여, 모멘텀 유지 시 Trailing Stop의 여유폭을 넓게 가져가 수익 극대화.

### 2) Partial Fill 후 Trailing Take Profit (`partial_scalp_trailing_take_profit`)
- 판정: 매물대를 뚫고 올라가는 전형적인 강한 돌파 패턴.
- 근거: 발생 21건, 평균 수익률 1.021%, 기여손익 21.44%. 부분 체결 이후 곧바로 가격이 상승하며 Trailing Stop으로 수익을 잠금.
- 다음 액션: Partial Fill 직후 강한 상승이 확인되면 Split-Entry(불타기)로 추가 물량을 확보하는 로직 섀도우 검증.

### 3) Full Fill 후 AI Review Exit (`full_scalp_preset_ai_review_exit`)
- 판정: 가장 품질이 좋은 정석 수익 패턴.
- 근거: 발생 5건, 평균 수익률 1.758%, 기여손익 8.79%. 모든 조건이 맞아떨어져 전량 체결되고, AI가 고점 둔화를 정확히 인식하고 청산함.
- 다음 액션: 해당 조건(AI 스코어 상위 5% + Full Fill)에서는 목표가(Take Profit)를 상향 조정.

### 4) Partial/Fallback 진입 후 AI Momentum Decay Exit
- 판정: AI의 훌륭한 추세 반전 사전 차단 방어.
- 근거: 총 발생 9건, 수익률 약 0.6% ~ 1.18%. 급락이 오기 전 AI가 모멘텀 감소를 인지해 수익을 지켜냄.
- 다음 액션: AI Momentum Decay 트리거의 민감도를 높여 다른 Soft Stop 손실 케이스들을 이 패턴으로 유도할 수 있는지 검증.


## 3. 기회비용 분석 (Opportunity Costs)

- 판정: AI Threshold 및 Overbought 게이트의 과도한 차단으로 인한 기회 상실.
- 근거: 일별 평균 20만 건 이상의 AI Threshold 블록과 5만~10만 건의 Overbought 블록 발생. 반면 실제 진입(Submitted)은 수십 건에 불과함.
- 다음 액션: AI Score 임계값을 소폭 하향하거나, 단기 체결강도가 극단적으로 높은 경우 Overbought 게이트를 예외적으로 통과시키는 "Dynamic Threshold" 도입 필요.
