# Holding/Exit Decision Matrix - 2026-07-01

## 판정

- matrix_version: `holding_exit_decision_matrix_v1_2026-07-01`
- application_mode: `advisory_canary_live_readiness_until_owner_approval`
- runtime_change: `False`

## Hard Veto

- `emergency_or_hard_stop`
- `active_sell_order_pending`
- `invalid_feature`
- `post_add_eval_exclusion`

## Counterfactual Coverage

- non_no_clear_edge_count: `3`
- no_clear_edge_count: `11`
- candidate_weight_source_non_clear_edge_count: `3`
- ready_count: `3` / `14`
- ready_rate: `0.2143`
- per_action_edge_buckets: `{'prefer_exit': 2, 'prefer_avg_down_wait': 1, 'prefer_pyramid_wait': 0}`
- per_action_samples: `{'exit_only': 210, 'avg_down_wait': 42, 'pyramid_wait': 3}`
- proxy_sample_snapshots: `4806`
- proxy_joined_candidates: `1153`
- proxy_actions_present: `['hold_defer', 'exit_only', 'avg_down_wait', 'pyramid_wait']`
- proxy_missing_actions: `[]`
- proxy_per_action_samples: `{'hold_defer': 4336, 'exit_only': 485, 'avg_down_wait': 3082, 'pyramid_wait': 1289}`


## Matrix Entries

| axis | bucket | bias | score | edge | sample | loss_rate | cf_ready | missing_actions | policy |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| price_bucket | price_10k_30k | no_clear_edge | -0.9494 | - | 17 | 0.5294 | False | pyramid_wait | candidate_weight_source |
| price_bucket | price_30k_70k | no_clear_edge | -0.312 | - | 18 | 0.4444 | False | pyramid_wait | candidate_weight_source |
| price_bucket | price_gte_70k | prefer_avg_down_wait | -0.0218 | 0.1643 | 8 | 0.375 | True | - | candidate_weight_source |
| price_bucket | price_lt_10k | no_clear_edge | - | - | - | - | False | avg_down_wait,pyramid_wait | insufficient_sample |
| volume_bucket | volume_2m_10m | no_clear_edge | -1.8788 | - | 9 | 0.6667 | False | pyramid_wait | defensive_only_high_loss_rate |
| volume_bucket | volume_500k_2m | prefer_exit | -0.2599 | 1.3213 | 25 | 0.44 | False | pyramid_wait | candidate_weight_source |
| volume_bucket | volume_gte_10m | no_clear_edge | - | - | - | - | False | avg_down_wait,pyramid_wait | insufficient_sample |
| volume_bucket | volume_lt_500k | no_clear_edge | -0.0285 | - | 29 | 0.4138 | False | pyramid_wait | candidate_weight_source |
| volume_bucket | volume_unknown | no_clear_edge | -2.4124 | - | 6 | 0.5 | True | - | candidate_weight_source |
| time_bucket | time_0900_0930 | no_clear_edge | - | - | - | - | False | pyramid_wait | insufficient_sample |
| time_bucket | time_0930_1030 | no_clear_edge | -0.4064 | - | 15 | 0.2667 | True | - | candidate_weight_source |
| time_bucket | time_1030_1400 | prefer_exit | 0.3264 | 0.3126 | 14 | 0.1429 | False | pyramid_wait | candidate_weight_source |
| time_bucket | time_1400_1530 | no_clear_edge | -0.5957 | - | 8 | 0.875 | False | avg_down_wait,pyramid_wait | defensive_only_high_loss_rate |
| time_bucket | time_outside_regular | no_clear_edge | -1.2932 | - | 29 | 0.6207 | False | pyramid_wait | candidate_weight_source |

## Prompt Hints

- `price_bucket=price_10k_30k` / `no_clear_edge`: price_bucket=price_10k_30k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `price_bucket=price_30k_70k` / `no_clear_edge`: price_bucket=price_30k_70k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `price_bucket=price_gte_70k` / `prefer_avg_down_wait`: price_bucket=price_gte_70k 과거 표본은 회복형 물타기 대기 후보가 상대적으로 우위다. 저점 미갱신과 수급 회복이 없으면 무시한다.
- `price_bucket=price_lt_10k` / `no_clear_edge`: price_bucket=price_lt_10k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_2m_10m` / `no_clear_edge`: volume_bucket=volume_2m_10m 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_500k_2m` / `prefer_exit`: volume_bucket=volume_500k_2m 과거 표본은 보유/추가매수보다 청산 우위가 있다. 단 hard veto와 현재 thesis를 먼저 확인한다.
- `volume_bucket=volume_gte_10m` / `no_clear_edge`: volume_bucket=volume_gte_10m 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_lt_500k` / `no_clear_edge`: volume_bucket=volume_lt_500k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_unknown` / `no_clear_edge`: volume_bucket=volume_unknown 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_0900_0930` / `no_clear_edge`: time_bucket=time_0900_0930 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_0930_1030` / `no_clear_edge`: time_bucket=time_0930_1030 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_1030_1400` / `prefer_exit`: time_bucket=time_1030_1400 과거 표본은 보유/추가매수보다 청산 우위가 있다. 단 hard veto와 현재 thesis를 먼저 확인한다.
- `time_bucket=time_1400_1530` / `no_clear_edge`: time_bucket=time_1400_1530 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_outside_regular` / `no_clear_edge`: time_bucket=time_outside_regular 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.

## 다음 액션

- `ADM`은 shadow가 아니라 advisory canary/live-readiness 축으로 관리한다.
- `recommended_bias != no_clear_edge`이고 `policy_hint=candidate_weight_source`인 bucket만 다음 bounded canary 후보로 본다.
- all `no_clear_edge`이면 perfect spot 대기가 아니라 최소 edge 부재로 판정하고 live AI 응답을 바꾸지 않는다.
