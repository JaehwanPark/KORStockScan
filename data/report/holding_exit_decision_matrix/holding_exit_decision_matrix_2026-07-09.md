# Holding/Exit Decision Matrix - 2026-07-09

## 판정

- matrix_version: `holding_exit_decision_matrix_v1_2026-07-09`
- application_mode: `advisory_canary_live_readiness_until_owner_approval`
- runtime_change: `False`

## Hard Veto

- `emergency_or_hard_stop`
- `active_sell_order_pending`
- `invalid_feature`
- `post_add_eval_exclusion`

## Counterfactual Coverage

- non_no_clear_edge_count: `4`
- no_clear_edge_count: `10`
- candidate_weight_source_non_clear_edge_count: `4`
- ready_count: `3` / `14`
- ready_rate: `0.2143`
- per_action_edge_buckets: `{'prefer_exit': 4, 'prefer_avg_down_wait': 0, 'prefer_pyramid_wait': 0}`
- per_action_samples: `{'exit_only': 237, 'avg_down_wait': 63, 'pyramid_wait': 3}`
- proxy_sample_snapshots: `628`
- proxy_joined_candidates: `178`
- proxy_actions_present: `['hold_defer', 'exit_only', 'avg_down_wait', 'pyramid_wait']`
- proxy_missing_actions: `[]`
- proxy_per_action_samples: `{'hold_defer': 611, 'exit_only': 29, 'avg_down_wait': 549, 'pyramid_wait': 61}`


## Matrix Entries

| axis | bucket | bias | score | edge | sample | loss_rate | cf_ready | missing_actions | policy |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| price_bucket | price_10k_30k | no_clear_edge | -1.3233 | 0.0206 | 29 | 0.4828 | False | pyramid_wait | no_clear_edge |
| price_bucket | price_30k_70k | no_clear_edge | -0.2729 | - | 16 | 0.1875 | True | - | candidate_weight_source |
| price_bucket | price_gte_70k | prefer_exit | -0.5251 | 1.7017 | 11 | 0.3636 | False | pyramid_wait | candidate_weight_source |
| price_bucket | price_lt_10k | no_clear_edge | -0.4961 | - | 23 | 0.3478 | False | pyramid_wait | candidate_weight_source |
| volume_bucket | volume_2m_10m | prefer_exit | -0.5653 | 1.6323 | 10 | 0.1 | False | pyramid_wait | candidate_weight_source |
| volume_bucket | volume_500k_2m | no_clear_edge | -0.4805 | - | 15 | 0.3333 | True | - | candidate_weight_source |
| volume_bucket | volume_gte_10m | no_clear_edge | -1.9345 | - | 8 | 0.5 | False | pyramid_wait | candidate_weight_source |
| volume_bucket | volume_lt_500k | prefer_exit | -0.5622 | 0.6986 | 36 | 0.3889 | False | pyramid_wait | candidate_weight_source |
| volume_bucket | volume_unknown | no_clear_edge | -1.9107 | - | 10 | 0.5 | False | pyramid_wait | candidate_weight_source |
| time_bucket | time_0900_0930 | no_clear_edge | - | - | - | - | False | pyramid_wait | insufficient_sample |
| time_bucket | time_0930_1030 | no_clear_edge | -0.3537 | - | 7 | 0.2857 | False | avg_down_wait,pyramid_wait | candidate_weight_source |
| time_bucket | time_1030_1400 | no_clear_edge | -1.2844 | - | 23 | 0.3913 | True | - | candidate_weight_source |
| time_bucket | time_1400_1530 | no_clear_edge | -0.2056 | - | 11 | 0.1818 | False | avg_down_wait,pyramid_wait | candidate_weight_source |
| time_bucket | time_outside_regular | prefer_exit | -0.6913 | 0.8261 | 36 | 0.4167 | False | pyramid_wait | candidate_weight_source |

## Prompt Hints

- `price_bucket=price_10k_30k` / `no_clear_edge`: price_bucket=price_10k_30k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `price_bucket=price_30k_70k` / `no_clear_edge`: price_bucket=price_30k_70k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `price_bucket=price_gte_70k` / `prefer_exit`: price_bucket=price_gte_70k 과거 표본은 보유/추가매수보다 청산 우위가 있다. 단 hard veto와 현재 thesis를 먼저 확인한다.
- `price_bucket=price_lt_10k` / `no_clear_edge`: price_bucket=price_lt_10k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_2m_10m` / `prefer_exit`: volume_bucket=volume_2m_10m 과거 표본은 보유/추가매수보다 청산 우위가 있다. 단 hard veto와 현재 thesis를 먼저 확인한다.
- `volume_bucket=volume_500k_2m` / `no_clear_edge`: volume_bucket=volume_500k_2m 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_gte_10m` / `no_clear_edge`: volume_bucket=volume_gte_10m 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_lt_500k` / `prefer_exit`: volume_bucket=volume_lt_500k 과거 표본은 보유/추가매수보다 청산 우위가 있다. 단 hard veto와 현재 thesis를 먼저 확인한다.
- `volume_bucket=volume_unknown` / `no_clear_edge`: volume_bucket=volume_unknown 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_0900_0930` / `no_clear_edge`: time_bucket=time_0900_0930 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_0930_1030` / `no_clear_edge`: time_bucket=time_0930_1030 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_1030_1400` / `no_clear_edge`: time_bucket=time_1030_1400 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_1400_1530` / `no_clear_edge`: time_bucket=time_1400_1530 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_outside_regular` / `prefer_exit`: time_bucket=time_outside_regular 과거 표본은 보유/추가매수보다 청산 우위가 있다. 단 hard veto와 현재 thesis를 먼저 확인한다.

## 다음 액션

- `ADM`은 shadow가 아니라 advisory canary/live-readiness 축으로 관리한다.
- `recommended_bias != no_clear_edge`이고 `policy_hint=candidate_weight_source`인 bucket만 다음 bounded canary 후보로 본다.
- all `no_clear_edge`이면 perfect spot 대기가 아니라 최소 edge 부재로 판정하고 live AI 응답을 바꾸지 않는다.
