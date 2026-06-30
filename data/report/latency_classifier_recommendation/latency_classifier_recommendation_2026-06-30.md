# Latency Classifier Recommendation 2026-06-30

- latency_block_count: 914
- unique_codes: 22
- selected_profile_id: grid_age51_jitter300_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 450, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age51_jitter300_spread0050 | reject | 51 | 300 | 0.0050 | 1 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter300_spread0075 | reject | 51 | 300 | 0.0075 | 1 | 17 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter300_spread0085 | reject | 51 | 300 | 0.0085 | 1 | 32 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter300_spread0087 | reject | 51 | 300 | 0.0087 | 1 | 37 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter300_spread0100 | reject | 51 | 300 | 0.0100 | 1 | 70 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter300_spread0104 | reject | 51 | 300 | 0.0104 | 1 | 75 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter300_spread0109 | reject | 51 | 300 | 0.0109 | 1 | 126 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter300_spread0112 | reject | 51 | 300 | 0.0112 | 1 | 158 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter300_spread0113 | reject | 51 | 300 | 0.0113 | 1 | 162 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter300_spread0120 | reject | 51 | 300 | 0.0120 | 1 | 163 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter450_spread0050 | reject | 51 | 450 | 0.0050 | 1 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter450_spread0075 | reject | 51 | 450 | 0.0075 | 1 | 17 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter450_spread0085 | reject | 51 | 450 | 0.0085 | 1 | 32 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter450_spread0087 | reject | 51 | 450 | 0.0087 | 1 | 37 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter450_spread0100 | reject | 51 | 450 | 0.0100 | 1 | 70 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter450_spread0104 | reject | 51 | 450 | 0.0104 | 1 | 75 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter450_spread0109 | reject | 51 | 450 | 0.0109 | 1 | 126 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter450_spread0112 | reject | 51 | 450 | 0.0112 | 1 | 158 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter450_spread0113 | reject | 51 | 450 | 0.0113 | 1 | 162 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter450_spread0120 | reject | 51 | 450 | 0.0120 | 1 | 163 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter500_spread0050 | reject | 51 | 500 | 0.0050 | 1 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter500_spread0075 | reject | 51 | 500 | 0.0075 | 1 | 17 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter500_spread0085 | reject | 51 | 500 | 0.0085 | 1 | 32 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter500_spread0087 | reject | 51 | 500 | 0.0087 | 1 | 37 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter500_spread0100 | reject | 51 | 500 | 0.0100 | 1 | 70 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter500_spread0104 | reject | 51 | 500 | 0.0104 | 1 | 75 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter500_spread0109 | reject | 51 | 500 | 0.0109 | 1 | 126 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter500_spread0112 | reject | 51 | 500 | 0.0112 | 1 | 158 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter500_spread0113 | reject | 51 | 500 | 0.0113 | 1 | 162 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age51_jitter500_spread0120 | reject | 51 | 500 | 0.0120 | 1 | 163 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 51, "max_ws_jitter_ms_for_caution": 300, "max_spread_ratio_for_caution": 0.005, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 51, "recovery_max_ws_jitter_ms": 300, "recovery_max_spread_ratio": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
