# 스캘핑 AI 프롬프트·수급데이터 진단 검토결과

## 문서 목적

본 문서는 다음 3개 문서를 함께 검토한 결과를 바탕으로 작성했다.

- 원페이지 팩트 리포트
- 전문가 리뷰 1
- 전문가 리뷰 2

목적은 두 전문가의 의견이 **현재 코드 기준 사실과 얼마나 부합하는지**를 검증하고,  
그 결과를 바탕으로 **튜닝 전 반드시 점검해야 할 사항**과 **AI 판단 관련 개선 필요사항**을 우선순위로 정리하는 것이다.

---

## 1. 최종 결론

두 전문가의 핵심 문제 제기는 전반적으로 **타당하다**.  
특히 아래 4개는 단순 의견 수준이 아니라, 현재 구조상 우선 수정 또는 우선 검증이 필요한 핵심 이슈다.

1. **WATCHING 진입판단과 HOLDING 청산판단이 같은 프롬프트를 재사용하는 문제**
2. **HOLDING 경로에 포지션 컨텍스트가 거의 전달되지 않는 문제**
3. **SCALP_PRESET_TP 경로의 action 정의와 코드 비교식이 불일치하는 버그**
4. **현재 라이브 Gemini 경로에 정량형 수급 피처와 보유 맥락이 충분히 연결되지 않은 문제**

반면, 아래 항목은 방향은 맞지만 **즉시 단정하거나 일괄 전환하면 안 되는 조건부 타당 항목**이다.

- Raw 시계열/호가 원본을 즉시 대거 제거해야 한다는 주장
- HOLDING에서 곧바로 action 중심 청산으로 전면 전환해야 한다는 주장
- 정량형 OpenAI 경로가 더 풍부하므로 엔진 자체를 바로 갈아타야 한다는 해석

즉, 지금 필요한 것은 **프롬프트 재설계와 입력 데이터 구조 개선**이지,  
AI 엔진 교체나 대규모 로직 전환이 아니다.

---

## 2. 전문가 2인 검토의견 타당성 검증

## 2-1. 사실상 확정적으로 타당한 항목

### A. WATCHING과 HOLDING이 동일 프롬프트를 사용한다
**판정: 타당**

팩트 리포트상 현재 라이브 스캘핑은 WATCHING과 일반 HOLDING이 동일한 `SCALPING_SYSTEM_PROMPT`를 사용한다.  
`cache_profile="holding"`은 캐시 키/TTL 차이일 뿐 프롬프트 본문을 바꾸지 않는다.

**의미**  
진입판단용 질문과 보유/청산판단용 질문은 목적이 다르다.  
같은 프롬프트를 재사용하면 HOLDING AI는 사실상 “지금 새로 들어갈까?” 관점으로 판단하게 된다.

---

### B. HOLDING 프롬프트에 포지션 컨텍스트가 없다
**판정: 타당**

현재 HOLDING 경로에서 계산되는 `buy_price`, `profit_rate`, `peak_profit`, `held_sec`, `position_tag`, `trailing_stop_price`, `ai_low_score_hits` 등은 실제 청산 판단에는 매우 중요하지만 프롬프트에는 직접 들어가지 않는다.

**의미**  
AI는 아래를 모른 채 판단한다.

- 지금 수익 중인지 손실 중인지
- 이미 최고수익 대비 얼마나 밀렸는지
- 얼마나 오래 들고 있었는지
- 어떤 타입의 포지션인지
- 현재 보호선이 어디인지

이 상태에서는 “보유 유지 vs 즉시 청산”에 대한 정밀 판단이 불가능하다.

---

### C. SCALP_PRESET_TP action 정의 불일치는 버그에 가깝다
**판정: 타당**

코드 비교식은 `['SELL', 'DROP']`을 보지만, 현재 프롬프트는 `BUY | WAIT | DROP`만 반환하도록 정의되어 있다.  
즉 `SELL`은 현재 프롬프트상 절대 나오지 않는 값이다.

**의미**  
이 문제는 철학 논쟁이 아니라 **정의 불일치**다.  
먼저 아래 둘 중 하나로 통일해야 한다.

