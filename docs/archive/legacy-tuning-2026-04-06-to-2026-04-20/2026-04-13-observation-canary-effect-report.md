# 2026-04-13 관측·Canary·Shadow·Simulation 효과 리포트

> 작성 기준일: `2026-04-13`
> 범위: `2026-04-08 ~ 2026-04-13`
> 목적: 관측/canary/shadow/simulation이 실제로 개선 방향을 잡는 데 어떤 수치적 도움을 줬는지, 반대로 무엇은 아직 아무 효과가 없었는지 한 번에 정리한다.

## 한줄 판정

사용자 비판은 절반 이상 맞다.  
`직접적인 실전 수익 개선이 수치로 입증된 canary/shadow`는 아직 없다.  
다만 `counterfactual + performance_tuning 관측`은 **우선순위 재정렬**과 **잘못된 승격 방지**에는 실제로 도움을 줬다.

## 총평

| 구분 | 개수 | 판정 |
| --- | ---: | --- |
| `직접 uplift 확인` | `0` | 아직 없음 |
| `우선순위 재정렬에 도움` | `3` | 있음 |
| `승격/확대 방지에 도움` | `2` | 있음 |
| `효과 거의 없음` | `3` | 있음 |

핵심은 아래다.

1. `관측`은 방향을 줬다. 특히 `latency vs strength vs overbought` 우선순위는 수치로 갈렸다.
2. `simulation(counterfactual)`은 “더 공격적으로 진입했어야 했는가”에 대해 날짜별로 다른 답을 줬다.
3. 반면 `WATCHING 75 shadow`, `post-sell`, `4/13 remote comparison`은 아직 실질 의사결정 가치를 거의 못 줬다.

## 정량 감사표

| 트랙 | 기간/표본 | 핵심 수치 | 실제 도움 | 판정 |
| --- | --- | --- | --- | --- |
| `missed_entry_counterfactual` | `4/09=20건`, `4/10=21건`, `4/13=5건` | `4/09` 추정 10분 PnL 합 `-104,313원`, `4/10` `+24,960원`, `4/13` `+2,250원` | 같은 `미진입`이라도 날짜별 EV 방향이 반대일 수 있음을 보여줌. blanket relax를 막고, 날짜별 해석을 가능하게 함 | `유의미` |
| `missed_entry reason breakdown` | `4/09~4/13` | `4/09` latency `14건`, strength `5건`, overbought `1건`; `4/10` latency `20건`, strength `1건`; `4/13` liquidity `2건`, latency `2건`, strength `1건` | `latency > strength > overbought` 우선순위를 수치로 고정 | `유의미` |
| `performance_tuning latency breakdown` | `4/13` | `budget_pass=829`, `submitted=2`, `budget_pass_to_submitted_rate=0.2%`, `latency_block=827`, `quote_fresh_latency_blocks=666`, `quote_fresh_latency_passes=2`, `quote_fresh_latency_pass_rate=0.3%` | 병목이 “AI/overbought”보다 `latency guard 내부`에 있음을 확인. 특히 fresh quote인데도 대부분 막히는 구조를 보여줌 | `유의미` |
| `latency danger reason 분해` | `4/13 latency_block=827` | `ws_jitter_too_high=217`, `other_danger=161`, `ws_age_too_high=159`, `quote_stale=110`, `spread_too_wide=93` | `quote_stale`만 고치면 끝나는 문제가 아니라는 점을 수치로 확인. 다음 개선축을 `jitter/ws_age/other_danger` 쪽으로 좁힘 | `유의미` |
| `remote_v2 latency canary` | `4/10 local vs remote` | `gatekeeper_eval_ms_p95`: local `22,469ms`, remote `14,247ms` (`-8,222ms`, 약 `-36.6%`), 하지만 `submitted_stocks`: local `4`, remote `0` | 지연 지표 개선이 바로 진입 개선으로 이어지지 않았음을 보여줌. 잘못된 조기 승격을 막음 | `부분 유의미` |
| `ai_holding_shadow_band` | `4/08 raw 621건` | `review=593`, `skip=28`, `near_ai_exit=True 74건`, `near_safe_profit=True 12건`, 동시 `0건` | near-band 직접 기여가 제한적이라는 근거를 제공. exit rule을 섣불리 건드리지 않게 함 | `부분 유의미` |
| `dual_persona_shadow` | `4/08 유효 표본 9건` | `conflict_ratio=100%`, `effective_override_ratio=0.0%`, `extra_ms_p95=7,666ms` | shadow 충돌은 크고 실질 override는 0이라 즉시 승격 금지 판단에 도움 | `부분 유의미` |
| `WATCHING 75 shadow` | `4/10`, `4/13` | 둘 다 `shadow_samples=0`, `buy_diverged=0`, `joined_missed_rows=0` | 현재까지는 방향성 제공 실패. “켜져 있었는지” 확인 외 실질 효과 없음 | `무효` |
| `post-sell feedback` | `4/10 local=6, remote=1`, `4/13 local=2, remote=1` | 평가 표본이 너무 적어 `timing_tuning_pressure_score`를 조정 근거로 쓰기 어려움 | 현재는 보고서 존재 의미는 있으나 튜닝축 가치 약함 | `무효에 가까움` |
| `4/13 server comparison` | `Performance Tuning`, `Entry Pipeline Flow` | 둘 다 `remote_error=TimeoutError` | 원격 비교검증 자체가 닫히지 않아 canary 판단을 강하게 못 밀어줌 | `무효` |

