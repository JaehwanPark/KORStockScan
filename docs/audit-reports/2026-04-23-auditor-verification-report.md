# 2026-04-23 감리인 성과보고서 재검토 결과

검토일: `2026-04-23`
검토자: `시스템트레이더(감사인)`
검토 대상: `docs/2026-04-23-auditor-performance-result-report.md`
근거: `performance_tuning_2026-04-23.json`, `trade_review_2026-04-23.json`, `wait6579_ev_cohort_2026-04-23.json`, `post_sell_feedback_2026-04-23.json`, `remote server_comparison`

---

## 판정
`조건부 보류 유지`는 부적절하다. 판정은 `긴급 시정`으로 상향해야 한다.

근거: `entry_armed -> submitted`에서 154→78→45→1의 퍼널 수축은 후보의 부재가 아니라 **제출 단계의 구조적 차단**이다. `budget_pass_events=4,373` 중 `order_bundle_submitted=3`, `latency_block=4,370`로 99.9%가 제출 직전에 차단된다. 이 상태에서 동일 축 재판정만 반복하면 동일 결과가 재생산된다.

---

## 판정 근거

### 1) 수치 정합성은 맞지만, 결론만 보면 안 된다

- `performance_tuning_2026-04-23.json`: `candidates(스캘핑)=154`, `ai_confirmed=78`, `entry_armed=45`, `submitted=1`.
- 동일 파일: `budget_pass_events=4373`, `order_bundle_submitted_events=3`, `latency_block_events=4370`, `quote_fresh_latency_blocks=4029`, `quote_fresh_latency_pass_rate=0.1%`.
- 동일 파일: `gatekeeper_eval_ms_p95=22653ms`, `gatekeeper_lock_wait_ms_p95=0ms`, `gatekeeper_fast_reuse_ratio=0.0`.
- `trade_review_2026-04-23.json`: `total_trades=2`, `COMPLETED=2`, `full_fill=2`, `partial_fill=0`, `avg_profit_rate=-0.47`.
- `wait6579_ev_cohort_2026-04-23.json`: `total_candidates=307`, `recovery_check=27`, `recovery_promoted=15`, `budget_pass=18`, `latency_pass=0`, `submitted=0`, `submission_blocker: no_budget_pass 94.1%, latency_block 5.9%`.
- `post_sell_feedback_2026-04-23.json`: `evaluated_candidates=2`, `missed_upside_rate=0.0`, `good_exit_rate=50.0`, `capture_efficiency_avg_pct=58.3`.

### 2) "느슨한 계획"을 유발한 지점

- 기존 보고서는 문제의 본질을 인지하였으나, 판정 문구를 낮게 두고 다음 액션을 계속 `재판정`과 `보류`에 남겨두어 조치 선순위가 흐려졌다.
- `entry_armed -> submitted` 핵심 병목이 잠겨 있는데 `entry_filter_quality`/`AI A/B`/`score-promote`를 동시에 잠금-재판정으로만 다루면 **원인 미변경 상태가 지속**된다.
- 따라서 `판정↑`보다 중요한 것은 `다음 액션`의 실천 강도다. 즉시 조치형 액션이 선행되어야 한다.

### 3) 검증축 중복금지 준수 여부

- 허용된 검증층은 3개로 단일화한다.  
  실시간 퍼널 축: `candidates→ai_confirmed→entry_armed→submitted`.  
  제출 직전 병목 분해: `budget_pass_events` 기반의 `latency_block` 원인 분해.  
  정책/성과 축: `COMPLETED+valid` 퍼널·이익·보유 포렌식.
- 이 3개 이외의 동일 지표 반복 비교(예: `budget_pass`와 `latency_block`만 바꾸어가며 여러 번 동일 결론을 내리기)는 금지한다.
- 중복 위험 포인트 1: `order_bundle_submitted=3`과 `submitted=1`은 같은 지표가 아니다. `submitted`를 우선 KPI로 사용하고, bundle 수는 증상 보조치로 제한한다.
- 중복 위험 포인트 2: `trade_review` 성과와 `performance_tuning` 퍼널은 다른 계층이므로 교차 판정만 허용한다.

---

## 핵심 판단

### A. 병목의 실체: latency/quote_fresh가 제출병목 축을 잠근다