- 코드 기준을 `DROP`만 보도록 단순화
- 또는 HOLDING/SCALP_PRESET_TP 전용 프롬프트에서 `SELL`을 합법 action으로 추가

**2026-04-12 추가 판단**

- 현재 구현 단계에서는 `SELL`을 즉시 제거하지 않고 placeholder로 명시 보존한다.
- 이유는 `SCALP_PRESET_TP` 검문이 향후 전용 HOLDING/exit action 체계로 분리될 가능성을 남겨두되,
  현재 라이브 공유 프롬프트가 `BUY|WAIT|DROP`만 허용하는 사실을 로그와 주석으로 분명히 남기기 위해서다.
- 따라서 현재 실집행 규칙은 `DROP만 live path`, `SELL은 schema placeholder`로 본다.

---

### D. 라이브 Gemini 경로에 정량형 수급 피처가 충분히 연결되지 않았다
**판정: 타당**

팩트 리포트상 아래 데이터는 이미 코드베이스에 존재하지만 현재 라이브 Gemini 프롬프트에는 직접 들어가지 않는다.

- 프로그램 순매수/순매도 관련 값
- 잔량 변화율과 깊이 변화
- 체결량 세부 지표
- `buy_pressure_10t`
- `distance_from_day_high_pct`
- `intraday_range_pct`
- `tick_acceleration_ratio`
- `same_price_buy_absorption`
- `large_sell_print_detected`
- 기타 OpenAI v2 경로의 정량 피처

**의미**  
현재 프롬프트는 “설명은 정교한데 입력 정량값이 부족한 상태”다.  
즉, AI가 해석해야 할 핵심 수급 신호 일부를 사람이 문장으로만 유도하고 있다.

---

### E. 일반 HOLDING에서 AI action/reason이 실시간 청산에 직접 반영되지 않는다
**판정: 타당**

현재 일반 HOLDING 경로에서는 `action`과 `reason`을 직접 청산 트리거로 쓰지 않고, `score`만 평활화해서 사용한다.

**의미**  
이는 노이즈 완화에는 유리할 수 있으나,  
AI가 “지금은 즉시 탈출”이라고 판단한 이유가 있어도 실시간 의사결정에 반영되지 않는 구조다.  
따라서 HOLDING 전용 프롬프트를 만들더라도 **출력 구조와 사용 방식까지 같이 재설계**해야 의미가 있다.

---

## 2-2. 방향은 맞지만 조건부로 받아들여야 하는 항목

### F. Raw 원본 시퀀스를 크게 줄여야 한다
**판정: 조건부 타당**

전문가 의견처럼, LLM에게 긴 숫자 시퀀스와 호가 원본을 직접 해석시키는 것은 효율이 낮을 가능성이 높다.  
특히 HOLDING critical 경로에서는 경량화가 매우 유효할 수 있다.

다만 다음은 아직 증명되지 않았다.

- Raw 시퀀스가 실제로 응답 지연의 주원인인지
- Raw 일부가 WATCHING 정확도에 기여하고 있는지
- 어떤 경로에서 어느 정도 제거해야 손실이 없는지

**검토 결론**  
전면 제거가 아니라 **경로별 축소**가 맞다.

- WATCHING: 정량 피처를 먼저 추가하고 Raw는 보조로 유지
- 일반 HOLDING: 호가 원본을 축소하고 포지션 컨텍스트를 보강
- HOLDING critical / SCALP_PRESET_TP: 최소 입력셋 중심으로 경량화

---

### G. 정량형 OpenAI 경로가 더 우수하므로 바로 전환해야 한다
**판정: 조건부 타당**

OpenAI v2 경로에 정량 피처가 더 풍부하게 구현된 것은 사실이다.  
그러나 현재 라이브 엔진은 Gemini이며, OpenAI 경로는 shadow 계열이다.

**검토 결론**  
즉시 엔진 교체보다는 아래 순서가 맞다.

1. 현재 Gemini 경로에 필요한 정량 피처를 먼저 이식
2. 동일 입력 기준으로 Gemini vs OpenAI shadow 비교
3. 그 후 엔진 전환 여부를 판단

