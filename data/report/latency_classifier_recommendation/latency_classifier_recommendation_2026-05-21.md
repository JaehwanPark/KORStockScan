# Latency Classifier Recommendation 2026-05-21

- latency_block_count: 332
- unique_codes: 13
- selected_profile_id: grid_age170_jitter203_spread0040
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 900, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_reject | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age170_jitter203_spread0040 | reject | 170 | 203 | 0.0040 | 0 | 4 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter203_spread0047 | reject | 170 | 203 | 0.0047 | 0 | 19 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter203_spread0050 | reject | 170 | 203 | 0.0050 | 0 | 20 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter203_spread0072 | reject | 170 | 203 | 0.0072 | 0 | 31 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter203_spread0075 | reject | 170 | 203 | 0.0075 | 0 | 31 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter203_spread0085 | reject | 170 | 203 | 0.0085 | 0 | 34 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter203_spread0093 | reject | 170 | 203 | 0.0093 | 0 | 37 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter203_spread0100 | reject | 170 | 203 | 0.0100 | 0 | 38 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter203_spread0113 | reject | 170 | 203 | 0.0113 | 0 | 38 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter203_spread0120 | reject | 170 | 203 | 0.0120 | 0 | 39 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter300_spread0040 | reject | 170 | 300 | 0.0040 | 0 | 4 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter300_spread0047 | reject | 170 | 300 | 0.0047 | 0 | 19 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter300_spread0050 | reject | 170 | 300 | 0.0050 | 0 | 20 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter300_spread0072 | reject | 170 | 300 | 0.0072 | 0 | 31 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter300_spread0075 | reject | 170 | 300 | 0.0075 | 0 | 31 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter300_spread0085 | reject | 170 | 300 | 0.0085 | 0 | 34 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter300_spread0093 | reject | 170 | 300 | 0.0093 | 0 | 37 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter300_spread0100 | reject | 170 | 300 | 0.0100 | 0 | 38 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter300_spread0113 | reject | 170 | 300 | 0.0113 | 0 | 38 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter300_spread0120 | reject | 170 | 300 | 0.0120 | 0 | 39 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter409_spread0040 | reject | 170 | 409 | 0.0040 | 0 | 4 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter409_spread0047 | reject | 170 | 409 | 0.0047 | 0 | 21 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter409_spread0050 | reject | 170 | 409 | 0.0050 | 0 | 22 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter409_spread0072 | reject | 170 | 409 | 0.0072 | 0 | 33 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter409_spread0075 | reject | 170 | 409 | 0.0075 | 0 | 33 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter409_spread0085 | reject | 170 | 409 | 0.0085 | 0 | 36 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter409_spread0093 | reject | 170 | 409 | 0.0093 | 0 | 39 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter409_spread0100 | reject | 170 | 409 | 0.0100 | 0 | 40 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter409_spread0113 | reject | 170 | 409 | 0.0113 | 0 | 40 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age170_jitter409_spread0120 | reject | 170 | 409 | 0.0120 | 0 | 41 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold_sample
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 170, "max_ws_jitter_ms_for_caution": 203, "max_spread_ratio_for_caution": 0.00401, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 170, "recovery_max_ws_jitter_ms": 203, "recovery_max_spread_ratio": 0.00401}`
- reason: recommended_action=reject; recovery_count=0 below floor=33; latency_blocks=332 recovery_count=0 floor=33 quote_stale_override=0 broker_guard_bypass=0
