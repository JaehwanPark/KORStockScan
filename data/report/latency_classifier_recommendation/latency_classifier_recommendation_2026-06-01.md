# Latency Classifier Recommendation 2026-06-01

- latency_block_count: 25222
- unique_codes: 74
- selected_profile_id: grid_age191_jitter200_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 900, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age191_jitter200_spread0050 | reject | 191 | 200 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter200_spread0072 | reject | 191 | 200 | 0.0072 | 0 | 1038 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter200_spread0075 | reject | 191 | 200 | 0.0075 | 0 | 1395 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter200_spread0080 | reject | 191 | 200 | 0.0080 | 0 | 1848 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter200_spread0085 | reject | 191 | 200 | 0.0085 | 0 | 2568 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter200_spread0088 | reject | 191 | 200 | 0.0088 | 0 | 2654 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter200_spread0099 | reject | 191 | 200 | 0.0099 | 0 | 3174 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter200_spread0100 | reject | 191 | 200 | 0.0100 | 0 | 3194 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter200_spread0112 | reject | 191 | 200 | 0.0112 | 0 | 3308 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter200_spread0120 | reject | 191 | 200 | 0.0120 | 0 | 3380 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0050 | reject | 191 | 300 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0072 | reject | 191 | 300 | 0.0072 | 0 | 1045 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0075 | reject | 191 | 300 | 0.0075 | 0 | 1407 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0080 | reject | 191 | 300 | 0.0080 | 0 | 1863 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0085 | reject | 191 | 300 | 0.0085 | 0 | 2593 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0088 | reject | 191 | 300 | 0.0088 | 0 | 2681 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0099 | reject | 191 | 300 | 0.0099 | 0 | 3211 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0100 | reject | 191 | 300 | 0.0100 | 0 | 3233 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0112 | reject | 191 | 300 | 0.0112 | 0 | 3348 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0120 | reject | 191 | 300 | 0.0120 | 0 | 3420 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter403_spread0050 | reject | 191 | 403 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter403_spread0072 | reject | 191 | 403 | 0.0072 | 0 | 1049 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter403_spread0075 | reject | 191 | 403 | 0.0075 | 0 | 1414 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter403_spread0080 | reject | 191 | 403 | 0.0080 | 0 | 1871 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter403_spread0085 | reject | 191 | 403 | 0.0085 | 0 | 2612 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter403_spread0088 | reject | 191 | 403 | 0.0088 | 0 | 2700 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter403_spread0099 | reject | 191 | 403 | 0.0099 | 0 | 3236 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter403_spread0100 | reject | 191 | 403 | 0.0100 | 0 | 3259 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter403_spread0112 | reject | 191 | 403 | 0.0112 | 0 | 3379 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter403_spread0120 | reject | 191 | 403 | 0.0120 | 0 | 3451 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 191, "max_ws_jitter_ms_for_caution": 200, "max_spread_ratio_for_caution": 0.005, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 191, "recovery_max_ws_jitter_ms": 200, "recovery_max_spread_ratio": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