- 판정: `latency_block`이 제출 병목의 99.9%를 차지한다.
- 판정 근거: `quote_fresh_latency_blocks=4029`가 `latency_block`의 대부분을 구성한다. `gatekeeper_lock_wait=0`으로 보아 lock 병목은 1순위가 아니며, `model_call` 지연 및 freshness 경로가 우선 후보이다.
- 판정 근거: `WAIT65~79` 경로도 `latency_pass=0`, `submitted=0`으로 upstream 회복은 되나 제출 전이 안 열림.
- 다음 액션: `quote_fresh`는 `spread/ws_age/ws_jitter/quote_stale` 4요인으로 분해 후 원인별 비중을 단일 표로 고정한다.
- 다음 액션: 제출 직전 후보의 중복 재시도인지/고유 symbol 비중인지 확인한다.

### B. buy_recovery_canary 효과의 오해 방지

- 판정: `buy_recovery_canary`는 실효성 기여가 0건으로 유지되며, 현재는 `제출 병목` 보조수단으로만 의미가 있다.
- 판정 근거: `recovery_promoted=15`, `submitted=0`.
- 다음 액션: recovery 수치와 제출 수치는 분리해 해석한다.
- 다음 액션: 재평가된 후보 기여도가 submit으로 연결되지 않으면 downstream 병목 우선 정리 후에만 canary 조건 변경.

### C. HOLDING/확대 판단: 표본 부족으로 결정 정밀도 제한

- 판정: HOLDING hybrid 확대, score/promote 승격, entry_filter_quality 착수는 모두 `표본 미성숙 + 제출 병목 동반` 조건에서 보류는 정합하다.
- 판정 근거: `trade_review`는 2건(완결)으로 표본이 부족하다.
- 판정 근거: HOLDING/soft-stop 관련 포렌식은 근거가 아니라 의사결정 선결 조건(표본) 미달 상태를 기록한 항목이다.
- 다음 액션: 확대·완화는 금지하고, 최소 1일 관측치 축적 이후만 후보화한다.

---

## 즉시 조치형 개선 항목(감사 반영안)

- E-1: 판정 라벨을 `조건부 보류 유지`에서 `긴급 시정`으로 즉시 상향.
- E-2: `quote_fresh` 원인분해를 오늘 장후 보고에 단일표로 넣는다. 항목은 spread/ws_age/ws_jitter/quote_stale 4칸뿐, 재판정 문구는 금지.
- E-3: `budget_pass_events`의 고유 심볼 수, 시도 횟수 분포를 산출해 병목이 중복 재시도인지 확인한다. 분모 팽창이 있으면 제출 KPI 기준만으로 보고서를 해석한다.
- E-4: `roll-back guard` 교차 점검을 동일 문서에 기재한다. 특히 `gatekeeper_eval_ms_p95=22653ms` > 15,900ms 조건 충족 시 경고를 판정에 반영한다.
- E-5: 다음 액션은 최소 1개는 시스템 동작 변경 가정이 들어가야 한다. 무행동 보류/재판정 반복은 허용하지 않는다.

---

## 다음 액션(검증축 중복금지 기준 적용)

1. 오늘 즉시: `quote_fresh` 4요인 분해 + `order_bundle_submitted`와 `submitted`의 역할 주석.
2. 오늘 장후: `submitted` 기준 병목 전용 보류축 잠금, `entry_armed -> submitted` 이외 축은 parking 유지.
3. 내일 PREOPEN: 1축 canary 후보(quote_fresh 하위원인 1개)만 선정해 rollback guard 3개 이상 포함 시도.
4. 내일 12:00~12:20: canary 반나절 판정.
5. 내일 POSTCLOSE: 제출병목 개선이 확인된 경우에만 `entry_filter_quality`/`AI A/B score/promote` 재판정 창으로 이동.

---

## 결론

감리인 지적을 수렴해 판정 레벨은 상향하고, 실행 계획을 압축한다.
이번 보고서의 핵심은 "성능 수치가 나쁘다"가 아니라 **시스템이 제출 단계를 통과하지 못하는 상태를 방치하지 말고 단일 수단으로 즉시 뚫어야 한다**는 점이다.
감사인 1차 결론은 `긴급 시정`이며, 동일한 증거를 다시 감축/확대하는 중복 판정은 중단한다.

---

> 감사인 서명: `시스템트레이더(감사인)`  
> 검토 완료 시각: `2026-04-23 16:45 KST`
