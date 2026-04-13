# 스캘핑 HOLDING AI 프롬프트 최종 통합 설계안

## 문서 목적

본 문서는 시스템 트레이딩 전문가 3인의 스캘핑 HOLDING 프롬프트 재설계안을 종합해, 현재 `KORStockScan` GitHub 코드베이스에 가장 정합적인 최종 설계안으로 재구성한 문서다.

이번 설계의 기준은 3가지다.

1. 스캘핑이므로 AI 실행은 반드시 경량이어야 한다.
2. 현재 코드 구조를 존중해야 한다.
3. 프롬프트 분리와 데이터 주입은 한 번에 전부 바꾸지 않고 단계적으로 적용해야 한다.

---

## 1. 현재 코드 기준 문제 정의

현재 라이브 Gemini 경로는 스캘핑에서 `SCALPING_SYSTEM_PROMPT`를 공용으로 사용한다.  
즉, WATCHING과 HOLDING이 사실상 같은 질문 구조를 공유한다.

또한 `cache_profile="holding"`은 프롬프트를 바꾸는 장치가 아니라 캐시 키/TTL을 조정하는 용도에 가깝다.  
따라서 현재 HOLDING은 “보유 판단 전용 프롬프트”가 아니라 “진입 판단 프롬프트를 HOLDING에서도 재사용하는 구조”다.

추가로 현재 `_format_market_data()`는 여전히 다음을 길게 주입한다.

- raw 분봉 시계열
- raw 호가창
- 최근 10틱 상세 원본

이 구조는 스캘핑 HOLDING 경로에는 무겁다.

또 현재 `SCALP_PRESET_TP` 1회 AI 검문은 action 비교식과 프롬프트 스키마가 맞지 않는다.  
코드는 `SELL`을 보지만, 현행 스캘핑 프롬프트는 `BUY | WAIT | DROP`만 반환한다.

---

## 2. 최종 통합 설계 원칙

## 2-1. 질문을 분리한다

WATCHING의 질문은 아래다.

- 지금 신규 진입할 타점인가

HOLDING의 질문은 아래다.

- 지금 보유를 유지할까
- 수익 보호를 위해 정리할까
- 즉시 탈출해야 할까

따라서 HOLDING은 WATCHING 프롬프트를 재사용하면 안 된다.

---

## 2-2. HOLDING은 해석만 하고 계산은 미리 끝낸다

HOLDING 경로에서는 LLM이 직접 계산하면 안 된다.

원칙은 아래와 같다.

- raw 분봉/틱/호가 원본은 HOLDING에서 제거 또는 최소화
- 이미 계산된 정량 수치만 넣는다
- 포지션 컨텍스트를 먼저 넣는다
- action은 짧고 명확하게 유지한다
- reason은 1줄만 허용한다

---

## 2-3. HOLDING은 3개 경로로 나눈다

최종 통합안은 HOLDING을 아래 3개 경로로 나눈다.

### A. HOLDING_GENERAL
- 목적: 일반 보유 유지 vs 일반 청산 판단
- 호출 주기: 기존 HOLDING 리뷰 주기 유지
- 속도 우선순위: 중간
- 입력: 포지션 컨텍스트 + 핵심 수급 정량값

### B. HOLDING_CRITICAL
- 목적: 3~10초 재판단 구간에서 즉시 탈출 여부 판단
- 호출 구간: `profit_rate >= 0.5%` 또는 `profit_rate < 0`
- 속도 우선순위: 최우선
- 입력: 최소 정량셋만 사용

### C. PRESET_TP
- 목적: `profit_rate >= 0.8%` 구간 1회 AI 검문
- 역할: 익절 연장 vs 즉시 청산
- 속도 우선순위: 매우 높음
- 입력: 최소 3~5개 수치만 사용

---

## 3. 최종 action 설계

## 3-1. WATCHING action
WATCHING은 기존 유지가 맞다.

- `BUY`
- `WAIT`
- `DROP`

---

## 3-2. HOLDING_GENERAL / HOLDING_CRITICAL action
최종 통합안은 `WATCH`를 별도 action으로 두지 않는다.  
그 이유는 아래와 같다.

- 경량성 유지
- 구현 복잡도 축소
- 현재 시스템이 이미 `score`를 평활화해 사용하고 있으므로 중간 상태는 score로 표현 가능
- action 종류를 늘리면 override 규칙도 함께 복잡해진다

따라서 HOLDING action은 아래 3개로 고정한다.

- `HOLD`
- `SELL`
- `FORCE_EXIT`

