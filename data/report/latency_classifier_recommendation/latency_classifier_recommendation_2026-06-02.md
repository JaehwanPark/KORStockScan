# Latency Classifier Recommendation 2026-06-02

- latency_block_count: 27298
- unique_codes: 75
- selected_profile_id: grid_age191_jitter234_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 900, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age191_jitter234_spread0050 | reject | 191 | 234 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter234_spread0061 | reject | 191 | 234 | 0.0061 | 0 | 1064 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter234_spread0073 | reject | 191 | 234 | 0.0073 | 0 | 1953 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter234_spread0075 | reject | 191 | 234 | 0.0075 | 0 | 2102 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter234_spread0085 | reject | 191 | 234 | 0.0085 | 0 | 2153 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter234_spread0088 | reject | 191 | 234 | 0.0088 | 0 | 2831 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter234_spread0099 | reject | 191 | 234 | 0.0099 | 0 | 3338 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter234_spread0100 | reject | 191 | 234 | 0.0100 | 0 | 3401 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter234_spread0102 | reject | 191 | 234 | 0.0102 | 0 | 3410 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter234_spread0120 | reject | 191 | 234 | 0.0120 | 0 | 3524 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0050 | reject | 191 | 300 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0061 | reject | 191 | 300 | 0.0061 | 0 | 1068 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0073 | reject | 191 | 300 | 0.0073 | 0 | 1961 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0075 | reject | 191 | 300 | 0.0075 | 0 | 2110 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0085 | reject | 191 | 300 | 0.0085 | 0 | 2161 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0088 | reject | 191 | 300 | 0.0088 | 0 | 2842 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0099 | reject | 191 | 300 | 0.0099 | 0 | 3352 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0100 | reject | 191 | 300 | 0.0100 | 0 | 3416 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0102 | reject | 191 | 300 | 0.0102 | 0 | 3425 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter300_spread0120 | reject | 191 | 300 | 0.0120 | 0 | 3539 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter450_spread0050 | reject | 191 | 450 | 0.0050 | 0 | 5 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter450_spread0061 | reject | 191 | 450 | 0.0061 | 0 | 1092 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter450_spread0073 | reject | 191 | 450 | 0.0073 | 0 | 1994 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter450_spread0075 | reject | 191 | 450 | 0.0075 | 0 | 2143 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter450_spread0085 | reject | 191 | 450 | 0.0085 | 0 | 2194 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter450_spread0088 | reject | 191 | 450 | 0.0088 | 0 | 2884 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter450_spread0099 | reject | 191 | 450 | 0.0099 | 0 | 3397 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter450_spread0100 | reject | 191 | 450 | 0.0100 | 0 | 3462 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter450_spread0102 | reject | 191 | 450 | 0.0102 | 0 | 3471 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age191_jitter450_spread0120 | reject | 191 | 450 | 0.0120 | 0 | 3586 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 191, "max_ws_jitter_ms_for_caution": 234, "max_spread_ratio_for_caution": 0.005, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 191, "recovery_max_ws_jitter_ms": 234, "recovery_max_spread_ratio": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
