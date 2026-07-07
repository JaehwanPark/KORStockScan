# Latency Classifier Recommendation 2026-07-07

- latency_block_count: 332
- unique_codes: 17
- selected_profile_id: grid_age40_jitter300_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 450, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age40_jitter300_spread0050 | reject | 40 | 300 | 0.0050 | 4 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter300_spread0057 | reject | 40 | 300 | 0.0057 | 4 | 18 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter300_spread0075 | reject | 40 | 300 | 0.0075 | 4 | 40 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter300_spread0079 | reject | 40 | 300 | 0.0079 | 4 | 42 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter300_spread0085 | reject | 40 | 300 | 0.0085 | 4 | 49 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter300_spread0098 | reject | 40 | 300 | 0.0098 | 4 | 71 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter300_spread0100 | reject | 40 | 300 | 0.0100 | 4 | 80 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter300_spread0109 | reject | 40 | 300 | 0.0109 | 4 | 81 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter300_spread0118 | reject | 40 | 300 | 0.0118 | 4 | 82 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter300_spread0120 | reject | 40 | 300 | 0.0120 | 4 | 83 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter450_spread0050 | reject | 40 | 450 | 0.0050 | 4 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter450_spread0057 | reject | 40 | 450 | 0.0057 | 4 | 18 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter450_spread0075 | reject | 40 | 450 | 0.0075 | 4 | 40 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter450_spread0079 | reject | 40 | 450 | 0.0079 | 4 | 42 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter450_spread0085 | reject | 40 | 450 | 0.0085 | 4 | 49 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter450_spread0098 | reject | 40 | 450 | 0.0098 | 4 | 71 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter450_spread0100 | reject | 40 | 450 | 0.0100 | 4 | 80 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter450_spread0109 | reject | 40 | 450 | 0.0109 | 4 | 81 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter450_spread0118 | reject | 40 | 450 | 0.0118 | 4 | 82 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter450_spread0120 | reject | 40 | 450 | 0.0120 | 4 | 83 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter500_spread0050 | reject | 40 | 500 | 0.0050 | 4 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter500_spread0057 | reject | 40 | 500 | 0.0057 | 4 | 18 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter500_spread0075 | reject | 40 | 500 | 0.0075 | 4 | 40 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter500_spread0079 | reject | 40 | 500 | 0.0079 | 4 | 42 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter500_spread0085 | reject | 40 | 500 | 0.0085 | 4 | 49 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter500_spread0098 | reject | 40 | 500 | 0.0098 | 4 | 71 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter500_spread0100 | reject | 40 | 500 | 0.0100 | 4 | 80 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter500_spread0109 | reject | 40 | 500 | 0.0109 | 4 | 81 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter500_spread0118 | reject | 40 | 500 | 0.0118 | 4 | 82 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age40_jitter500_spread0120 | reject | 40 | 500 | 0.0120 | 4 | 83 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 40, "max_ws_jitter_ms_for_caution": 300, "max_spread_ratio_for_caution": 0.005, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 40, "recovery_max_ws_jitter_ms": 300, "recovery_max_spread_ratio": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