즉, 현 시점의 우선순위는 **엔진 교체가 아니라 입력 구조 표준화**다.

---

### H. HOLDING에서 action 중심 의사결정으로 바로 바꿔야 한다
**판정: 부분 타당**

현재처럼 점수만 쓰는 구조는 한계가 있다.  
그러나 곧바로 action 1회 응답만으로 청산을 전면 결정하게 바꾸면 노이즈에 취약할 수 있다.

**검토 결론**  
가장 합리적인 구조는 아래다.

- `score`는 추세/확신도 보조 신호
- `action`은 즉시 경보 또는 강한 청산 트리거 후보
- `reason`은 로그 및 사후 분석 근거
- 특정 조건에서만 `FORCE_EXIT`급 action을 즉시 실행

즉, **score-only → action-only**가 아니라 **혼합 구조**가 맞다.

---

## 2-3. 전문가 1 의견 중 특히 높은 품질로 보이는 항목

전문가 1 문서에는 아래처럼 코드와 운영정합성 측면에서 특히 유효한 지적이 포함되어 있다.

### 1) 프롬프트 스코어 구간과 실제 진입 임계값 불일치
현재 프롬프트는 `80~100 = BUY`인데 실제 진입 기준은 `>= 75`다.  
이는 AI 판단 체계와 시스템 해석 기준의 구조적 어긋남이다.

### 2) AI 호출 시점에 이미 통과된 기계 게이트 정보 미전달
AI는 이미 통과된 강도/유동성/추격률 조건을 모른다.  
따라서 AI에게 “지금은 타점 해석만 하라”는 문맥이 부족하다.

### 3) `AI_WATCHING_COOLDOWN=180초`, Big-Bite 가점, parse fail 후 50점 처리
이 3개는 모두 AI 품질 진단에서 빠지면 안 되는 운영 파라미터다.  
특히 50점 폴백 비중이 높다면 AI 품질 문제가 아니라 파싱/출력 안정성 문제일 수 있다.

---

## 3. 튜닝 전 점검해야 하는 사항 우선순위

## P1. 즉시 점검 및 수정해야 할 항목

### 1. SCALP_PRESET_TP action 정의 통일
- 프롬프트와 코드 비교식을 같은 스키마로 맞춘다.
- `SELL`을 쓸지, `DROP`만 쓸지 먼저 결정한다.

### 2. WATCHING 스코어 체계와 라이브 진입 임계값 정합성 점검
- 프롬프트: `80~100 BUY`
- 시스템: `>=75 진입`
- 둘 중 하나를 수정해야 한다.

### 3. HOLDING 전용 프롬프트 분리 여부를 확정
이 항목은 선택사항이 아니라 사실상 구조 개선의 시작점이다.

---

## P2. 바로 계측하고 설계에 반영해야 할 항목

### 4. HOLDING에서 실제로 필요한 포지션 컨텍스트 정의
최소 포함 대상:

- `buy_price`
- `profit_rate`
- `peak_profit`
- `held_sec`
- `position_tag`
- `trailing_stop_price`
- `hard_stop_price`
- `ai_low_score_hits`
- `exit_mode`

### 4-1. 2026-04-12 P0 운영계측 반영

다음 값은 우선 운영 로그 기준으로 분리 관측한다.

- `ai_parse_ok`
- `ai_parse_fail`
- `ai_fallback_score_50`
- `ai_response_ms`
- `ai_prompt_type`
- `ai_result_source`
- `ai_score_raw`
- `ai_score_after_bonus`
- `entry_score_threshold`
- `big_bite_bonus_applied`
- `ai_cooldown_blocked`

해석 원칙:

- `score=50`만으로 AI 품질 저하로 단정하지 않는다.
- `parse_fail`, `cooldown`, `lock_contention`, `cache_hit`을 별도 축으로 분리한다.
- Big-Bite 보정 전후를 나눠야 실제 AI 본판단과 운영가점 효과를 분리 해석할 수 있다.