## 트랙별 핵심 해석

### 1. Counterfactual은 “공격적으로 바꿨으면 무조건 더 좋았는가?”를 부정했다

- `2026-04-09`
  - `evaluated=20`
  - `missed_winner_rate=60.0%`
  - 그런데 `estimated_counterfactual_pnl_10m_krw_sum=-104,313원`
- `2026-04-10`
  - `evaluated=21`
  - `missed_winner_rate=81.0%`
  - `estimated_counterfactual_pnl_10m_krw_sum=+24,960원`

같은 “미진입이 많다”는 관측이라도, `4/09`는 더 공격적으로 들어갔으면 더 잃는 day였고, `4/10`은 반대로 기회비용이 더 큰 day였다.  
즉 이 리포트는 적어도 **blanket relax 금지**라는 중요한 역할은 했다.

### 2. 성능 튜닝 관측은 주병목을 `latency 내부`로 좁혔다

`2026-04-13 performance_tuning` 기준:

- `budget_pass=829`
- `submitted=2`
- `budget_pass_to_submitted_rate=0.2%`
- `latency_block=827`
- `quote_fresh_latency_blocks=666`
- `quote_fresh_latency_passes=2`

이 수치는 “AI가 못 사서”가 아니라 **살 준비가 된 케이스 대부분이 latency guard에서 막혔다**는 뜻이다.  
게다가 danger 분해 결과도:

- `ws_jitter_too_high=217`
- `other_danger=161`
- `ws_age_too_high=159`
- `quote_stale=110`
- `spread_too_wide=93`

즉 `quote_stale`만 완화한다고 해결될 구조가 아니라는 점까지 보여줬다.

### 3. remote_v2 canary는 “좋은 숫자지만 승격 못 함”을 보여줬다

`2026-04-10 local vs remote` 기준:

- `gatekeeper_eval_ms_p95`
  - local `22,469ms`
  - remote `14,247ms`
- 하지만 `submitted_stocks`
  - local `4`
  - remote `0`

이건 canary가 **좋은 느낌**은 줬지만, **실제 funnel uplift를 못 만들었다**는 뜻이다.  
즉 “효과가 있었다”가 아니라 “이 숫자만 보고 승격하면 안 된다”는 음의 근거를 제공했다.

