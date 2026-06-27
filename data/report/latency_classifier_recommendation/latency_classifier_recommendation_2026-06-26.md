# Latency Classifier Recommendation 2026-06-26

- latency_block_count: 35
- unique_codes: 23
- selected_profile_id: grid_age46_jitter300_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 810, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age46_jitter300_spread0050 | reject | 46 | 300 | 0.0050 | 1 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter300_spread0055 | reject | 46 | 300 | 0.0055 | 1 | 1 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter300_spread0070 | reject | 46 | 300 | 0.0070 | 1 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter300_spread0075 | reject | 46 | 300 | 0.0075 | 1 | 3 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter300_spread0080 | reject | 46 | 300 | 0.0080 | 1 | 5 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter300_spread0085 | reject | 46 | 300 | 0.0085 | 1 | 5 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter300_spread0100 | reject | 46 | 300 | 0.0100 | 1 | 5 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter300_spread0110 | reject | 46 | 300 | 0.0110 | 1 | 6 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter300_spread0120 | reject | 46 | 300 | 0.0120 | 1 | 6 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter450_spread0050 | reject | 46 | 450 | 0.0050 | 1 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter450_spread0055 | reject | 46 | 450 | 0.0055 | 1 | 1 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter450_spread0070 | reject | 46 | 450 | 0.0070 | 1 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter450_spread0075 | reject | 46 | 450 | 0.0075 | 1 | 3 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter450_spread0080 | reject | 46 | 450 | 0.0080 | 1 | 5 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter450_spread0085 | reject | 46 | 450 | 0.0085 | 1 | 5 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter450_spread0100 | reject | 46 | 450 | 0.0100 | 1 | 5 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter450_spread0110 | reject | 46 | 450 | 0.0110 | 1 | 6 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter450_spread0120 | reject | 46 | 450 | 0.0120 | 1 | 6 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter500_spread0050 | reject | 46 | 500 | 0.0050 | 1 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter500_spread0055 | reject | 46 | 500 | 0.0055 | 1 | 1 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter500_spread0070 | reject | 46 | 500 | 0.0070 | 1 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter500_spread0075 | reject | 46 | 500 | 0.0075 | 1 | 3 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter500_spread0080 | reject | 46 | 500 | 0.0080 | 1 | 5 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter500_spread0085 | reject | 46 | 500 | 0.0085 | 1 | 5 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter500_spread0100 | reject | 46 | 500 | 0.0100 | 1 | 5 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter500_spread0110 | reject | 46 | 500 | 0.0110 | 1 | 6 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter500_spread0120 | reject | 46 | 500 | 0.0120 | 1 | 6 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter937_spread0050 | reject | 46 | 937 | 0.0050 | 1 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter937_spread0055 | reject | 46 | 937 | 0.0055 | 1 | 1 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age46_jitter937_spread0070 | reject | 46 | 937 | 0.0070 | 1 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 46, "max_ws_jitter_ms_for_caution": 300, "max_spread_ratio_for_caution": 0.005, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 46, "recovery_max_ws_jitter_ms": 300, "recovery_max_spread_ratio": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
