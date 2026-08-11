# Latency Classifier Recommendation 2026-08-11

- latency_block_count: 114
- unique_codes: 45
- selected_profile_id: grid_age97_jitter300_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 315, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age97_jitter300_spread0050 | reject | 97 | 300 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter300_spread0075 | reject | 97 | 300 | 0.0075 | 0 | 8 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter300_spread0077 | reject | 97 | 300 | 0.0077 | 0 | 10 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter300_spread0085 | reject | 97 | 300 | 0.0085 | 0 | 17 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter300_spread0100 | reject | 97 | 300 | 0.0100 | 0 | 17 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter300_spread0106 | reject | 97 | 300 | 0.0106 | 0 | 19 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter300_spread0120 | reject | 97 | 300 | 0.0120 | 0 | 24 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter450_spread0050 | reject | 97 | 450 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter450_spread0075 | reject | 97 | 450 | 0.0075 | 0 | 8 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter450_spread0077 | reject | 97 | 450 | 0.0077 | 0 | 10 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter450_spread0085 | reject | 97 | 450 | 0.0085 | 0 | 17 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter450_spread0100 | reject | 97 | 450 | 0.0100 | 0 | 17 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter450_spread0106 | reject | 97 | 450 | 0.0106 | 0 | 19 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter450_spread0120 | reject | 97 | 450 | 0.0120 | 0 | 24 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter500_spread0050 | reject | 97 | 500 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter500_spread0075 | reject | 97 | 500 | 0.0075 | 0 | 8 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter500_spread0077 | reject | 97 | 500 | 0.0077 | 0 | 10 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter500_spread0085 | reject | 97 | 500 | 0.0085 | 0 | 17 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter500_spread0100 | reject | 97 | 500 | 0.0100 | 0 | 17 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter500_spread0106 | reject | 97 | 500 | 0.0106 | 0 | 19 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter500_spread0120 | reject | 97 | 500 | 0.0120 | 0 | 24 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter1000_spread0050 | reject | 97 | 1000 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter1000_spread0075 | reject | 97 | 1000 | 0.0075 | 0 | 8 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter1000_spread0077 | reject | 97 | 1000 | 0.0077 | 0 | 10 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter1000_spread0085 | reject | 97 | 1000 | 0.0085 | 0 | 17 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter1000_spread0100 | reject | 97 | 1000 | 0.0100 | 0 | 17 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter1000_spread0106 | reject | 97 | 1000 | 0.0106 | 0 | 19 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter1000_spread0120 | reject | 97 | 1000 | 0.0120 | 0 | 24 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter1500_spread0050 | reject | 97 | 1500 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age97_jitter1500_spread0075 | reject | 97 | 1500 | 0.0075 | 0 | 8 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 97, "max_ws_jitter_ms_for_caution": 300, "max_spread_ratio_for_caution": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
