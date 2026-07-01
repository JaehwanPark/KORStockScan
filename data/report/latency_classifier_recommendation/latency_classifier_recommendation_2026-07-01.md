# Latency Classifier Recommendation 2026-07-01

- latency_block_count: 884
- unique_codes: 25
- selected_profile_id: grid_age60_jitter300_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 405, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age60_jitter300_spread0050 | reject | 60 | 300 | 0.0050 | 3 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter300_spread0075 | reject | 60 | 300 | 0.0075 | 3 | 21 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter300_spread0083 | reject | 60 | 300 | 0.0083 | 3 | 26 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter300_spread0085 | reject | 60 | 300 | 0.0085 | 3 | 52 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter300_spread0087 | reject | 60 | 300 | 0.0087 | 3 | 67 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter300_spread0096 | reject | 60 | 300 | 0.0096 | 3 | 116 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter300_spread0100 | reject | 60 | 300 | 0.0100 | 3 | 130 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter300_spread0110 | reject | 60 | 300 | 0.0110 | 3 | 138 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter300_spread0120 | reject | 60 | 300 | 0.0120 | 3 | 144 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter450_spread0050 | reject | 60 | 450 | 0.0050 | 3 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter450_spread0075 | reject | 60 | 450 | 0.0075 | 3 | 21 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter450_spread0083 | reject | 60 | 450 | 0.0083 | 3 | 26 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter450_spread0085 | reject | 60 | 450 | 0.0085 | 3 | 52 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter450_spread0087 | reject | 60 | 450 | 0.0087 | 3 | 67 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter450_spread0096 | reject | 60 | 450 | 0.0096 | 3 | 116 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter450_spread0100 | reject | 60 | 450 | 0.0100 | 3 | 130 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter450_spread0110 | reject | 60 | 450 | 0.0110 | 3 | 138 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter450_spread0120 | reject | 60 | 450 | 0.0120 | 3 | 144 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter500_spread0050 | reject | 60 | 500 | 0.0050 | 3 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter500_spread0075 | reject | 60 | 500 | 0.0075 | 3 | 21 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter500_spread0083 | reject | 60 | 500 | 0.0083 | 3 | 26 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter500_spread0085 | reject | 60 | 500 | 0.0085 | 3 | 52 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter500_spread0087 | reject | 60 | 500 | 0.0087 | 3 | 67 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter500_spread0096 | reject | 60 | 500 | 0.0096 | 3 | 116 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter500_spread0100 | reject | 60 | 500 | 0.0100 | 3 | 130 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter500_spread0110 | reject | 60 | 500 | 0.0110 | 3 | 138 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter500_spread0120 | reject | 60 | 500 | 0.0120 | 3 | 144 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter1000_spread0050 | reject | 60 | 1000 | 0.0050 | 3 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter1000_spread0075 | reject | 60 | 1000 | 0.0075 | 3 | 21 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age60_jitter1000_spread0083 | reject | 60 | 1000 | 0.0083 | 3 | 26 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 60, "max_ws_jitter_ms_for_caution": 300, "max_spread_ratio_for_caution": 0.005, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 60, "recovery_max_ws_jitter_ms": 300, "recovery_max_spread_ratio": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
