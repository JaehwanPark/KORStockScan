# Latency Classifier Recommendation 2026-06-05

- latency_block_count: 24790
- unique_codes: 18
- selected_profile_id: grid_age158_jitter260_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 810, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age158_jitter260_spread0050 | reject | 158 | 260 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter260_spread0075 | reject | 158 | 260 | 0.0075 | 0 | 468 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter260_spread0084 | reject | 158 | 260 | 0.0084 | 0 | 750 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter260_spread0085 | reject | 158 | 260 | 0.0085 | 0 | 759 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter260_spread0089 | reject | 158 | 260 | 0.0089 | 0 | 1290 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter260_spread0100 | reject | 158 | 260 | 0.0100 | 0 | 1959 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter260_spread0101 | reject | 158 | 260 | 0.0101 | 0 | 2122 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter260_spread0111 | reject | 158 | 260 | 0.0111 | 0 | 2416 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter260_spread0120 | reject | 158 | 260 | 0.0120 | 0 | 2427 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter300_spread0050 | reject | 158 | 300 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter300_spread0075 | reject | 158 | 300 | 0.0075 | 0 | 470 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter300_spread0084 | reject | 158 | 300 | 0.0084 | 0 | 753 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter300_spread0085 | reject | 158 | 300 | 0.0085 | 0 | 762 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter300_spread0089 | reject | 158 | 300 | 0.0089 | 0 | 1296 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter300_spread0100 | reject | 158 | 300 | 0.0100 | 0 | 1969 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter300_spread0101 | reject | 158 | 300 | 0.0101 | 0 | 2132 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter300_spread0111 | reject | 158 | 300 | 0.0111 | 0 | 2426 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter300_spread0120 | reject | 158 | 300 | 0.0120 | 0 | 2437 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter450_spread0050 | reject | 158 | 450 | 0.0050 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter450_spread0075 | reject | 158 | 450 | 0.0075 | 0 | 484 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter450_spread0084 | reject | 158 | 450 | 0.0084 | 0 | 775 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter450_spread0085 | reject | 158 | 450 | 0.0085 | 0 | 784 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter450_spread0089 | reject | 158 | 450 | 0.0089 | 0 | 1347 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter450_spread0100 | reject | 158 | 450 | 0.0100 | 0 | 2038 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter450_spread0101 | reject | 158 | 450 | 0.0101 | 0 | 2203 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter450_spread0111 | reject | 158 | 450 | 0.0111 | 0 | 2505 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter450_spread0120 | reject | 158 | 450 | 0.0120 | 0 | 2517 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter500_spread0050 | reject | 158 | 500 | 0.0050 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter500_spread0075 | reject | 158 | 500 | 0.0075 | 0 | 485 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age158_jitter500_spread0084 | reject | 158 | 500 | 0.0084 | 0 | 777 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 158, "max_ws_jitter_ms_for_caution": 260, "max_spread_ratio_for_caution": 0.005, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 158, "recovery_max_ws_jitter_ms": 260, "recovery_max_spread_ratio": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
