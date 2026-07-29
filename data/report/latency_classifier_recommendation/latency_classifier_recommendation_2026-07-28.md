# Latency Classifier Recommendation 2026-07-28

- latency_block_count: 31
- unique_codes: 16
- selected_profile_id: grid_age25_jitter300_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 450, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age25_jitter300_spread0050 | reject | 25 | 300 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter300_spread0056 | reject | 25 | 300 | 0.0056 | 0 | 3 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter300_spread0066 | reject | 25 | 300 | 0.0066 | 0 | 5 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter300_spread0075 | reject | 25 | 300 | 0.0075 | 0 | 6 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter300_spread0082 | reject | 25 | 300 | 0.0082 | 0 | 6 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter300_spread0085 | reject | 25 | 300 | 0.0085 | 0 | 6 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter300_spread0099 | reject | 25 | 300 | 0.0099 | 0 | 7 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter300_spread0100 | reject | 25 | 300 | 0.0100 | 0 | 7 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter300_spread0116 | reject | 25 | 300 | 0.0116 | 0 | 7 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter300_spread0120 | reject | 25 | 300 | 0.0120 | 0 | 7 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter450_spread0050 | reject | 25 | 450 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter450_spread0056 | reject | 25 | 450 | 0.0056 | 0 | 3 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter450_spread0066 | reject | 25 | 450 | 0.0066 | 0 | 5 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter450_spread0075 | reject | 25 | 450 | 0.0075 | 0 | 6 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter450_spread0082 | reject | 25 | 450 | 0.0082 | 0 | 6 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter450_spread0085 | reject | 25 | 450 | 0.0085 | 0 | 6 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter450_spread0099 | reject | 25 | 450 | 0.0099 | 0 | 7 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter450_spread0100 | reject | 25 | 450 | 0.0100 | 0 | 7 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter450_spread0116 | reject | 25 | 450 | 0.0116 | 0 | 7 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter450_spread0120 | reject | 25 | 450 | 0.0120 | 0 | 7 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter500_spread0050 | reject | 25 | 500 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter500_spread0056 | reject | 25 | 500 | 0.0056 | 0 | 3 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter500_spread0066 | reject | 25 | 500 | 0.0066 | 0 | 5 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter500_spread0075 | reject | 25 | 500 | 0.0075 | 0 | 6 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter500_spread0082 | reject | 25 | 500 | 0.0082 | 0 | 6 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter500_spread0085 | reject | 25 | 500 | 0.0085 | 0 | 6 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter500_spread0099 | reject | 25 | 500 | 0.0099 | 0 | 7 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter500_spread0100 | reject | 25 | 500 | 0.0100 | 0 | 7 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter500_spread0116 | reject | 25 | 500 | 0.0116 | 0 | 7 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age25_jitter500_spread0120 | reject | 25 | 500 | 0.0120 | 0 | 7 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 25, "max_ws_jitter_ms_for_caution": 300, "max_spread_ratio_for_caution": 0.005, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 25, "recovery_max_ws_jitter_ms": 300, "recovery_max_spread_ratio": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
