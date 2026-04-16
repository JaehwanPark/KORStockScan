# `budget_pass -> submitted` 병목 재판정

작성일: 2026-04-16  
검토 기준: `entry_pipeline_flow_2026-04-16`, `performance_tuning_2026-04-16`, `pipeline_events_2026-04-16.jsonl`  
검토 코드: `src/engine/sniper_entry_pipeline_report.py`, `src/engine/sniper_entry_latency.py`, `src/engine/sniper_state_handlers.py`

---

## 1. 판정

1. 판정: `budget_pass -> submitted`는 **실병목이 맞다**.
   - 근거: 이벤트 기준 `budget_pass_events=3923`, `order_bundle_submitted_events=24`, `budget_pass_event_to_submitted_rate=0.6%`다. 단순 최신 상태 착시가 아니라 주문 제출 직전 전환이 실제로 거의 일어나지 않았다.
   - 다음 액션: 내일 장전 전까지는 다른 5개 관찰축보다 이 구간 복구를 우선한다.

2. 판정: 동시에 현재 보고서의 `budget_pass_stocks=2`, `budget_pass_to_submitted_rate=0.0%`는 **모니터링 정의상 착시를 만든다**.
   - 근거: `entry_pipeline_flow`의 기존 지표는 "종목별 최신 시도(latest attempt)" 기준이고, `latency_block_events=3899`는 "당일 누적 이벤트" 기준이다. 서로 다른 분모를 같은 퍼널처럼 읽으면 병목 위치가 틀어질 수 있다.
   - 다음 액션: `entry_pipeline_flow`에서 최신 시도 기준과 이벤트 기준을 분리 표기한다.

3. 판정: `SCALP_LATENCY_GUARD_CANARY`는 "비활성"이 아니라 **실운영에서 사실상 무력화**돼 있었다.
   - 근거: 로컬 런타임 기본값은 `SCALP_LATENCY_GUARD_CANARY_ENABLED=True`인데, `2026-04-16` 실데이터에서 `latency_canary_applied=True`는 0건이다. 원인은 canary 비교 시 `signal_strength=0.86` 같은 확률값을 `85.0` 점수 기준과 직접 비교하는 스케일 버그다.
   - 다음 액션: 점수 정규화 버그만 우선 수정하고, 태그/임계값 추가 완화는 장전 관찰 후 1축씩 판단한다.

---

## 2. 핵심 수치

### A. 최신 시도 기준 (`entry_pipeline_flow`)

- `tracked_stocks=181`
- `budget_pass_stocks=2`
- `submitted_stocks=0`
- `budget_pass_to_submitted_rate=0.0%`
- `blocked_stocks=26`

이 수치는 "각 종목의 마지막 시도"만 남긴 결과다.  
`budget_pass` 후 `latency_block`을 여러 번 반복한 종목도 마지막 상태가 `blocked_overbought`, `blocked_gatekeeper_reject`, `strength_momentum_observed` 등으로 바뀌면 `budget_pass_stocks`에서 빠진다.

### B. 이벤트 기준 (`pipeline_events`, `performance_tuning`)

- `budget_pass_events=3923`
- `order_bundle_submitted_events=24`
- `budget_pass_event_to_submitted_rate=0.6%`
- `latency_block_events=3899`
- `latency_pass_events=24`
- `quote_fresh_latency_blocks=2963`
- `quote_fresh_latency_passes=24`
- `quote_fresh_latency_pass_rate=0.8%`
- `expired_armed_events=399`

이 수치가 실제 주문 직전 병목의 본체다.  
즉 "budget_pass 자체가 거의 안 나온다"보다, "budget_pass는 계속 나오는데 submitted로 거의 안 넘어간다"가 더 정확한 해석이다.

---

## 3. 왜 canary가 0건이었는가

### 코드 현황

- 기본값: `src/utils/constants.py`
  - `SCALP_LATENCY_GUARD_CANARY_ENABLED=True`
  - `SCALP_LATENCY_GUARD_CANARY_TAGS=("SCANNER", "VWAP_RECLAIM", "OPEN_RECLAIM")`
  - `SCALP_LATENCY_GUARD_CANARY_MIN_SIGNAL_SCORE=85.0`

- 호출부: `src/engine/sniper_state_handlers.py`
  - `signal_strength=float(stock.get('rt_ai_prob', ...))`

- canary 판정부: `src/engine/sniper_entry_latency.py`
  - 기존에는 `0.86 < 85.0`처럼 비교되어 사실상 전건 `low_signal`이었다.

### 실데이터 분포

- `latency_canary_reason=low_signal`: `1949`
- `latency_canary_reason=tag_not_allowed`: `1014`
- `latency_canary_reason=quote_stale`: `936`