### 5. WATCHING에서 AI에게 전달할 기계 선통과 조건 정의
최소 포함 대상:

- 동적 체결강도 PASS 여부와 핵심 수치
- 유동성 PASS 여부
- 추격률 PASS 여부
- `target_buy_price`
- `gap_pct`
- `threshold_profile`
- `momentum_tag`

### 6. 현재 감사용 값 중 즉시 프롬프트에 올릴 값 선별
가장 우선순위가 높은 값:

- `buy_pressure_10t`
- `distance_from_day_high_pct`
- `intraday_range_pct`

---

## P3. 2주 내 구조 개선으로 묶어야 할 항목

### 7. 정량형 수급 피처 이식
우선순위 높은 입력:

- `tick_acceleration_ratio`
- `same_price_buy_absorption`
- `large_sell_print_detected`
- `net_ask_depth`
- `ask_depth_ratio`
- `prog_net_qty`
- `prog_delta_qty`

## 4. HOLDING hybrid override 기준 (2026-04-12 초안)

현 단계 권고는 `score-only -> action-only` 전환이 아니라 `문서화된 예외 override + score 기본 유지`다.

1. `FORCE_EXIT`
- 일반 HOLDING에서도 즉시 청산 후보로 인정
- 단, 최소한 `profit_rate`, `peak_profit_retrace`, 시장악화 신호를 함께 본다

2. `SELL`
- 1차 canary에서는 즉시집행 금지
- 강한 경고 action으로만 기록하고, 실제 청산은 score/보호선/하드스탑과 교차 확인

3. `DROP`
- `SCALP_PRESET_TP` 전용 검문에서는 즉시 청산 허용
- 일반 HOLDING에는 그대로 이식하지 않는다

4. `reason`
- 실행조건이 아니라 로그/리포트용 근거

5. 기본 원칙
- override 조건을 만족하지 않으면 `smoothed_score` 중심 로직 유지
- `net_aggressive_delta_10t`

### 8. 경로별 입력셋 분리
- WATCHING: 정확도 중심
- 일반 HOLDING: 포지션 관리 중심
- HOLDING critical: 속도 중심 최소 입력셋
- SCALP_PRESET_TP: 출구 검문 전용 최소 입력셋

### 9. HOLDING에서 action/reason 활용 방식 재설계
- 점수만 사용하던 구조를 보완
- 즉시청산, 보호선 상향, 홀드 유지의 분기 기준을 정한다.

---

## P4. 운영 계측 우선 항목

### 10. Gemini JSON 파싱 실패율 집계
- parse fail 비율
- 50점 폴백 비율
- 변동성 급등 구간과의 상관관계

### 11. AI_WATCHING_COOLDOWN으로 인한 missed entry 점검
- 쿨다운 중 기계게이트 통과 후 대기 건수
- `entry_armed` 만료와 AI 호출 간격의 상관관계

### 12. Big-Bite 가점이 AI 판단 우회 경로로 작동하는지 점검
- +5 / +2 가점 전후 score 분포
- 70점대 종목이 가점으로 75 이상이 되는 비중

### 13. WATCHING 75 shadow canary 집계
- `watching_prompt_75_shadow` 로그를 전용 집계로 분리한다.
- `src/engine/watching_prompt_75_shadow_report.py` 기준으로 아래 3개를 같이 본다.
- `buy_diverged`
- `75~79` 분포
- `buy_diverged / score_band x MISSED_WINNER` 교차표
- 해석 원칙:
- `shadow BUY`가 늘어도 `MISSED_WINNER` 개선 근거 없이 바로 본서버 반영하지 않는다.
- `buy_diverged=true` 표본의 `missed_winner_rate`, `avg_close_10m_pct`, `estimated_counterfactual_pnl_10m_krw`를 함께 본다.
- `2026-04-13 10:43 KST` 중간관찰:
  - 최근 3일 `eligible_shadow(75~79, non-BUY, non-fallback)`는 `0 / 1 / 0`이다.
  - 즉 현재 `shadow_samples=0`의 1차 원인은 기능 미기동이 아니라 `band 자체 희소성`이다.
  - `WAIT 65`는 최근 3일 `286건`, counterfactual join `85건` 중 `MISSED_WINNER=62`라서 다음 의사결정은 `75` band보다 `65 WAIT` 해석 강화가 더 중요하다.
  - `fallback50`는 최근 3일 `4건`이며 전부 `ai_result_source=cooldown`이라 파싱 실패와 구분해 읽어야 한다.
  - `WAIT 65` joined 표본의 `terminal_stage x outcome`은 `latency_block -> MISSED_WINNER 50 / AVOIDED_LOSER 20`, `blocked_strength_momentum -> MISSED_WINNER 11`, `blocked_liquidity -> MISSED_WINNER 1`이다.
  - 같은 표본에서 `overbought_blocked=True`는 `0건`이라 현재 missed-winner 축은 `overbought`보다 `latency/strength` 쪽이 우세하다.

