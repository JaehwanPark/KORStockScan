# WAIT 65 관련 통합 검토의견

## 문서 목적

본 문서는 기존 검토의견과 새로 첨부된 외부 전문가 의견을 함께 반영하여,  
`WAIT 65` 교차집계 이후 다음 액션을 어떻게 가져가는 것이 가장 적절한지에 대한 통합 의견을 정리한 문서다.

핵심 질문은 아래 두 가지다.

1. 지금 더 깊은 세부 원인분석을 먼저 해야 하는가
2. 아니면 바로 개선을 시작하고 이후 검증하는 것이 맞는가

---

## 1. 입력된 두 관점의 요약

## 관점 A — 제한적 추가 분석 후 수정
이 관점은 다음을 핵심으로 본다.

- `WAIT 65` missed-winner의 상위 원인은 이미 `latency_block`, 그다음 `blocked_strength_momentum`으로 충분히 특정되었다
- 다만 실제 수정 포인트는 하위 원인에 따라 달라지므로, 최소 1회 하위 분해는 필요하다
- 잘못된 전면 완화를 막기 위해 `quote_stale / ws_jitter / armed_expired_after_wait`, `below_window_buy_value / below_buy_ratio / below_strength_base` 정도는 먼저 봐야 한다

---

## 관점 B — 바로 개선 착수
첨부된 외부 전문가 의견은 다음을 핵심으로 본다.

- `WAIT 65 + latency_block`이 missed-winner 50건으로 압도적 1위이므로 원인 특정은 이미 충분하다
- 지금 더 세부 분해를 계속하면 분석-개선 사이클만 늘어진다
- latency 완화 이후 남는 분포를 보는 쪽이 오히려 더 깨끗한 재분석 재료가 된다
- 따라서 지금 즉시 `quote_stale=False` 축 중심 latency 완화 canary와 `blocked_strength_momentum` 국소 재설계를 착수하는 것이 맞다

---

## 2. 공통으로 일치하는 부분

두 관점은 표현은 다르지만, 아래 4가지에서는 사실상 일치한다.

### 1) 핵심 병목은 `latency_block`
기존 전문가 리포트와 onepager 모두 현재 주병목이 `budget_pass 이후 latency_block`이라고 판단했고, 장중/장후 표본에서도 `quote_stale=False/True = 14/17`로 stale quote만의 문제가 아니라고 정리했다. fileciteturn13file4 fileciteturn13file9turn13file18

### 2) 두 번째 축은 `blocked_strength_momentum`
상류 필터에서는 `blocked_strength_momentum`이 가장 큰 탈락 원인이며, 전역 완화가 아니라 `momentum_tag × threshold_profile` 기반의 국소 재설계가 적합하다는 데 기존 점검들도 일관성이 있다. fileciteturn13file4turn13file13

### 3) `overbought`는 현재 우선순위가 낮다
기존 전문가 점검에서도 `blocked_overbought`는 표본 부족으로 유지가 맞다고 봤고, 이번 추가 의견도 핵심 원인을 latency와 strength 쪽으로 본다. fileciteturn13file4turn13file9 fileciteturn13file1

### 4) 전면 완화는 위험하다
기존 점검은 `quote_stale=False` 축 중심 접근과 `momentum_tag`별 국소 canary를 권고했고, 이는 전역 threshold 완화보다 좁은 축 조정이 맞다는 뜻이다. fileciteturn13file3turn13file4

---

## 3. 실제로 충돌하는 부분

실제 차이는 “무엇이 문제인가”가 아니라 “언제 손댈 것인가”에 있다.

### 관점 A의 장점
- 잘못된 완화 방향을 막는다
- 원인별 처방을 더 정확히 고를 수 있다
- canary 실패 시 원인 해석이 쉽다

### 관점 A의 한계
- EV 누수가 계속되는 동안 개선 착수가 늦어진다
- 하위 분해를 해도 latency 완화 후 분포가 다시 바뀌면 재분석이 필요할 수 있다

### 관점 B의 장점
- 현재 가장 큰 EV 누수 축을 바로 줄일 수 있다
- latency 완화 이후 남는 분포로 더 깨끗한 2차 분석이 가능하다
- 실매매 음수 상태에서 분석-개선 사이클 지연을 줄인다. fileciteturn13file1

### 관점 B의 한계
- 하위 원인 확인 없이 넓게 완화하면 loser 유입이 늘 수 있다
- “바로 개선”이 “전면 완화”로 확대되면 운영 원칙을 벗어날 위험이 있다

---

## 4. 통합 판단

## 최종 결론
가장 적절한 방향은 아래다.

> **전면적인 추가 분석을 먼저 하는 것도 아니고, 전면적인 즉시 완화를 하는 것도 아니다.**  
> **저위험 즉시 canary는 지금 시작하고, 실제 임계값/룰 변경 폭은 좁은 하위 분해 1회로 제한해 함께 제어하는 것이 맞다.**

