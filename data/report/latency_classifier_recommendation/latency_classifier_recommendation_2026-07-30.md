# Latency Classifier Recommendation 2026-07-30

- latency_block_count: 7
- unique_codes: 2
- selected_profile_id: grid_age200_jitter90_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 540, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age200_jitter90_spread0050 | reject | 200 | 90 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter90_spread0067 | reject | 200 | 90 | 0.0067 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter90_spread0074 | reject | 200 | 90 | 0.0074 | 0 | 1 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter90_spread0074 | reject | 200 | 90 | 0.0074 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter90_spread0075 | reject | 200 | 90 | 0.0075 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter90_spread0085 | reject | 200 | 90 | 0.0085 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter90_spread0087 | reject | 200 | 90 | 0.0087 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter90_spread0096 | reject | 200 | 90 | 0.0096 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter90_spread0100 | reject | 200 | 90 | 0.0100 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter90_spread0120 | reject | 200 | 90 | 0.0120 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter300_spread0050 | reject | 200 | 300 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter300_spread0067 | reject | 200 | 300 | 0.0067 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter300_spread0074 | reject | 200 | 300 | 0.0074 | 0 | 1 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter300_spread0074 | reject | 200 | 300 | 0.0074 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter300_spread0075 | reject | 200 | 300 | 0.0075 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter300_spread0085 | reject | 200 | 300 | 0.0085 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter300_spread0087 | reject | 200 | 300 | 0.0087 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter300_spread0096 | reject | 200 | 300 | 0.0096 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter300_spread0100 | reject | 200 | 300 | 0.0100 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter300_spread0120 | reject | 200 | 300 | 0.0120 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter450_spread0050 | reject | 200 | 450 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter450_spread0067 | reject | 200 | 450 | 0.0067 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter450_spread0074 | reject | 200 | 450 | 0.0074 | 0 | 1 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter450_spread0074 | reject | 200 | 450 | 0.0074 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter450_spread0075 | reject | 200 | 450 | 0.0075 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter450_spread0085 | reject | 200 | 450 | 0.0085 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter450_spread0087 | reject | 200 | 450 | 0.0087 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter450_spread0096 | reject | 200 | 450 | 0.0096 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter450_spread0100 | reject | 200 | 450 | 0.0100 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age200_jitter450_spread0120 | reject | 200 | 450 | 0.0120 | 0 | 2 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 200, "max_ws_jitter_ms_for_caution": 90, "max_spread_ratio_for_caution": 0.005, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 200, "recovery_max_ws_jitter_ms": 90, "recovery_max_spread_ratio": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