---

## 4. AI 판단 관련 개선 필요사항 우선순위

## 1순위. 진입용/보유용 프롬프트 완전 분리
가장 큰 구조적 개선 포인트다.

- WATCHING은 “지금 탑승해도 되는가?”
- HOLDING은 “지금 유지해야 하는가, 줄여야 하는가, 즉시 나가야 하는가?”

질문이 다르면 프롬프트도 달라야 한다.

---

## 2순위. action 스키마와 점수체계 재정의
경로별로 action과 score 의미를 명확히 분리해야 한다.

예시:

- WATCHING: `BUY | WAIT | DROP`
- HOLDING: `HOLD | SELL | FORCE_EXIT`

그리고 각 경로에서 score가 의미하는 바도 따로 정의해야 한다.

---

## 3순위. HOLDING에 포지션 컨텍스트 주입
이 항목이 빠지면 HOLDING AI 튜닝은 사실상 무의미하다.

핵심은 다음 3개다.

- 현재 손익
- 최고수익 대비 현재 위치
- 보유 시간과 포지션 태그

---

## 4순위. WATCHING에 기계 선통과 문맥을 명시
AI는 이미 검증된 조건을 다시 의심하는 역할이 아니라,  
**지금 이 순간 타점 해석**에 집중해야 한다.

---

## 5순위. 정량형 수급 피처 중심 입력으로 재구성
자연어 원칙을 정량값으로 연결해야 판단 일관성이 오른다.

핵심 연결 예시:

- Ask Eating → `same_price_buy_absorption`, `ask_depth_ratio`
- 속도 저하 → `tick_acceleration_ratio`, `recent_5tick_seconds`
- 위치 판단 → `distance_from_day_high_pct`, `curr_vs_micro_vwap_bp`

---

## 6순위. HOLDING critical 경로 경량 프롬프트 분리
3~10초 단위 재검토 구간에서는 최소 입력셋이 유리하다.  
여기서는 해석보다 반응 속도가 더 중요하다.

---

## 7순위. score-only 구조를 혼합형으로 전환
- `score`: 확신도/추세강도
- `action`: 직접 의사결정 후보
- `reason`: 사후분석 및 디버깅

---

## 8순위. 파싱 안정성과 폴백 영향 계측
모델 품질을 보기 전에 출력 안정성을 먼저 봐야 한다.  
50점 폴백이 많으면 AI 판단력보다 프롬프트/파서 구조가 먼저 문제다.

---

## 5. 최종 판단

이번 검토의 핵심은 “AI가 똑똑하냐”가 아니다.  
핵심은 **현재 시스템이 AI에게 맞는 질문을 하고 있는가**,  
그리고 **판단에 필요한 수급·포지션 정보를 제대로 주고 있는가**다.

현재 상태에서는 아래 3가지가 가장 먼저 정리되어야 한다.

1. **진입 프롬프트와 보유 프롬프트 분리**
2. **SCALP_PRESET_TP action 불일치 수정**
3. **정량형 수급 피처와 포지션 컨텍스트의 단계적 주입**

이 3가지가 정리되면, 그 다음부터는 AI 판단 정확도·속도·일관성에 대한 튜닝이 실제 의미를 갖게 된다.