### score 해석
- `0~20`: 즉시 탈출 성향 매우 강함
- `21~44`: 청산 우세
- `45~64`: 애매함 / 중립
- `65~84`: 홀드 우세
- `85~100`: 강한 홀드

핵심은 WATCHING score와 HOLDING score를 같은 의미로 해석하지 않는 것이다.

---

## 3-3. PRESET_TP action
`SCALP_PRESET_TP`는 HOLDING action을 그대로 쓰지 않고 전용 action으로 분리한다.

- `EXTEND`
- `EXIT`

이렇게 분리하는 이유는 현재 코드의 `SELL/DROP` 불일치를 가장 깔끔하게 해소하기 위해서다.

---

## 4. 최종 프롬프트 구조

## 4-1. SCALPING_HOLDING_SYSTEM_PROMPT

프롬프트 목적은 아래 한 문장으로 정리한다.

“신규 진입 여부가 아니라, 이미 보유 중인 스캘핑 포지션을 지금 유지할지, 정리할지, 즉시 탈출할지를 판단한다.”

프롬프트 핵심 원칙은 아래와 같다.

1. 현재 손익보다 최고 수익 대비 되밀림을 더 중요하게 본다.
2. 보유 시간이 길어지는데 모멘텀이 이어지지 않으면 보유 기대값이 낮다.
3. 수급 둔화는 청산 신호다.
4. 포지션 태그에 따라 보유 허용 폭이 다를 수 있다.
5. 신규 진입 관점으로 판단하지 않는다.
6. 출력은 JSON 한 개만 반환한다.

출력 필드는 아래로 고정한다.

- `action`
- `score`
- `reason`

---

## 4-2. HOLDING_CRITICAL_PROMPT

critical 경로는 더 짧아야 한다.

핵심 질문은 아래 한 줄이면 충분하다.

“현재 보유 포지션을 즉시 유지할지, 정리할지, 강제 탈출할지만 판단하라.”

판단 기준은 아래 5개만 본다.

- 최고 수익 대비 되밀림
- 체결 속도 둔화
- 최근 매수 압도율 약화
- 매도 잔량 증가
- 대량 매도틱

출력은 GENERAL과 동일하게 `HOLD | SELL | FORCE_EXIT`로 유지한다.

---

## 4-3. PRESET_TP_PROMPT

PRESET_TP는 더 작게 간다.

핵심 질문은 아래다.

“수익 중인 포지션에서 익절을 연장할지, 지금 바로 청산할지만 판단하라.”

출력은 아래로 고정한다.

- `EXTEND`
- `EXIT`

---

## 5. 최종 주입 데이터 설계

## 5-1. 공통 원칙

HOLDING에는 아래를 직접 넣지 않는다.

- 긴 raw 1분봉 배열
- 호가 1~5 전체 원본 배열
- 최근 10틱 상세 원본 전체
- 장황한 자연어 시장 설명

HOLDING에는 아래 3종만 넣는다.

- 포지션 정보
- 핵심 수급 정량값
- 현재 보호/청산 문맥

---

## 5-2. 1차 최소셋

첫 적용 최소셋은 아래 9개다.

- `profit_rate`
- `peak_profit`
- `drawdown_from_peak`
- `held_sec`
- `position_tag`
- `buy_pressure_10t`
- `tick_acceleration_ratio`
- `ask_depth_ratio`
- `large_sell_print_detected`

이 9개면 1차 HOLDING 분리의 최소 실행셋으로 충분하다.

---

## 5-3. HOLDING_GENERAL 권장 입력

일반 HOLDING은 아래를 사용한다.

- `curr_price`
- `buy_price`
- `profit_rate`
- `peak_profit`
- `drawdown_from_peak`
- `held_sec`
- `position_tag`
- `trailing_stop_price`
- `hard_stop_price`
- `ai_low_score_hits`
- `protect_profit_pct`
- `buy_pressure_10t`
- `tick_acceleration_ratio`
- `ask_depth_ratio`
- `large_sell_print_detected`
- `net_aggressive_delta_10t`
- `net_ask_depth`
- `distance_from_day_high_pct`

---

## 5-4. HOLDING_CRITICAL 권장 입력

critical 경로는 아래만 사용한다.

- `profit_rate`
- `peak_profit`
- `drawdown_from_peak`
- `held_sec`
- `position_tag`
- `buy_pressure_10t`
- `tick_acceleration_ratio`
- `ask_depth_ratio`
- `large_sell_print_detected`
- `net_aggressive_delta_10t`

---

## 5-5. PRESET_TP 권장 입력

PRESET_TP는 아래만 사용한다.

