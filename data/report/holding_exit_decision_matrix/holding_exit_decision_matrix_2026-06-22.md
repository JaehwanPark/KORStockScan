# Holding/Exit Decision Matrix - 2026-06-22

## 판정

- matrix_version: `holding_exit_decision_matrix_v1_2026-06-22`
- application_mode: `advisory_canary_live_readiness_until_owner_approval`
- runtime_change: `False`

## Hard Veto

- `emergency_or_hard_stop`
- `active_sell_order_pending`
- `invalid_feature`
- `post_add_eval_exclusion`

## Counterfactual Coverage

- non_no_clear_edge_count: `0`
- no_clear_edge_count: `12`
- candidate_weight_source_non_clear_edge_count: `0`
- ready_count: `0` / `12`
- ready_rate: `0`
- per_action_edge_buckets: `{'prefer_exit': 0, 'prefer_avg_down_wait': 0, 'prefer_pyramid_wait': 0}`
- per_action_samples: `{'exit_only': 30, 'avg_down_wait': 0, 'pyramid_wait': 3}`
- proxy_sample_snapshots: `1696`
- proxy_joined_candidates: `0`
- proxy_actions_present: `['hold_defer', 'exit_only', 'avg_down_wait', 'pyramid_wait']`
- proxy_missing_actions: `[]`
- proxy_per_action_samples: `{'hold_defer': 1600, 'exit_only': 428, 'avg_down_wait': 1147, 'pyramid_wait': 405}`


## Matrix Entries

| axis | bucket | bias | score | edge | sample | loss_rate | cf_ready | missing_actions | policy |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| price_bucket | price_10k_30k | no_clear_edge | - | - | - | - | False | avg_down_wait,pyramid_wait | insufficient_sample |
| price_bucket | price_30k_70k | no_clear_edge | - | - | - | - | False | avg_down_wait | insufficient_sample |
| price_bucket | price_gte_70k | no_clear_edge | -2.104 | - | 5 | 0.8 | False | avg_down_wait,pyramid_wait | defensive_only_high_loss_rate |
| price_bucket | price_lt_10k | no_clear_edge | - | - | - | - | False | avg_down_wait,pyramid_wait | insufficient_sample |
| volume_bucket | volume_2m_10m | no_clear_edge | - | - | - | - | False | avg_down_wait | insufficient_sample |
| volume_bucket | volume_500k_2m | no_clear_edge | - | - | - | - | False | avg_down_wait,pyramid_wait | insufficient_sample |
| volume_bucket | volume_gte_10m | no_clear_edge | - | - | - | - | False | avg_down_wait,pyramid_wait | insufficient_sample |
| volume_bucket | volume_lt_500k | no_clear_edge | - | - | - | - | False | avg_down_wait,pyramid_wait | insufficient_sample |
| volume_bucket | volume_unknown | no_clear_edge | - | - | - | - | False | avg_down_wait,pyramid_wait | insufficient_sample |
| time_bucket | time_0930_1030 | no_clear_edge | - | - | - | - | False | avg_down_wait,pyramid_wait | insufficient_sample |
| time_bucket | time_1030_1400 | no_clear_edge | -1.3107 | - | 7 | 0.5714 | False | avg_down_wait | candidate_weight_source |
| time_bucket | time_1400_1530 | no_clear_edge | - | - | - | - | False | avg_down_wait,pyramid_wait | insufficient_sample |

## Prompt Hints

- `price_bucket=price_10k_30k` / `no_clear_edge`: price_bucket=price_10k_30k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `price_bucket=price_30k_70k` / `no_clear_edge`: price_bucket=price_30k_70k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `price_bucket=price_gte_70k` / `no_clear_edge`: price_bucket=price_gte_70k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `price_bucket=price_lt_10k` / `no_clear_edge`: price_bucket=price_lt_10k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_2m_10m` / `no_clear_edge`: volume_bucket=volume_2m_10m 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_500k_2m` / `no_clear_edge`: volume_bucket=volume_500k_2m 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_gte_10m` / `no_clear_edge`: volume_bucket=volume_gte_10m 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_lt_500k` / `no_clear_edge`: volume_bucket=volume_lt_500k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_unknown` / `no_clear_edge`: volume_bucket=volume_unknown 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_0930_1030` / `no_clear_edge`: time_bucket=time_0930_1030 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_1030_1400` / `no_clear_edge`: time_bucket=time_1030_1400 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_1400_1530` / `no_clear_edge`: time_bucket=time_1400_1530 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.

## 다음 액션

- `ADM`은 shadow가 아니라 advisory canary/live-readiness 축으로 관리한다.
- `recommended_bias != no_clear_edge`이고 `policy_hint=candidate_weight_source`인 bucket만 다음 bounded canary 후보로 본다.
- all `no_clear_edge`이면 perfect spot 대기가 아니라 최소 edge 부재로 판정하고 live AI 응답을 바꾸지 않는다.