즉, 이번 통합 의견은 두 관점 중 하나를 버리는 방식이 아니라 아래처럼 합치는 것이 맞다.

### 핵심 원칙
1. 우선순위 재설정은 즉시 반영한다
2. `latency_block` 저위험 축은 지금 즉시 canary 착수 가능하다
3. `blocked_strength_momentum`은 전역 완화가 아니라 국소 재설계로 간다
4. 세부 원인분해는 하위 1단계까지만 하고, 전면 분석으로 확대하지 않는다

---

## 5. 통합 권고안

## 권고 1. 지금 즉시 반영할 운영 해석 기준
아래 해석은 즉시 고정하는 것이 맞다.

- `WAIT 65`는 AI threshold miss 단독 문제로 보지 말 것
- 1순위는 `latency_block`
- 2순위는 `blocked_strength_momentum`
- `overbought`는 이번 묶음에서는 비우선

이 판단은 현재 교차집계와 기존 전문가 리포트 흐름 모두와 부합한다. fileciteturn13file1turn13file9

---

## 권고 2. 지금 즉시 착수 가능한 개선
아래는 바로 시작해도 된다.

### A. `quote_stale=False` 축 중심 latency canary
기존 전문가 점검에서도 장후 기준 `budget_pass 후 미제출 34/34`가 latency였고, 장중 누적에서도 `quote_stale=False/True = 14/17`이라 stale quote만의 문제는 아니라고 봤다. 따라서 `quote_stale=False` 축 중심 canary 착수는 정당하다. fileciteturn13file4turn13file9

### B. `blocked_strength_momentum` 국소 재설계 준비
기존 점검은 이 축에서 전역 완화가 아니라 `momentum_tag × threshold_profile` 교차 기반 국소 canary가 맞다고 정리했다. 따라서 즉시 할 일은 “전역 threshold 완화”가 아니라 “국소 재설계 착수”다. fileciteturn13file4turn13file13

---

## 권고 3. 병행할 최소 분석 범위
즉시 개선과 병행하되, 분석 범위는 아래까지만 제한하는 것이 맞다.

### A. `WAIT 65 + latency_block`
- `quote_stale`
- `ws_jitter`
- `armed_expired_after_wait`

### B. `WAIT 65 + blocked_strength_momentum`
- `below_window_buy_value`
- `below_buy_ratio`
- `below_strength_base`

이 하위 분해는 “개선을 미루기 위한 분석”이 아니라, **즉시 착수하는 canary의 폭을 과도하게 넓히지 않기 위한 안전장치**로 쓰는 것이 맞다.

---

## 권고 4. 하지 말아야 할 것
지금 단계에서 아래는 하지 않는 것이 맞다.

- WAIT 65 threshold 전면 완화
- latency gate 전반 상향
- strength momentum gate 전반 완화
- `overbought` 우선 착수
- shadow 하한 조정 선행
- 원인 단정 전 대규모 인프라/아키텍처 리팩터링

기존 부적합 메모도 원인 확정 전 다축 변경과 대규모 인프라 대응은 운영 원칙에 맞지 않는다고 정리했다. fileciteturn13file12turn13file14

---

## 6. 실행 순서 제안

### Step 1
운영 해석 기준 즉시 고정

- `WAIT 65 = threshold miss 단독 문제 아님`
- `latency_block` 1순위
- `blocked_strength_momentum` 2순위
- `overbought` 후순위

### Step 2
즉시 canary 착수

- `quote_stale=False` 축 중심 latency 완화 canary
- `blocked_strength_momentum` 국소 재설계 준비

### Step 3
동시에 하위 원인 1단계 분해

- `latency_block` 하위 3축
- `blocked_strength_momentum` 하위 3축

### Step 4
가장 비중 큰 하위 원인 1개만 추가 조정

### Step 5
장후 재집계 후 2차 판단

---

## 7. 최종 통합의견

첨부된 외부 전문가 의견의 장점은 “지금 충분히 원인이 특정됐으니 EV 누수를 멈추기 위해 개선을 늦추지 말자”는 점에 있다. fileciteturn13file1  
기존 검토의 장점은 “하지만 잘못된 전면 완화를 막기 위해 하위 원인 1단계 확인은 필요하다”는 점에 있다.

두 의견을 합치면 최종적으로 아래가 가장 적절하다.

> **지금은 더 깊은 분석만 계속할 단계가 아니라, 저위험 즉시 canary를 시작할 단계다.**  
> **다만 전면 완화는 금지하고, `latency_block`과 `blocked_strength_momentum`의 하위 1단계 분해를 병행해 canary 폭을 좁게 통제하는 것이 맞다.**

한 줄로 정리하면 아래와 같다.

**지금 필요한 것은 “분석 후 개선”도 아니고 “개선 후 분석”도 아니라, 저위험 축은 즉시 개선하고 하위 원인 분해는 그 개선 폭을 제어하는 범위에서 병행하는 것이다.**