- `profit_rate`
- `peak_profit`
- `drawdown_from_peak`
- `buy_pressure_10t`
- `tick_acceleration_ratio`
- `large_sell_print_detected`
- `distance_from_day_high_pct`

---

## 6. 정량 피처 출처 원칙

최종 통합안은 OpenAI v2에 이미 구현된 정량 피처를 Gemini 경로로 이식하되, 엔진 클래스 직접 결합은 금지한다.

즉 아래 방향으로 구현한다.

- `ai_engine_openai_v2.py`의 `_extract_scalping_features()`를 참고
- 공통 `scalping_feature_helper.py`로 추출
- Gemini와 OpenAI가 공통 helper를 사용
- WATCHING/HOLDING에 같은 의미로 재사용

1차 이식 우선 피처는 아래다.

- `tick_acceleration_ratio`
- `buy_pressure_10t`
- `large_sell_print_detected`
- `net_aggressive_delta_10t`
- `ask_depth_ratio`
- `net_ask_depth`
- `distance_from_day_high_pct`

---

## 7. 시스템 해석 규칙

## 7-1. HOLDING_GENERAL / HOLDING_CRITICAL
초기에는 action-only로 전환하지 않는다.

### 기본 원칙
- `FORCE_EXIT`: 즉시 청산 후보
- `SELL`: 조건부 청산 후보
- `HOLD`: 기존 score 흐름 유지

### 운영 해석
- `FORCE_EXIT`는 override 후보
- `SELL`은 보호 수익률, 되밀림 폭, low-score 조건과 결합할 때만 override 후보
- 그 외는 기존 `smoothed_score` 중심 유지
- `reason`은 반드시 로그 저장

---

## 7-2. PRESET_TP
PRESET_TP는 전용 해석으로 간다.

- `EXIT`: 즉시 청산
- `EXTEND`: 기존 지정 익절 유지 또는 보호선 상향

현재 `['SELL', 'DROP']` 비교식은 최종적으로 `EXIT` 단일 비교로 바꾸는 것이 맞다.

---

## 8. 로그 설계

최종 통합안 적용 후 반드시 남길 로그는 아래다.

- `ai_prompt_type`
- `ai_prompt_version`
- `holding_context_payload_version`
- `holding_ai_action`
- `holding_ai_score`
- `holding_ai_reason`
- `preset_tp_ai_action`
- `preset_tp_ai_score`
- `preset_tp_ai_reason`
- `profit_rate_sent`
- `peak_profit_sent`
- `drawdown_from_peak_sent`
- `held_sec_sent`
- `position_tag_sent`
- `buy_pressure_10t_sent`
- `tick_acceleration_ratio_sent`
- `ask_depth_ratio_sent`
- `large_sell_print_detected_sent`
- `override_triggered`
- `override_rule_version`
- `ai_response_ms`
- `ai_parse_ok`

---

## 9. 최종 적용 순서

최종 설계는 아래 순서로 적용한다.

### Step 1
프롬프트 물리 분리만 먼저 한다.

- WATCHING
- HOLDING_GENERAL
- PRESET_TP 분리 초안
- 입력 데이터는 최소 변경

### Step 2
HOLDING 포지션 컨텍스트를 주입한다.

### Step 3
핵심 수급 정량 4~7개를 주입한다.

### Step 4
HOLDING_CRITICAL 경량 프롬프트를 분리한다.

### Step 5
PRESET_TP 전용 action을 `EXTEND/EXIT`로 전환한다.

### Step 6
override 규칙을 제한적으로 켠다.

### Step 7
그 후 raw 축소 A/B를 본다.

---

## 10. 최종 채택 요약

3개안을 종합한 최종 결론은 아래와 같다.

- 전체 방향은 설계안 1의 문제 정의를 채택한다.
- 경로 분리, PRESET_TP 전용 schema, 공통 feature helper는 설계안 2를 채택한다.
- 단계적 반영과 최소셋 우선은 설계안 3을 채택한다.

그리고 최종 통합 설계에서는 복잡도를 줄이기 위해 아래를 선택한다.

- HOLDING 일반/critical action은 `HOLD | SELL | FORCE_EXIT`
- PRESET_TP는 `EXTEND | EXIT`
- `WATCH`는 별도 action으로 두지 않고 score 구간으로 흡수
- raw 데이터 제거는 마지막 단계
- 정량 피처 helper 추출이 선행
- 프롬프트 분리와 payload 주입은 반드시 순차 진행

한 줄로 정리하면 아래와 같다.

**최종안은 “가벼운 HOLDING 전용 프롬프트 + 경로별 최소 payload + 전용 PRESET_TP schema + score/action 혼합 해석” 구조다.**
