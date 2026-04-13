# 스캘핑 AI 프롬프트 정밀 튜닝 점검 리포트

> **작성 기준일:** 2026-04-11  
> **점검 범위:** WATCHING 진입판단 프롬프트 / HOLDING 청산판단 프롬프트 / 입력 데이터 구성 / 판단 속도 vs 정확도 스윗스팟  
> **주 AI 엔진:** GeminiSniperEngine (라이브 의사결정)  
> **참조:** OpenAIDualPersonaShadowEngine (shadow-only, 본 점검의 비교 기준으로 활용)

---

## 목차

1. [핵심 결함 요약](#1-핵심-결함-요약)
2. [WATCHING 진입판단 프롬프트 점검](#2-watching-진입판단-프롬프트-점검)
3. [HOLDING 청산판단 프롬프트 점검](#3-holding-청산판단-프롬프트-점검)
4. [입력 데이터 갭 분석](#4-입력-데이터-갭-분석)
5. [정확도 vs 판단속도 스윗스팟 분석](#5-정확도-vs-판단속도-스윗스팟-분석)
6. [추가 검토가 필요한 사항](#6-추가-검토가-필요한-사항)
7. [제안사항 및 우선순위](#7-제안사항-및-우선순위)

---

## 1. 핵심 결함 요약

| # | 결함 | 위치 | 심각도 |
|---|---|---|---|
| A | WATCHING과 HOLDING이 동일 프롬프트 사용 | 프롬프트 설계 | ★★★★★ |
| B | HOLDING 프롬프트에 포지션 컨텍스트 전무 | 데이터 입력 | ★★★★★ |
| C | SCALP_PRESET_TP 경로의 action 정의 불일치 | 로직 버그 | ★★★★★ |
| D | 정량형 OpenAI 피처셋이 라이브에 미연결 | 아키텍처 | ★★★★ |
| E | 프로그램·체결량·잔량변화 미입력 | 데이터 입력 | ★★★★ |
| F | HOLDING AI score만 사용, action/reason 미사용 | 판단 구조 | ★★★ |
| G | HOLDING 전용 청산 threshold가 프롬프트 미입력 | 데이터 입력 | ★★★ |

---

## 2. WATCHING 진입판단 프롬프트 점검

### 2-1. 현재 프롬프트 구조 평가

현재 `SCALPING_SYSTEM_PROMPT`의 설계 방향은 올바르다. 스캘핑 철학(돌파 직전 탑승, 1~2% 목표, 칼손절)을 명확히 정의하고, 3원칙(Ask Eating, 속도 저하 도망, 위치 우선)을 구체적으로 명시하고 있다. JSON 형식 강제와 `reason` 1줄 요약 구조도 파싱 신뢰성 면에서 적절하다.

**그러나 세 가지 구조적 문제가 있다.**

---

### 2-2. 문제 A — 스코어링 구간과 진입 임계값의 불일치

현재 프롬프트 정의:

```
80~100 → BUY
50~79  → WAIT
0~49   → DROP
```

현재 라이브 진입 임계값: `current_ai_score >= 75`

**문제:** 프롬프트는 `80점 이상`을 BUY로 정의하는데, 시스템은 `75점 이상`에서 진입을 허용한다. 즉 AI가 WAIT으로 분류한 75~79점 구간이 실제로는 진입 트리거가 된다. AI의 판단 체계와 시스템의 진입 기준이 5점 구간에서 구조적으로 어긋나 있다.

**권고:**
프롬프트 스코어링 구간을 실제 진입 임계값에 맞춰 재정렬하거나, 진입 임계값을 80으로 상향 조정하는 방향 중 하나를 선택해야 한다. 현재처럼 두 기준이 불일치한 상태에서는 AI가 자신의 기준에 맞게 스코어를 산출해도 시스템이 다른 기준으로 해석한다.

```
권고 옵션 1 — 프롬프트 재정렬:
  75~100 → BUY (강한 진입 신호)
  50~74  → WAIT
  0~49   → DROP

권고 옵션 2 — 임계값 상향:
  진입 임계값을 80으로 올리고 75~79는 WAIT 처리
```

---

### 2-3. 문제 B — AI 호출 시점에 이미 통과한 기계 게이트 정보 미전달

AI가 호출될 시점은 이미 다음을 통과한 후다:
- 동적 체결강도 게이트(`evaluate_scalping_strength_momentum()`)
- Big-Bite 게이트
- 유동성 게이트
- 추격률 게이트(`gap_pct < 1.5%`)

그런데 AI는 이 정보를 모른다. AI 입장에서는 아무 종목이나 들어온 것처럼 보인다.

**문제:** AI가 이미 검증된 조건을 재검토하는 데 판단 자원을 낭비하거나, 실제로는 통과된 기계 조건을 프롬프트 데이터만 보고 반대로 평가하는 역방향 오판이 발생할 수 있다.

**권고:** 프롬프트 도입부에 사전 통과 조건을 명시적으로 전달한다.

```
[사전 검증 완료 조건 - 이미 기계가 확인함]
- 동적 체결강도: PASS (window_buy_ratio: {값}, threshold_profile: {프로파일명})
- 유동성: PASS ({liquidity_value}원)
- 추격률: PASS (scanner 대비 {gap_pct}% 이내)
- 목표 매수가: {target_buy_price}원 (현재가 {curr_price}원)

위 조건은 기계가 이미 검증했다. 너는 아래 시장 데이터를 보고
'지금 이 순간의 타점'만 판단해라.
```

---

### 2-4. 문제 C — 위치 판단 지표의 정의 불일치

프롬프트 3원칙의 "위치" 조건:

> *"현재가가 Micro-VWAP 아래에 있거나, 당일 최고가를 찍고 줄설거지가 나오는 역배열 패턴이라면 절대 진입하지 마라"*

그런데 실제 입력 데이터에는 `Micro-VWAP` 수치는 들어가지만 `당일 최고가 대비 이격도`(`distance_from_day_high_pct`)는 들어가지 않는다. AI가 판단 근거로 명시한 지표를 실제로 받지 못하는 것이다.

**권고:** `distance_from_day_high_pct`와 `intraday_range_pct`를 즉시 입력 데이터에 추가한다. 이 두 값은 이미 계산되어 있으나 감사용 로그에만 남기고 있다.

---

## 3. HOLDING 청산판단 프롬프트 점검

### 3-1. 가장 심각한 설계 결함 — 진입판단 프롬프트의 청산 재사용

현재 라이브 HOLDING 리뷰는 WATCHING과 동일한 `SCALPING_SYSTEM_PROMPT`를 사용한다. 이 프롬프트는 "돌파 직전의 찰나에 탑승"을 판단하기 위해 설계된 것이다.

**보유 중 AI에게 묻는 실제 질문과 프롬프트의 설계 목적이 전혀 다르다.**

| 구분 | WATCHING이 묻는 것 | HOLDING이 실제로 묻고 싶은 것 |
|---|---|---|
| 핵심 질문 | 지금 탑승할 타점인가? | 지금 탈출할 시점인가? |
| 시간 지평 | 향후 수십 초~수분 | 지금 이 순간 |
| 포지션 인식 | 없음 (진입 전) | 있음 (+1.2%, 보유 3분, 최고 +1.8%) |
| 판단 기준 | 모멘텀 가속 여부 | 모멘텀 유지/소멸 여부 |

**현재 AI는 자신이 포지션을 보유 중이라는 사실조차 모른 채 청산 판단에 관여하고 있다.**

---

### 3-2. HOLDING 프롬프트에 들어가야 하지만 현재 미입력인 포지션 데이터

다음 데이터는 이미 `handle_holding_state()`에서 계산되어 있으나 프롬프트에 전달되지 않는다.

```
[현재 미입력 포지션 컨텍스트]
- buy_price         : 진입가
- profit_rate       : 현재 손익률
- peak_profit       : 최고 수익률 (고점 대비 현재 위치 파악용)
- held_sec          : 보유 시간 (초)
- trailing_stop_price : 현재 트레일링 스탑가
- hard_stop_price   : 하드 스탑가
- ai_low_score_hits : 연속 저점수 횟수
- exit_mode         : 현재 청산 모드
- position_tag      : 포지션 태그 (OPEN_RECLAIM / SCANNER / fallback 등)
- protect_profit_pct : 보호 수익률
```

**이 정보 없이 AI는 "지금 모멘텀이 있냐"라는 진입 판단만 할 수 있다. "지금 들고 있는 포지션을 유지해야 하냐"는 판단은 불가능하다.**

---

### 3-3. SCALP_PRESET_TP 경로의 action 정의 불일치 — 로직 버그

현재 코드:
```python
# SCALP_PRESET_TP 경로의 즉시 청산 비교식
if action in ['SELL', 'DROP']:
    즉시청산()
```

현재 프롬프트 정의:
```json
"action": "BUY" | "WAIT" | "DROP"
```

**`SELL`은 프롬프트 상에 존재하지 않는 action이다.** AI가 절대 반환하지 않는 값을 청산 조건으로 비교하고 있다. 실질적으로 `DROP`만 청산 트리거로 작동하는데, 이것이 의도된 설계인지 버그인지 불분명하다.

만약 HOLDING 청산에 더 공격적인 조기 탈출 조건이 필요하다면 `SELL`을 프롬프트에 추가해야 하고, 불필요하다면 비교식에서 `SELL`을 제거해야 한다. 현재는 두 코드가 서로 모순된 상태다.

---

### 3-4. HOLDING에서 AI score만 사용하는 구조의 한계

현재 일반 HOLDING에서는 AI의 `action`과 `reason`을 직접 사용하지 않고 `smoothed_score`만 사용한다.

```
smoothed_score = 기존 score * 0.6 + 신규 raw score * 0.4
```

이 설계의 의도(평활화로 노이즈 감소)는 이해할 수 있다. 그러나 결과적으로 AI의 `reason`(판단 근거)은 로그에만 남고 실제 청산 결정에 전혀 반영되지 않는다. AI가 "대량 매도 틱 감지, 즉시 탈출 권고"라고 `reason`에 써도 시스템은 score 수치만 읽는다.

**권고:** HOLDING 전용 프롬프트를 별도 설계하면서, `action`을 직접 청산 트리거로 사용하는 로직을 추가한다. 단 기존 `smoothed_score` 로직은 보조 신호로 유지한다.

---

## 4. 입력 데이터 갭 분석

### 4-1. 즉시 추가 가능한 고가치 미입력 데이터

아래 데이터는 이미 계산되어 있으며 입력 데이터 구성 코드(`_format_market_data()`)에 추가만 하면 된다.

#### WATCHING에서 즉시 추가 권고

| 데이터 | 위치 | 스캘핑 판단 기여 | 우선순위 |
|---|---|---|---|
| `distance_from_day_high_pct` | 감사용 로그에 이미 계산됨 | 고점 대비 현재 위치, 줄설거지 감지 | ★★★★★ |
| `intraday_range_pct` | 감사용 로그에 이미 계산됨 | 변동폭 대비 현재 위치 | ★★★★ |
| `buy_pressure_10t` | 감사용 로그에 이미 계산됨 | 프롬프트 3원칙 1번의 핵심 수치 | ★★★★★ |
| `tick_acceleration_ratio` | OpenAI 피처셋에 구현됨 | 프롬프트 3원칙 2번의 핵심 수치 | ★★★★★ |
| `net_bid_depth` / `bid_depth_ratio` | ws_data에 존재 | 매수 잔량 변화율 | ★★★★ |
| `net_ask_depth` / `ask_depth_ratio` | ws_data에 존재 | 매도벽 소화율 직접 지표 | ★★★★★ |
| `prog_net_qty` / `prog_delta_qty` | ws_data에 존재 | 프로그램 매매 방향성 | ★★★ |
| `large_sell_print_detected` | OpenAI 피처셋에 구현됨 | 고점 매도 틱 감지 (3원칙 2번) | ★★★★ |
| `same_price_buy_absorption` | OpenAI 피처셋에 구현됨 | 매도벽 소화 직접 신호 (3원칙 1번) | ★★★★★ |
| `gap_pct` / `target_buy_price` | handle_watching_state에 존재 | 추격 정도 맥락 | ★★★ |

#### HOLDING에서 즉시 추가 권고

| 데이터 | 위치 | 청산 판단 기여 | 우선순위 |
|---|---|---|---|
| `profit_rate` | handle_holding_state에 존재 | 현재 손익률, 청산 판단의 가장 기본값 | ★★★★★ |
| `peak_profit` | handle_holding_state에 존재 | 고점 대비 현재 drawdown 파악 | ★★★★★ |
| `held_sec` | handle_holding_state에 존재 | 보유 시간, 조기 손절 판단 기준 | ★★★★ |
| `position_tag` | handle_holding_state에 존재 | 포지션 성격 (OPEN_RECLAIM / SCANNER / fallback) | ★★★★ |
| `trailing_stop_price` | handle_holding_state에 존재 | 현재 보호선 위치 | ★★★ |
| `ai_low_score_hits` | handle_holding_state에 존재 | 연속 저점수 누적 상태 | ★★★★ |
| `exit_mode` | handle_holding_state에 존재 | 현재 청산 모드 맥락 | ★★★ |

---

### 4-2. 정량형 OpenAI 피처셋의 활용 가능성

`src/engine/ai_engine_openai_v2.py`에 이미 구현된 `SCALPING_SYSTEM_PROMPT_V3`와 정량형 피처 추출기는 현재 라이브 경로에 미연결 상태다. 이 피처셋이 제공하는 핵심 지표는 다음과 같다.

```
tick_acceleration_ratio  : 최근 5틱 vs 이전 5틱 속도비 (수치화된 3원칙 2번)
microprice_edge_bp       : 미시가격 우위 (bp 단위 정량값)
same_price_buy_absorption: 같은 가격대 매수 흡수 여부 (3원칙 1번 직접 지표)
large_sell_print_detected: 대량 매도 틱 감지 (3원칙 2번 직접 지표)
spread_bp                : 스프레드 (bp 단위, latency 판단 보조)
top1/top3_depth_ratio    : 최우선 호가 잔량 비율
net_aggressive_delta_10t : 최근 10틱 공격적 순매수
```

이 지표들은 현재 프롬프트의 3원칙이 자연어로 설명하는 내용을 수치로 정의한 것이다. **자연어 판단보다 이 정량값을 먼저 제공하면 AI의 판단 일관성이 크게 향상된다.**

---

## 5. 정확도 vs 판단속도 스윗스팟 분석

### 5-1. 현재 구조의 속도 vs 정확도 트레이드오프

| 요소 | 현재 상태 | 속도 영향 | 정확도 영향 |
|---|---|---|---|
| 프롬프트 길이 | 중간 (3원칙 + 스코어링 기준) | 무관 (입력 토큰) | 보통 |
| 입력 데이터량 | 적음 (핵심 정량값 대부분 미입력) | 빠름 | 낮음 |
| 원본 시퀀스 포함 | 분봉 시계열 + 호가창 + 10틱 상세 | 느림 (토큰 多) | 중간 (AI가 직접 해석) |
| AI 호출 주기 | WATCHING: 180초 cooldown | 적절 | — |
| HOLDING critical: 3~10초 | 매우 빠름 | 토큰 절약 필요 |

---

### 5-2. WATCHING 스윗스팟 설계안

**원칙:** 원본 시퀀스를 줄이고, 핵심 정량값을 구조화해서 전달한다.

현재 방식은 AI에게 원본 틱/분봉/호가창을 그대로 주고 AI가 직접 해석하게 한다. 이는 토큰을 많이 쓰면서도 AI의 해석 편차가 크다.

권고 방식은 핵심 수치를 전처리해서 전달하고, 원본은 보조 확인용으로만 유지한다.

```
[현재] 원본 10틱 상세 → AI가 buy_pressure 직접 계산
[권고] buy_pressure_10t: 82.3% / tick_acceleration_ratio: 1.47x 
       → AI는 수치를 해석만 함

[현재] 호가창 1~5호가 전체 원본 → AI가 잔량 비율 계산
[권고] ask_depth_ratio: -23.4% (매도잔량 감소 중)
       same_price_buy_absorption: True
       → AI는 의미를 해석만 함
```

**예상 효과:**
- 입력 토큰 30~40% 감소 → 응답 속도 개선
- AI 판단 일관성 향상 (수치 기반 판단 vs 원본 해석 편차)
- 정확도: 핵심 지표 직접 제공으로 오히려 향상 예상

---

### 5-3. HOLDING 스윗스팟 설계안

HOLDING critical zone(3~10초 주기)에서는 속도가 최우선이다.

**권고 구조 — HOLDING 전용 경량 프롬프트:**

```
[포지션 현황]
- 진입가: {buy_price}원 / 현재가: {curr_price}원
- 현재 손익: {profit_rate}% / 최고 수익: {peak_profit}%
- 보유 시간: {held_sec}초 / 연속 저점수: {ai_low_score_hits}회
- 포지션 태그: {position_tag}

[실시간 수급 — 핵심 수치만]
- tick_acceleration_ratio: {값} (1.0 미만 = 속도 둔화)
- buy_pressure_10t: {값}%
- large_sell_print_detected: {True/False}
- ask_depth_ratio: {값}% (음수 = 매도벽 소화 중)
- net_aggressive_delta_10t: {값}

[판단 기준]
- HOLD: 모멘텀 유지, 포지션 유리
- EXIT: 모멘텀 둔화 또는 손익 보호 필요
- FORCE_EXIT: 즉시 탈출 (대량 매도 틱, 급격한 속도 저하)
```

분봉 시계열과 전체 호가창 원본은 HOLDING critical 경로에서 제외한다. 이미 `SCALP_PRESET_TP`에서 `recent_candles=[]`로 호출하는 것이 이 방향의 부분 구현이다. 이를 일반 HOLDING critical 경로에도 적용하고, 대신 포지션 컨텍스트와 핵심 수치를 채워 넣는다.

---

### 5-4. 경로별 스윗스팟 정의

| 경로 | 목표 | 권고 프롬프트 크기 | 핵심 입력 | 원본 시퀀스 |
|---|---|---|---|---|
| WATCHING | 타점 정확도 | 중간 | 정량 피처 + 포지션 맥락 | 10틱 원본 유지 (보조) |
| HOLDING 일반 | 모멘텀 유지 판단 | 중간-소 | 포지션 컨텍스트 + 수급 핵심 수치 | 분봉만 (호가 원본 제거) |
| HOLDING critical | 즉각 청산 판단 | 최소 | 포지션 컨텍스트 + 3~5개 핵심 수치 | 전체 제거 |
| SCALP_PRESET_TP | 익절 연장/즉시 청산 | 최소 | 10틱 수급 + 포지션 현황 | 현재대로 (`candles=[]`) |

---

## 6. 추가 검토가 필요한 사항

### 6-1. AI 모델 특성 관련

**Gemini의 JSON 출력 안정성 검증이 필요하다.** 현재 프롬프트는 `단 1글자의 부연 설명도 추가하지 마`라고 강제하지만, Gemini 모델이 실제로 얼마나 자주 JSON 파싱 오류를 내는지 집계가 없다. 파싱 실패 시 `score=50` 폴백으로 처리되는 구조이므로, 파싱 실패율이 높다면 사실상 중요한 시점에 AI 판단이 무력화되고 있을 수 있다.

**확인이 필요한 질문:**
- Gemini 응답의 JSON 파싱 성공률은 얼마인가?
- 파싱 실패 발생 시점과 시장 상황(변동성 급등 구간)의 상관관계가 있는가?
- `score=50` 폴백 처리 건수가 전체 AI 호출 대비 몇 %인가?

---

### 6-2. AI 호출 타이밍 관련

**WATCHING의 `AI_WATCHING_COOLDOWN=180초`가 스캘핑 판단 주기와 맞는지 검토가 필요하다.** 스캘핑에서 180초는 매우 긴 주기다. 강한 모멘텀이 발생해도 마지막 AI 호출 이후 180초가 지나지 않으면 재호출이 안 된다. 반면 기계 게이트는 계속 돌고 있다.

**확인이 필요한 질문:**
- `AI_WATCHING_COOLDOWN` 경과 전에 기계 게이트를 통과한 뒤 waiting한 건수는 얼마인가?
- `entry_armed`가 AI 쿨다운으로 인해 만료된 케이스가 있는가?

---

### 6-3. Big-Bite 보정 점수의 타당성

현재 Big-Bite confirmed 시 `+5점`, armed 시 `+2점`을 AI score에 더한다. 이 수치의 근거가 무엇인지 확인이 필요하다. 특히 AI score가 70점일 때 Big-Bite confirmed가 붙으면 75점이 되어 진입 임계값을 통과한다. Big-Bite 보정이 `AI 판단 우회 경로`로 기능하고 있는지 점검이 필요하다.

---

### 6-4. HOLDING 평활화 계수의 근거

현재 `smoothed_score = 기존 * 0.6 + 신규 * 0.4`. 이 계수가 실제 시장 데이터에서 검증된 값인지, 또는 초기 임의 설정값인지 확인이 필요하다. 스캘핑처럼 빠른 시장에서 `0.6` 가중치는 과거 점수에 너무 높은 비중을 줄 수 있다.

---

## 7. 제안사항 및 우선순위

### 7-1. 즉시 착수 (이번 주)

**제안 1 — SCALP_PRESET_TP action 불일치 수정 (버그 수준)**

```python
# 현재 (버그)
if action in ['SELL', 'DROP']:

# 수정안 A — SELL 제거 (현재 프롬프트 유지)
if action in ['DROP']:

# 수정안 B — 프롬프트에 SELL 추가 (더 공격적 청산)
"action": "BUY" | "WAIT" | "DROP" | "SELL"
```

설계 의도에 따라 A 또는 B를 선택. 현재 상태는 버그다.

**제안 2 — WATCHING 프롬프트 스코어 구간 재정렬**

진입 임계값 75와 프롬프트 BUY 기준 80의 불일치를 해소한다.

**제안 3 — 감사용 값 3개를 즉시 프롬프트에 추가**

이미 계산되어 있는 `distance_from_day_high_pct`, `buy_pressure_10t`, `intraday_range_pct`를 `_format_market_data()`에 추가한다. 코드 변경 최소, 효과 즉시 발생.

---

### 7-2. 단기 착수 (2주 이내)

**제안 4 — WATCHING 핵심 정량 피처 입력 보강**

OpenAI 피처셋에 이미 구현된 `tick_acceleration_ratio`, `same_price_buy_absorption`, `large_sell_print_detected`, `net_ask_depth`, `ask_depth_ratio`를 Gemini 경로 `_format_market_data()`에 추가한다.

**제안 5 — HOLDING 전용 프롬프트 신설**

포지션 컨텍스트(진입가, 현재 손익률, 최고 수익률, 보유 시간, position_tag)를 포함하는 `SCALPING_HOLDING_SYSTEM_PROMPT`를 별도로 작성한다. `cache_profile="holding"` 경로에서 이 프롬프트를 사용하도록 분기를 추가한다.

**제안 6 — 사전 통과 조건 프롬프트 명시**

AI 호출 시점에 이미 통과한 기계 게이트 조건을 프롬프트 도입부에 구조화해서 전달한다.

---

### 7-3. 중기 착수 (4주 이내)

**제안 7 — HOLDING critical 경량 프롬프트 분리**

critical zone(손익률 >= 0.5% 또는 < 0%)에서 호출되는 3~10초 주기 AI 리뷰는 별도 경량 프롬프트로 분리한다. 분봉 원본 제거, 포지션 컨텍스트 + 수급 핵심 수치 5개로만 구성한다.

**제안 8 — Gemini JSON 파싱 실패율 집계 및 모니터링**

`ai_parse_fail` 이벤트를 `ENTRY_PIPELINE` 로그에 추가하고, 파싱 실패율을 일별 집계한다. 실패율이 5% 초과 시 프롬프트 JSON 강제 구조를 재검토한다.

**제안 9 — AI score vs 실현손익 상관관계 주기 집계**

`ai_confirmed score`와 해당 거래의 `realized_pnl`을 매칭해 AI 판단의 실제 예측력을 수치화한다. 이 데이터가 쌓이면 스코어 임계값, 평활화 계수, Big-Bite 보정 점수의 재보정 근거가 된다.

---

### 우선순위 종합표

| 순위 | 제안 | 예상 효과 | 공수 | 착수 시점 |
|---|---|---|---|---|
| 1 | SCALP_PRESET_TP action 불일치 수정 | 버그 제거 | 소 | 즉시 |
| 2 | WATCHING 스코어 구간 재정렬 | 판단 일관성 | 소 | 즉시 |
| 3 | `distance_from_day_high_pct` 등 3개 즉시 추가 | 정확도 ↑ | 소 | 즉시 |
| 4 | WATCHING 정량 피처 보강 | 정확도 ↑, 토큰 ↓ | 중 | 2주 이내 |
| 5 | HOLDING 전용 프롬프트 신설 | 청산 판단 근본 개선 | 중 | 2주 이내 |
| 6 | 사전 통과 조건 프롬프트 명시 | 오판 감소 | 소 | 2주 이내 |
| 7 | HOLDING critical 경량 프롬프트 분리 | 속도 ↑, 정확도 ↑ | 중 | 4주 이내 |
| 8 | Gemini 파싱 실패율 집계 | 리스크 모니터링 | 소 | 4주 이내 |
| 9 | AI score vs 실현손익 상관관계 집계 | 장기 튜닝 근거 | 중 | 4주 이내 |

---

## 최종 의견

현재 프롬프트 설계의 가장 큰 문제는 **파라미터 튜닝 이전에 존재하는 구조적 결함** 두 가지다.

> **① HOLDING 청산 판단에 진입 탑승용 프롬프트를 재사용하고 있다.** AI는 자신이 포지션을 보유 중이라는 사실도, 현재 손익률도, 보유 시간도 모른 채 청산 판단을 내리고 있다. 이 상태에서 HOLDING 프롬프트를 튜닝하는 것은 기초가 잘못된 상태에서 마감재를 고치는 것이다.
>
> **② SCALP_PRESET_TP의 `SELL` vs `DROP` 불일치는 버그다.** 이것이 먼저 수정되어야 이후 청산 로직 튜닝 결과를 신뢰할 수 있다.

이 두 가지가 해소된 이후에, 정량 피처 보강과 속도-정확도 최적화 작업이 의미 있는 결과를 낼 수 있다.

---

*작성 기준: 2026-04-11 | 외부 시스템 트레이딩 전문가 점검 의견*
