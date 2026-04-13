# WAIT 65 세부 원인 분석 vs 즉시 개선 검토 의견

> 작성 기준일: 2026-04-13
> 검토 질문: 세부 원인 분석을 더 깊이 진행할 것인가, 아니면 바로 개선을 진행하고 이후에 들여다볼 것인가

---

## 결론

**바로 개선을 진행하는 것이 맞다.** 세부 원인 분해는 개선 이후 검증 단계에서 해도 늦지 않다.

---

## 근거

### 판단 근거가 이미 충분히 확보되어 있다

WAIT 65 + latency_block이 missed_winner 50건으로 압도적 1위다. latency_block의 세부 원인(quote_stale / ws_jitter / armed_expired)을 분해해도 결론은 "latency gate를 완화해야 한다"는 방향에서 벗어나지 않는다. 세부 분해는 완화 방식을 정교화하는 데 쓰이는데, 현재 이미 `quote_stale=False` 축 중심 완화라는 방향이 이전 점검에서 고정되어 있다.

blocked_strength_momentum도 마찬가지다. 하위 분해(below_window_buy_value / below_buy_ratio 등)를 해도 결론은 "momentum_tag별 국소 재설계"이며, 이것도 이전 점검에서 이미 방향이 잡혀 있다.

---

### 세부 분해를 지금 계속하면 생기는 두 가지 문제

**첫째, 분석-개선 사이클이 늘어진다.** 현재 실매매 손익은 여전히 음수이고 EV 누수가 발생 중이다. 분석을 한 단계 더 내려가는 동안에도 latency_block은 계속 작동하고 있다.

**둘째, 개선 후 데이터가 더 깨끗한 분석 재료가 된다.** latency gate를 완화한 이후에 남은 missed_winner 분포를 보면 지금보다 훨씬 명확하게 strength/momentum 축의 세부 원인을 분리할 수 있다. 지금 세부 분해를 해도 latency 개선 후 분포가 바뀌면 다시 해야 한다.

---

## 권고 순서

| 단계 | 내용 |
|---|---|
| 지금 즉시 | latency gate 완화 canary 착수 (quote_stale=False 축 중심) |
| 병행 | blocked_strength_momentum 국소 재설계 착수 (momentum_tag 교차표 기반) |
| 개선 후 | latency 완화 이후 남은 WAIT 65 분포 재집계 → 세부 원인 분해 |

---

## 한줄 요약

원인은 충분히 특정됐다. 지금 필요한 것은 더 깊은 분석이 아니라 이미 아는 원인에 대한 조치다.

---

*작성 기준: 2026-04-13 | 외부 시스템 트레이딩 전문가 점검 의견*
