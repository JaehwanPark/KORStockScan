# Latency Classifier Recommendation 2026-05-27

- latency_block_count: 36801
- unique_codes: 68
- selected_profile_id: grid_age167_jitter109_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 810, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age167_jitter109_spread0050 | reject | 167 | 109 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter109_spread0069 | reject | 167 | 109 | 0.0069 | 0 | 1078 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter109_spread0075 | reject | 167 | 109 | 0.0075 | 0 | 1297 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter109_spread0085 | reject | 167 | 109 | 0.0085 | 0 | 1596 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter109_spread0092 | reject | 167 | 109 | 0.0092 | 0 | 2498 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter109_spread0094 | reject | 167 | 109 | 0.0094 | 0 | 3692 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter109_spread0100 | reject | 167 | 109 | 0.0100 | 0 | 4014 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter109_spread0112 | reject | 167 | 109 | 0.0112 | 0 | 4225 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter109_spread0120 | reject | 167 | 109 | 0.0120 | 0 | 4320 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter207_spread0050 | reject | 167 | 207 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter207_spread0069 | reject | 167 | 207 | 0.0069 | 0 | 1081 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter207_spread0075 | reject | 167 | 207 | 0.0075 | 0 | 1302 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter207_spread0085 | reject | 167 | 207 | 0.0085 | 0 | 1603 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter207_spread0092 | reject | 167 | 207 | 0.0092 | 0 | 2534 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter207_spread0094 | reject | 167 | 207 | 0.0094 | 0 | 3739 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter207_spread0100 | reject | 167 | 207 | 0.0100 | 0 | 4067 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter207_spread0112 | reject | 167 | 207 | 0.0112 | 0 | 4279 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter207_spread0120 | reject | 167 | 207 | 0.0120 | 0 | 4374 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter300_spread0050 | reject | 167 | 300 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter300_spread0069 | reject | 167 | 300 | 0.0069 | 0 | 1081 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter300_spread0075 | reject | 167 | 300 | 0.0075 | 0 | 1302 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter300_spread0085 | reject | 167 | 300 | 0.0085 | 0 | 1603 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter300_spread0092 | reject | 167 | 300 | 0.0092 | 0 | 2546 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter300_spread0094 | reject | 167 | 300 | 0.0094 | 0 | 3762 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter300_spread0100 | reject | 167 | 300 | 0.0100 | 0 | 4107 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter300_spread0112 | reject | 167 | 300 | 0.0112 | 0 | 4319 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter300_spread0120 | reject | 167 | 300 | 0.0120 | 0 | 4414 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter398_spread0050 | reject | 167 | 398 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter398_spread0069 | reject | 167 | 398 | 0.0069 | 0 | 1081 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter398_spread0075 | reject | 167 | 398 | 0.0075 | 0 | 1302 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 167, "max_ws_jitter_ms_for_caution": 109, "max_spread_ratio_for_caution": 0.005, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 167, "recovery_max_ws_jitter_ms": 109, "recovery_max_spread_ratio": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
