# Latency Classifier Recommendation 2026-06-09

- latency_block_count: 14045
- unique_codes: 75
- selected_profile_id: grid_age200_jitter213_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 810, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age200_jitter213_spread0050 | reject | 200 | 213 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter213_spread0075 | reject | 200 | 213 | 0.0075 | 0 | 186 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter213_spread0085 | reject | 200 | 213 | 0.0085 | 0 | 273 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter213_spread0096 | reject | 200 | 213 | 0.0096 | 0 | 356 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter213_spread0100 | reject | 200 | 213 | 0.0100 | 0 | 669 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter213_spread0102 | reject | 200 | 213 | 0.0102 | 0 | 692 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter213_spread0104 | reject | 200 | 213 | 0.0104 | 0 | 822 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter213_spread0115 | reject | 200 | 213 | 0.0115 | 0 | 1002 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter213_spread0120 | reject | 200 | 213 | 0.0120 | 0 | 1066 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter300_spread0050 | reject | 200 | 300 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter300_spread0075 | reject | 200 | 300 | 0.0075 | 0 | 187 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter300_spread0085 | reject | 200 | 300 | 0.0085 | 0 | 275 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter300_spread0096 | reject | 200 | 300 | 0.0096 | 0 | 359 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter300_spread0100 | reject | 200 | 300 | 0.0100 | 0 | 673 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter300_spread0102 | reject | 200 | 300 | 0.0102 | 0 | 697 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter300_spread0104 | reject | 200 | 300 | 0.0104 | 0 | 828 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter300_spread0115 | reject | 200 | 300 | 0.0115 | 0 | 1009 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter300_spread0120 | reject | 200 | 300 | 0.0120 | 0 | 1074 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter410_spread0050 | reject | 200 | 410 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter410_spread0075 | reject | 200 | 410 | 0.0075 | 0 | 189 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter410_spread0085 | reject | 200 | 410 | 0.0085 | 0 | 279 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter410_spread0096 | reject | 200 | 410 | 0.0096 | 0 | 364 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter410_spread0100 | reject | 200 | 410 | 0.0100 | 0 | 679 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter410_spread0102 | reject | 200 | 410 | 0.0102 | 0 | 705 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter410_spread0104 | reject | 200 | 410 | 0.0104 | 0 | 837 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter410_spread0115 | reject | 200 | 410 | 0.0115 | 0 | 1019 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter410_spread0120 | reject | 200 | 410 | 0.0120 | 0 | 1085 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter450_spread0050 | reject | 200 | 450 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter450_spread0075 | reject | 200 | 450 | 0.0075 | 0 | 189 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter450_spread0085 | reject | 200 | 450 | 0.0085 | 0 | 279 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 200, "max_ws_jitter_ms_for_caution": 213, "max_spread_ratio_for_caution": 0.005, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 200, "recovery_max_ws_jitter_ms": 213, "recovery_max_spread_ratio": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
