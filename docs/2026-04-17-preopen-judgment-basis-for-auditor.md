# 2026-04-17 PREOPEN 판정 근거서 (감사인 제출용)

작성일: 2026-04-17  
제출 대상: 감사인  
기준 문서: `docs/2026-04-17-stage2-todo-checklist.md`  
기준 로그/스냅샷: `trade_review_2026-04-16`, `performance_tuning_2026-04-16`, `entry_pipeline_flow_2026-04-16`, `add_blocked_lock_2026-04-16`

휴일 보정: `2026-04-18~2026-04-19`는 휴일로, 후속 실행 슬롯은 `2026-04-20` 기준으로 재배치함.

---

## 1. 제출 목적

본 문서는 `2026-04-17 PREOPEN`에서 처리한 주요 운영 판정의 근거를
체크리스트 원문과 분리해 감사인이 바로 검토할 수 있도록 재구성한 별도 제출본이다.

정리 원칙은 아래와 같다.

1. 손익 파생값보다 거래수, 퍼널, blocker 분포, 체결 품질을 우선한다.
2. `NULL`, 미완료 상태, fallback 정규화 값은 손익 판단 근거에서 제외한다.
3. 실전 로직 변경은 한 번에 한 축 canary만 허용하며, 가능하면 `shadow-only`를 우선한다.

---

## 2. 요약 판정

1. 판정: `entry_pipeline` 해석은 **최신 시도 기준이 아니라 이벤트 기준 퍼널로 고정**한다.
   - 근거: `budget_pass_stocks=2`는 최신 상태 착시였고, 실제 이벤트 기준은 `budget_pass_events=3923`, `order_bundle_submitted_events=24`, `budget_pass_event_to_submitted_rate=0.6%`였다.
   - 다음 액션: 장전/장중 판정 분모를 `budget_pass_event_to_submitted_rate`, `latency_block_events`로 고정한다.

2. 판정: `latency canary signal-score` bugfix는 **반영 검증 완료**다.
   - 근거: `signal_strength=0.x` 입력을 `0~100` 점수로 정규화하는 회귀 테스트가 통과했고, 기존 `low_signal` 오차 차단을 설명할 수 있었다.
   - 다음 액션: 장중 첫 30분 `latency_canary_applied`, `low_signal`, `tag_not_allowed`, `quote_stale` 분포를 재판정한다.

3. 판정: `latency canary` 추가 완화(`tag/min_score`)는 **금일 미승인**이다.
   - 근거: bugfix-only 잠재 복구가 `110건`인 반면, `min_score 80` 완화는 `490건` 수준으로 리스크가 급증한다.
   - 다음 액션: bugfix-only 실표본을 먼저 보고 다음 1축을 `tag expansion` 또는 보류 중 하나로 다시 정한다.

4. 판정: `SCALP loss_fallback` 실전 전환은 **미승인(기본 OFF 유지)**이며, 하위 결정은 `롤백 우선`으로 고정했다.
   - 근거: `loss_fallback_probe` 로그에서 `fallback_candidate=True`가 0건이었고, `add_judgment_locked` 차단도 남아 있었다.
   - 다음 액션: `skip_add_judgment_lock` 우회를 제거한 롤백안을 먼저 검증하고, 미해소 시 lock key 분리안을 다음 1축으로 승격한다.

5. 판정: `SCANNER 일반 포지션 timeout`은 **조건부 승인(shadow-only)**이다.
   - 근거: 롯데쇼핑/올릭스는 현행 `fallback 전용 조기정리 로직`으로 직접 커버되지 않았다.
   - 다음 액션: `scanner_never_green_timeout_shadow` 후보 로그만 수집하고, 실전 반영은 장후 재판정 후 결정한다.

6. 판정: `scalping_exit action schema` 완전 분리는 **실전 미포함 유지**다.
   - 근거: 현재 운영 경로는 `BUY/WAIT/DROP` 유산 스키마와 호환 상태이며, 금일 실전 반영 범위에 포함되지 않았다.
   - 다음 액션: `파싱 양방향 호환 -> HOLDING schema shadow-only -> parse/미체결/지연 가드 통과 시 canary` 순서로 진행한다.

---

## 3. 항목별 근거

### 3-1. Entry Pipeline latest/event 정합성

1. 판정: `budget_pass -> submitted` 실병목은 유지되며, 해석 기준만 교정해야 한다.
   - 근거: `build_entry_pipeline_flow_report('2026-04-16')` 재검증 결과
     `budget_pass_stocks=2`, `submitted_stocks=0`, `budget_pass_to_submitted_rate=0.0%`였지만,
     이벤트 기준으로는 `budget_pass_events=3923`, `order_bundle_submitted_events=24`,
     `budget_pass_event_to_submitted_rate=0.6%`, `latency_block_events=3899`였다.
   - 다음 액션: 최신 시도 기준은 "종단 상태 설명"에만 쓰고, 운영 판정은 이벤트 기준 퍼널로만 유지한다.

### 3-2. Latency Canary 정규화 bugfix

1. 판정: 점수 정규화 bugfix는 구현/회귀 기준으로 검증 완료다.
   - 근거: `src/tests/test_sniper_entry_latency.py`의
     `test_latency_entry_canary_normalizes_probability_signal_strength`가 통과했다.
     전체 회귀 실행 결과는 `12 passed`.
   - 다음 액션: 실표본 기준에서 `latency_canary_applied`가 0건을 벗어나는지 확인한다.

