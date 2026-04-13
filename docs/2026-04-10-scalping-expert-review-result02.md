# 스캘핑 자동매매 시스템 전문가 종합 점검 리포트

> **점검 기준일:** 2026-04-10  
> **점검 범위:** 진입 퍼널 → 체결 품질 → 보유/청산 → 사후평가 → 매매 로직 설계  
> **점검 관점:** 손실 억제보다 기대값/순이익 극대화  
> **기준 데이터:** 실매매 스냅샷, pipeline_events, trade_review, missed_entry_counterfactual, post_sell_feedback, Stage 2 체크리스트

---

## 목차

1. [퍼널 구조 요약](#1-퍼널-구조-요약)
2. [단계별 튜닝 포인트 점검](#2-단계별-튜닝-포인트-점검)
3. [실제 매매 성과 분석](#3-실제-매매-성과-분석)
4. [매매 로직 설계 구조 진단](#4-매매-로직-설계-구조-진단)
5. [종합 튜닝 우선순위](#5-종합-튜닝-우선순위)
6. [딥리서치 필요성 판단](#6-딥리서치-필요성-판단)
7. [최종 결론 및 액션 아이템](#7-최종-결론-및-액션-아이템)

---

## 1. 퍼널 구조 요약

### 2026-04-10 장후 유니크 퍼널

```
ai_confirmed 75
    │  ▼ -41% (strength/momentum/ai_score/overbought 필터)
entry_armed 44
    │  ▼ -9%
budget_pass 40
    │  ▼ -85% ← 현재 최우선 병목
submitted 6
```

### 병목 원인 분해

| 차단 구간 | 건수 | 주요 원인 |
|---|---|---|
| ai_confirmed → entry_armed | -31건 | blocked_strength_momentum 40, blocked_ai_score 23, blocked_overbought 5 |
| budget_pass → submitted (장후) | -34건 | latency_block 34/34 (100%) |
| budget_pass → submitted (장중 누적) | -31건 | latency_block (quote_stale=False/True = 14/17) |

**핵심 판정:** 현재 주병목은 청산 규칙이 아닌 `budget_pass 이후 latency_block`이다. 단, latency 완화 전 상류 필터(strength/momentum)의 구조적 문제도 병행 점검이 필요하다.

---

## 2. 단계별 튜닝 포인트 점검

### 2-1. AI BUY 확정 → entry_armed 구간 (41% 탈락)

**진단:**

`blocked_strength_momentum 40건`이 가장 큰 상류 탈락 원인이다. 전역 완화는 EV 훼손 위험이 있으며, `momentum_tag × threshold_profile` 교차 분석을 통한 국소 재설계가 적합하다.

`blocked_ai_score 23건`은 AI 스코어 임계값이 시장 변동성 구간에 무관하게 고정값으로 운영되고 있을 가능성이 있다. 변동성 레짐별 동적 임계값(adaptive threshold) 적용 여지를 검토해야 한다.

`blocked_overbought 5건`은 표본 부족으로 현재는 유지가 맞다.

**권고 액션:**
- `momentum_tag별 missed_winner_rate` 교차표 산출 → `missed_winner_rate > 70%` 조합만 선별 canary 설계
- AI 스코어 임계값의 변동성 레짐 연동 여부 검토

---

### 2-2. budget_pass → submitted 구간 (85% 탈락) — 최우선 과제

**진단:**

`quote_stale=False` 케이스 14건은 데이터 신선도와 무관하게 `ws_age_ms`, `ws_jitter_ms`, `spread_ratio` 중 하나 이상이 DANGER로 판정한 것이다. 현재 DANGER 판정이 `이론적 최대 slippage` 기준인지, `보수적 마진` 기준인지 명확히 해야 한다.

스캘핑에서 **예상 기대값 > 예상 slippage**이면 진입해야 하는 것이 EV 극대화 원칙이다. 현재 로직은 이 비교 없이 이진(binary) 차단을 적용하고 있다.

**권고 액션:**
1. `quote_stale=False` 코호트 14건의 각 gate 지표 실측값 분포 추출 → DANGER 판정 threshold의 실효성 검증
2. DANGER 판정 케이스에 대한 `예상 slippage vs 예상 기대값` 반사실 시뮬레이션 실시
3. latency gate를 `진입 차단` 로직에서 `수량/슬리피지 조정` 로직으로 재설계 검토:

```
SAFE    → 정상 수량, 정상 주문가
CAUTION → 수량 축소 or 지정가 마진 확대
DANGER  → 수량 최소화 or 기대값 임계 이상일 때만 진입
```

---

### 2-3. 체결 품질 — full fill vs partial fill

**진단:**

`fallback partial` 코호트가 손익 기여 음수라는 것은 단순 수량 감소 문제가 아닐 수 있다. partial fill 이후에도 full fill 기준으로 설계된 `preset_exit`이 그대로 적용되면, 포지션 사이즈와 청산 기준의 불일치가 발생한다.

**권고 액션:**
- fallback partial 코호트의 평균 fill rate와 `avg_profit_rate` 분리 집계
- partial fill 시 `preset_exit` 자동 재계산 로직 존재 여부 확인
- partial fill 임계치 이하 시 즉시 취소 옵션 검토

---

### 2-4. 보유 → 청산 구간

**현재 수치 (2026-04-10, 완료 6건):**

| 지표 | 수치 | 비고 |
|---|---|---|
| missed_upside_rate | 16.7% | 표본 부족 단계 |
| good_exit_rate | 16.7% | 표본 부족 단계 |
| capture efficiency | 22.65% | 개선 여지 있음 |
| estimated_extra_upside_10m_krw_sum | +24,730원 | |

**진단:**

capture efficiency 22.65%는 낮지만, 완료 거래 6건은 통계적 신뢰도가 낮다. 청산 튜닝은 완료 거래 30건 이상 축적 후 본격 착수가 맞다. 현재는 `ai_holding_review` 판단 근거를 로깅으로 축적하는 것이 우선이다.

`hard_time_stop`이 `ai_holding_review` 이후에 위치하는 구조는 AI의 hold 권고를 무력화할 수 있으며, 이 경우 ai_holding_review의 존재 의미가 약해진다. time_stop의 조기 발동이 missed_upside의 구조적 원인일 가능성을 검증해야 한다.

---

### 2-5. 반사실 분석 (missed_entry_counterfactual)

**2026-04-10 기준:**

| 구분 | 건수 | missed_winner_rate | estimated_pnl_10m |
|---|---|---|---|
| 전체 evaluated | 21건 | 81.0% | +24,960원 |
| latency_block 표본 | 20건 | 80.0% | — |

**진단:**

반사실 추정의 `10분 후 가격` 기준에는 구조적 낙관 편향이 있다. AI BUY 신호 발생 시점은 이미 모멘텀이 붙기 시작한 시점이므로, 실제 진입가는 신호 시점보다 높았을 것이다. `missed_winner_rate 80~81%`는 인상적이지만 실제 달성 가능한 기대값은 이보다 낮을 수 있다.

**권고 액션:**
- 반사실 추정에 `예상 진입가 = 신호 시점 가격 + 평균 체결 슬리피지` 보정 수익률 병행 산출
- latency gate 완화 효과의 과대 추정 방지

---

## 3. 실제 매매 성과 분석

### 일별 성과 추이

| 날짜 | 완료 거래 | 승/패 | avg_profit_rate | realized_pnl |
|---|---|---|---|---|
| 2026-04-09 | 4건 | — | -0.90% | -18,590원 |
| 2026-04-10 | 6건 | 2/4 | -0.41% | -10,885원 |

**트렌드 판단:** 완료 거래 수 증가, 손실폭 감소로 방향성은 개선 중이다.

### 실질 EV 훼손 규모

```
실현손익          -10,885원
미진입 기회비용   -24,960원 (counterfactual 보정 전)
──────────────────────────
실질 EV 훼손    ≈ -35,845원
```

**핵심 판단:** 실현손익 개선보다 미진입 기회비용 회수가 현재 가장 큰 EV 레버리지다.

---

## 4. 매매 로직 설계 구조 진단

### 4-1. AI 확정 → strength 필터 이중 검열 문제 ★★★★

**문제:**

AI가 BUY를 확정한 뒤 strength/momentum을 다시 차단하는 구조는 다음 두 경우 중 하나다:

- AI 스코어가 모멘텀/강도를 이미 반영한다 → 필터가 AI 판단을 사후에 덮어쓰는 이중 검열
- AI 스코어가 모멘텀을 반영하지 않는다 → AI 모델 자체의 피처 설계 결함

**핵심 확인 질문:**
> AI 모델의 입력 피처에 `strength`, `momentum_tag`, `overbought` 지표가 포함되어 있는가?

- 포함되어 있다면 → 이중 필터 제거 검토
- 포함되어 있지 않다면 → 필터가 아닌 모델 피처 보강이 맞다

---

### 4-2. Latency Gate 이진 차단 — EV 비기반 설계 문제 ★★★★

**문제:**

현재 DANGER 판정 시 진입을 전면 차단하는 로직은 다음 두 케이스를 구분하지 않는다:

```
Case A: latency 나쁨 + 예상 slippage > 기대값  → 차단 합리적
Case B: latency 나쁨 + 기대값 >> 예상 slippage → 차단 비합리적 (EV 훼손)
```

스캘핑에서 latency는 `진입할지 말지`의 기준이 아니라 `얼마나 공격적으로 진입할지`의 기준이어야 한다.

**권고:** latency gate를 EV 조건부 수량 조정 로직으로 재설계

---

### 4-3. entry_armed 만료 미추적 문제 ★★★

**문제:**

유효시간 만료 케이스가 이후 상승했다면, 이는 `latency_block`과 별개의 기회비용이다. 현재 `missed_entry_counterfactual`이 두 케이스를 합산하고 있다면 병목 원인 진단이 희석된다.

**권고:** `expired_armed`를 별도 이벤트로 분리 집계하여 유효시간 설정의 적정성을 독립 검증

---

### 4-4. 청산 로직의 구조적 비대칭 문제 ★★★★

**문제 1 — preset vs AI 청산 우선순위 충돌:**

`preset_exit_setup`과 `ai_holding_review`가 충돌할 때 명시적 우선순위 로직이 없다면, 마지막으로 실행된 쪽이 이기는 **레이스 컨디션**이 발생할 수 있다.

**문제 2 — hard_time_stop의 AI 무력화:**

`hard_time_stop`이 `ai_holding_review` 이후에 위치하면, AI가 hold를 권고해도 시간이 되면 강제 청산된다. time_stop이 AI 판단을 구조적으로 무력화한다면 ai_holding_review의 존재 의미가 약해진다.

**문제 3 — partial fill 후 청산 기준 불일치:**

partial fill 발생 시 full fill 기준으로 설계된 preset_exit이 그대로 적용되면, 수량-preset 비동기화로 음수 손익이 발생한다.

---

### 4-5. AI 피드백 루프 부재 가능성 ★★★

**문제:**

`post_sell_feedback` 결과(GOOD_EXIT / MISSED_UPSIDE / NEUTRAL)가 AI 모델 재학습이나 스코어 보정에 연결되지 않는다면, 시스템은 고정된 모델로 계속 운영된다. 스캘핑처럼 시장 미시구조가 빠르게 변하는 전략에서 이는 **모델 열화(drift)를 감지하지 못하는 리스크**다.

**권고:**
- `ai_confirmed 스코어 vs 실제 수익률` 상관관계를 주기적으로 모니터링
- AI 스코어의 예측력 유지 여부를 검증하는 로직 추가

---

### 로직 결함 종합

| # | 결함 위치 | 문제 유형 | 심각도 |
|---|---|---|---|
| 1 | AI확정 → strength 필터 | 이중 검열 / 설계 일관성 부재 | ★★★★ |
| 2 | Latency gate 이진 차단 | EV 비기반 진입 결정 | ★★★★ |
| 3 | preset vs AI 청산 우선순위 | 레이스 컨디션 / 로직 충돌 | ★★★★ |
| 4 | partial fill 후 청산 기준 불일치 | 수량-preset 비동기화 | ★★★★ |
| 5 | entry_armed 만료 미추적 | 병목 원인 오진 가능성 | ★★★ |
| 6 | 반사실 분석 낙관 편향 | 의사결정 근거 왜곡 | ★★★ |
| 7 | AI 피드백 루프 부재 | 모델 열화 무감지 리스크 | ★★★ |

---

## 5. 종합 튜닝 우선순위

| 순위 | 항목 | 기대 효과 | 위험도 | 권고 액션 |
|---|---|---|---|---|
| **1** | Latency gate 완화 (`quote_stale=False` 축) | 제출 전환율 ↑↑ | 중 | ws_jitter threshold canary 선행 적용 |
| **2** | AI 이중 필터 구조 점검 | 진입 효율 ↑ + 설계 일관성 확보 | 낮 | AI 피처 vs 필터 교차 분포 분석 |
| **3** | Latency gate → EV 조건부 수량 조정 재설계 | DANGER 구간 EV 회수 | 중 | slippage 반사실 시뮬레이션 선행 |
| **4** | Partial fill 청산 기준 자동 재계산 | fallback partial 음수 기여 제거 | 낮 | fill rate 임계치 기반 preset 재계산 로직 |
| **5** | Strength/Momentum 국소 재설계 | entry_armed 전환율 ↑ | 중상 | tag별 missed_winner율 교차분석 후 착수 |
| **6** | expired_armed 분리 집계 | 병목 원인 진단 정확도 ↑ | 낮 | pipeline_events 이벤트 타입 추가 |
| **7** | AI 스코어 예측력 모니터링 | 모델 열화 조기 감지 | 낮 | 주기적 상관관계 집계 추가 |
| **8** | 청산 capture efficiency 개선 | GOOD_EXIT 비율 ↑ | 낮 | 완료 거래 30건+ 축적 후 착수 |

---

## 6. 딥리서치 필요성 판단

**현 시점 딥리서치: 불필요**

현재 병목은 파라미터 튜닝 및 로직 설계 문제이며, 알고리즘 방향성 자체를 외부 문헌에서 검토해야 하는 단계가 아니다. 필요한 데이터는 이미 내부(`pipeline_events JSONL`, `missed_entry_counterfactual`, `post_sell_feedback`)에 존재한다.

**딥리서치가 유효한 시점:**
- latency gate 재설계 시 HFT/스캘핑 slippage 모델링 이론 참조가 필요할 때
- momentum filter의 구조적 재설계 방향을 외부 연구(예: market microstructure, order flow imbalance)에서 검토할 때
- AI 모델 열화(drift) 감지 방법론이 필요할 때

**지금 당장 필요한 것은 딥리서치가 아니라 내부 데이터 드릴다운이다.**

---

## 7. 최종 결론 및 액션 아이템

### 핵심 판단

현재 스캘핑 튜닝의 핵심 질문은 **"손절을 완화할지"가 아니라**, 두 가지다:

> **① `budget_pass 이후 latency 차단으로 놓치는 고기대값 진입을 어떻게 회수할지`**
>
> **② `AI 확정 이후 이중 필터 구조가 설계 의도에 부합하는지`**

### 즉시 착수 액션 (이번 주)

1. `quote_stale=False` latency_block 14건의 gate 지표 실측값 분포 추출 및 DANGER threshold 검증
2. AI 모델 입력 피처에 strength/momentum 포함 여부 확인 → 이중 필터 제거 또는 모델 피처 보강 방향 결정
3. fallback partial fill 코호트의 fill rate × profit_rate 분리 집계

### 다음 단계 착수 액션 (2~4주)

4. latency gate를 EV 조건부 수량 조정 로직으로 재설계 (slippage 반사실 시뮬레이션 선행)
5. `expired_armed` 이벤트 분리 집계 추가
6. momentum_tag별 missed_winner_rate 교차표 산출 → 국소 canary 설계

### 보류 액션 (표본 축적 후)

7. 청산 capture efficiency 개선 (완료 거래 30건+ 후 착수)
8. overbought 완화 검토

---

### 전문가 추가 점검 시 제공이 필요한 자료

- `latency missed winner` 대표 3건 (quote_stale=False 2건, True 1건)
- `체결 품질` 대표 3건 (normal full fill 1건, fallback full fill 1건, fallback partial fill 1건)
- `청산 복기` 대표 2건 (GOOD_EXIT 1건, MISSED_UPSIDE 1건)
- 현재 canary 파라미터 및 롤백 조건 (latency, dynamic strength, fallback qty multiplier)
- 로컬 vs `songstockscan` 퍼널/체결 품질/리포트 차이 비교

---

*작성 기준: 2026-04-10 | 외부 시스템 트레이딩 전문가 점검 의견*