### 4. 일부 shadow는 아직 사실상 0점이다

`WATCHING 75 shadow`

- `2026-04-10 shadow_samples=0`
- `2026-04-13 shadow_samples=0`

이 트랙은 현재까지 **실질적인 방향성 정보를 하나도 못 줬다**.  
사용자 비판대로 “있다고 해서 도움되는 관측축”은 아니다.

### 5. post-sell은 보고서가 크지만 아직 튜닝축은 아니다

- `2026-04-10 evaluated_candidates`: local `6`, remote `1`
- `2026-04-13 evaluated_candidates`: local `2`, remote `1`

표본이 너무 적어서 `timing_tuning_pressure_score`나 `estimated_extra_upside_10m_krw_sum`을 실제 튜닝 근거로 밀기 어렵다.  
즉 현재는 존재 가치가 “없다”기보다, **장후 설명용 비중이 튜닝용 비중보다 크다**.

## 최종 판정

사용자 비판 중 맞는 부분:

1. `WATCHING 75 shadow`, `post-sell`, `4/13 remote comparison`은 아직 실전 개선 방향을 잡는 데 거의 기여하지 못했다.
2. `직접 uplift`를 만든 canary/shadow는 아직 없다.
3. 따라서 “관측을 많이 했으니 곧 좋아질 것”이라는 식의 설명은 설득력이 약하다.

반박 가능한 부분:

1. `counterfactual`은 날짜별 EV 방향을 갈라줬다.
2. `performance_tuning`은 병목이 `AI/overbought`가 아니라 `latency guard 내부`라는 것을 수치로 입증했다.
3. `remote_v2 canary`는 승격할 근거는 못 줬지만, 승격하면 안 되는 이유를 줬다.

즉 요약하면:

- `관측/시뮬레이션`은 **방향 설정**에는 도움을 줬다.
- `canary/shadow`는 **직접 uplift 입증**에는 아직 실패했다.
- 특히 `0-sample shadow`와 `timeout 비교`는 계속 유지할 이유가 약하다.

## 지금 시점의 실무 결론

1. 계속 봐야 하는 것
   - `missed_entry_counterfactual`
   - `performance_tuning latency breakdown`
2. 빠르게 승부 봐야 하는 것
   - `작업 10 HOLDING hybrid 적용`
   - `FORCE_EXIT 제한형 MVP`
3. 정리하거나 낮춰야 하는 것
   - `WATCHING 75 shadow`가 표본 0 상태를 반복하면 우선순위 하향
   - `post-sell`은 표본이 늘기 전까지 설명 지표로만 사용
   - `server_comparison`은 `remote_error`를 닫지 못하면 운영 판단 근거에서 비중 축소

## 참고 근거

- [performance_tuning_2026-04-13.json](../data/report/monitor_snapshots/performance_tuning_2026-04-13.json)
- [missed_entry_counterfactual_2026-04-09.json](../data/report/monitor_snapshots/missed_entry_counterfactual_2026-04-09.json)
- [missed_entry_counterfactual_2026-04-10.json](../data/report/monitor_snapshots/missed_entry_counterfactual_2026-04-10.json)
- [missed_entry_counterfactual_2026-04-13.json](../data/report/monitor_snapshots/missed_entry_counterfactual_2026-04-13.json)
- [server_comparison_2026-04-10.md](../data/report/server_comparison/server_comparison_2026-04-10.md)
- [server_comparison_2026-04-13.md](../data/report/server_comparison/server_comparison_2026-04-13.md)
- [watching_prompt_75_shadow_2026-04-10.md](../tmp/watching_prompt_75_shadow_2026-04-10.md)
- [watching_prompt_75_shadow_2026-04-13.md](../tmp/watching_prompt_75_shadow_2026-04-13.md)
- [2026-04-08-stage2-todo-checklist.md](./checklists/2026-04-08-stage2-todo-checklist.md)