2. 판정: 기존 `low_signal` 대량 차단은 비활성이라기보다 스케일 불일치의 결과였다.
   - 근거: `2026-04-16` 로그에서 `latency_canary_reason` 분포는
     `low_signal 234`, `tag_not_allowed 76`, `quote_stale 60`으로 재계수됐다.
   - 다음 액션: bugfix-only 상태에서 `low_signal` 감소 여부를 우선 관찰한다.

### 3-3. SCALP Loss Fallback

1. 판정: `loss_fallback_probe add_judgment_locked` 우회 검증은 실패였고, 후속 조치로 우회 롤백을 적용했다.
   - 근거: `logs/pipeline_event_logger_info.log*` 기준 `loss_fallback_probe=4건`,
     그중 `gate_reason=add_judgment_locked 1건`으로 비중이 `25%`였다.
   - 다음 액션: 롤백 적용 후 `gate_reason` 분포를 다시 계수하고, 잔존 시 lock key 분리안을 적용한다.

2. 판정: 실전 전환 근거는 아직 없다.
   - 근거: 동일 로그 및 `trade_review_2026-04-16` 스냅샷 기준
     `fallback_candidate=True`는 `0건`, 스냅샷 내 `gate_reason=add_judgment_locked`는 `4건`이었다.
   - 다음 액션: `SCALP_LOSS_FALLBACK_ENABLED=False`,
     `SCALP_LOSS_FALLBACK_OBSERVE_ONLY=True`를 유지한다.

### 3-4. SCANNER 일반 포지션 Timeout Shadow

1. 판정: 일반 SCANNER 장기 표류에 대한 별도 shadow 축은 필요하다.
   - 근거: `trade_review_2026-04-16` 스냅샷에서 롯데쇼핑/올릭스가 `SCANNER` 포지션으로 확인되며,
     현행 로직은 `entry_mode=fallback` 조기정리에 치우쳐 있다.
   - 다음 액션: `scanner_never_green_timeout_shadow` 후보만 기록하는 `shadow-only` 조건으로 1일치 표본을 먼저 수집한다.

### 3-5. A/B 시나리오 및 Action Schema

1. 판정: 모델별 A/B 시나리오는 감사 기준에 맞게 분리 고정했다.
   - 근거: 실험군/대조군, 중단조건, 평가 기준을
     [2026-04-17-model-ab-test-scenario-draft.md](/home/ubuntu/KORStockScan/docs/2026-04-17-model-ab-test-scenario-draft.md)
     에 확정했다.
   - 다음 액션: POSTCLOSE 비교표도 동일 기준으로 고정한다.

2. 판정: `scalping_exit` schema 완전 분리는 계획축으로만 유지한다.
   - 근거: 현재 운영은 `HOLDING action schema(HOLD/SELL/FORCE_EXIT)`로 완전히 분리되지 않았고,
     실전 변경 시 원인 귀속을 흐릴 수 있다.
   - 다음 액션: `shadow-only` 선행 후 `parse_error`, `미체결`, `지연` 가드를 통과했을 때만 canary로 올린다.

---

## 4. 검증 결과

### 테스트

- `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_sniper_entry_latency.py src/tests/test_entry_pipeline_report.py`
- 결과: `12 passed`

### 리포트 재생성/재검증

- `PYTHONPATH=. .venv/bin/python -m src.engine.add_blocked_lock_report --date 2026-04-16`
- 결과: `total_blocked_events=1392`, `stagnation_blocked_events=941`

### 자동화 동기화 상태

1. 판정: `문서 -> GitHub Project -> Calendar` 동기화는 사용자 지시로 `수동 진행`으로 전환했다.
   - 근거: 본 세션 작업 지시에서 GitHub/Calendar 동기화는 수동 진행으로 명시됐다.
   - 다음 액션: 수동 동기화 결과(생성/갱신 건수, 실패 항목, 재실행 필요 여부)를 체크리스트에 역기록한다.

### 장후 체크리스트 반영 상태

1. 판정: `AIPrompt P2/작업7/작업9` 항목은 `착수 또는 보류 사유 기록` 기준으로 닫았다.
   - 근거: 체크리스트에 세 항목 모두 판정/근거/다음 액션이 추가되었고, `P1 보류 시 사유 + 다음 실행시각`도 함께 기록됐다.
   - 다음 액션: `2026-04-20 PREOPEN/POSTCLOSE` 슬롯에서 착수 여부를 재판정한다.

---

## 5. 감사인 확인 요청 포인트

1. `latency canary`는 bugfix-only 관찰 후에도 추가 완화를 보수적으로 1축씩 여는 접근이 타당한지 확인 요청.
2. `loss_fallback_probe`는 실전 전환보다 `lock 충돌 제거`를 먼저 보는 현재 우선순위가 타당한지 확인 요청.
3. `SCANNER 일반 포지션 timeout`을 곧바로 canary가 아니라 `shadow-only`로 두는 것이 적절한지 확인 요청.
4. `scalping_exit action schema` 분리를 실전 즉시 반영하지 않고 `shadow-only`로 단계화하는 것이 적절한지 확인 요청.

---

## 6. 참고 문서

- [2026-04-17-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-17-stage2-todo-checklist.md)
- [2026-04-16-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-16-stage2-todo-checklist.md)
- [2026-04-16-budget-pass-submitted-bottleneck-analysis.md](/home/ubuntu/KORStockScan/docs/2026-04-16-budget-pass-submitted-bottleneck-analysis.md)
- [2026-04-16-holding-profit-conversion-plan.md](/home/ubuntu/KORStockScan/docs/2026-04-16-holding-profit-conversion-plan.md)
- [2026-04-17-model-ab-test-scenario-draft.md](/home/ubuntu/KORStockScan/docs/2026-04-17-model-ab-test-scenario-draft.md)