추가 확인:

- `low_signal`인데 `ai_score >= 85.0`인 케이스가 `260`건 존재
- 이는 canary가 꺼져서가 아니라 **점수 스케일 버그로 잘못 차단**됐다는 뜻이다

### bugfix-only 기대치

현재 태그/임계값을 그대로 두고 점수 스케일만 바로잡으면, `2026-04-16` 데이터 기준 canary 조건을 통과했어야 할 표본은 `110`건이다.

- `SCANNER`: `30`
- `VWAP_RECLAIM`: `80`

이는 `budget_pass_events=3923` 전체를 바로 복구하는 수준은 아니지만, "의도한 canary 경로가 0건"인 비정상 상태는 장전 전에 해소할 수 있는 수준이다.

---

## 4. 지금 바로 해석을 바꿔야 하는 부분

1. 판정: "상단 퍼널이 막혀서 `budget_pass`가 2건뿐"이라는 문장은 부정확하다.
   - 근거: 최신 시도 기준은 2건이지만, 실제 이벤트는 `3923`건이다.
   - 다음 액션: `budget_pass_stocks`는 최신 시도 분포 설명용으로만 쓰고, 병목 판단은 이벤트 기준으로 옮긴다.

2. 판정: 주병목은 여전히 `budget_pass 이후 latency guard`다.
   - 근거: 이벤트 기준 `budget_pass_events=3923`, `latency_block_events=3899`, `latency_pass_events=24`다.
   - 다음 액션: `overbought/gatekeeper/swing_gap`은 "최신 종단 상태"로 보고, 실주문 병목의 1차 원인으로는 분리한다.

3. 판정: `quote_stale`만의 문제가 아니다.
   - 근거: `quote_fresh_latency_blocks=2963`로 stale이 아닌데도 대부분 DANGER다.
   - 다음 액션: 장전 반영은 bugfix-only로 제한하고, 이후 1축 canary는 `tag` 또는 `jitter` 중 하나만 추가로 건드린다.

---

## 5. 내일 장전 전 해소 가능 범위

### 가능

- `latency canary signal score` 스케일 버그 수정
- `entry_pipeline_flow`의 최신 시도 기준 vs 이벤트 기준 분리 표기
- PREOPEN 판단 로직을 `event funnel` 기준으로 교정

### 불가 또는 보류

- `budget_pass -> submitted` 전체 병목의 완전 해소
- `jitter`, `tag`, `min_signal`, `ws_age`를 한 번에 동시에 완화하는 다축 튜닝
- Gatekeeper 장지연 격리 같은 구조 개편

즉 **내일 장전까지 "관측 착시 제거 + 의도된 canary 경로 복구"는 가능하지만, 병목 전체 해소는 아니다.**

---

## 6. 내일 장전 권고안

1. 판정: `bugfix-only` 반영은 승인 가능.
   - 근거: 점수 스케일 버그는 의도한 canary 동작을 막는 명백한 구현 오류이고, 현재 태그/임계값을 바꾸지 않아도 된다.
   - 다음 액션: bugfix 적용 후 `latency_canary_applied`, `latency_canary_reason`, `budget_pass_event_to_submitted_rate`를 09:00~09:30 우선 관찰한다.

2. 판정: `tag` 확장이나 `min_signal` 완화는 장전 즉시 동시 반영하지 않는다.
   - 근거: `lower_min_ai_80`은 동일 데이터 기준 잠재 통과 표본이 `490`건으로 급증해 리스크가 크다. `DRYUP_SQUEEZE/SCALP_BASE/PRECLOSE` 태그 확장도 추가 효과는 있으나 bugfix와 동시에 넣으면 원인 분리가 불가능해진다.
   - 다음 액션: bugfix 반영 후에도 `latency_canary_applied`가 충분히 나오지 않으면 다음 1축은 `tag expansion` 우선으로 검토한다.

3. 판정: `jitter` 계산식 개편과 Gatekeeper 격리는 P1 후속이다.
   - 근거: 둘 다 실병목 가능성이 높지만 장전 직전 단축 반영으로는 검증 범위가 크다.
   - 다음 액션: 장후에 `quote_fresh_latency_blocks`, `ws_jitter_too_high`, `gatekeeper_eval_ms_p95`를 다시 보고 shadow-only 설계로 넘긴다.

---

## 7. 참고 코드/문서

- `src/engine/sniper_entry_latency.py`
- `src/engine/sniper_entry_pipeline_report.py`
- `src/engine/sniper_state_handlers.py`
- `src/utils/constants.py`
- [2026-04-17-stage2-todo-checklist.md](./2026-04-17-stage2-todo-checklist.md)
