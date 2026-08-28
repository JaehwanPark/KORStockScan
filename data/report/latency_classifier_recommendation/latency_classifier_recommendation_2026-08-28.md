# Latency Classifier Recommendation 2026-08-28

- latency_block_count: 305
- unique_codes: 66
- selected_profile_id: grid_age101_jitter300_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 576, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age101_jitter300_spread0050 | reject | 101 | 300 | 0.0050 | 0 | 1 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter300_spread0064 | reject | 101 | 300 | 0.0064 | 0 | 14 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter300_spread0075 | reject | 101 | 300 | 0.0075 | 0 | 22 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter300_spread0082 | reject | 101 | 300 | 0.0082 | 0 | 32 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter300_spread0085 | reject | 101 | 300 | 0.0085 | 0 | 33 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter300_spread0097 | reject | 101 | 300 | 0.0097 | 0 | 58 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter300_spread0100 | reject | 101 | 300 | 0.0100 | 0 | 59 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter300_spread0120 | reject | 101 | 300 | 0.0120 | 0 | 64 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter450_spread0050 | reject | 101 | 450 | 0.0050 | 0 | 1 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter450_spread0064 | reject | 101 | 450 | 0.0064 | 0 | 14 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter450_spread0075 | reject | 101 | 450 | 0.0075 | 0 | 22 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter450_spread0082 | reject | 101 | 450 | 0.0082 | 0 | 32 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter450_spread0085 | reject | 101 | 450 | 0.0085 | 0 | 33 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter450_spread0097 | reject | 101 | 450 | 0.0097 | 0 | 58 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter450_spread0100 | reject | 101 | 450 | 0.0100 | 0 | 59 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter450_spread0120 | reject | 101 | 450 | 0.0120 | 0 | 64 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter500_spread0050 | reject | 101 | 500 | 0.0050 | 0 | 1 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter500_spread0064 | reject | 101 | 500 | 0.0064 | 0 | 14 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter500_spread0075 | reject | 101 | 500 | 0.0075 | 0 | 22 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter500_spread0082 | reject | 101 | 500 | 0.0082 | 0 | 32 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter500_spread0085 | reject | 101 | 500 | 0.0085 | 0 | 33 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter500_spread0097 | reject | 101 | 500 | 0.0097 | 0 | 58 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter500_spread0100 | reject | 101 | 500 | 0.0100 | 0 | 59 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter500_spread0120 | reject | 101 | 500 | 0.0120 | 0 | 64 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter534_spread0050 | reject | 101 | 534 | 0.0050 | 0 | 1 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter534_spread0064 | reject | 101 | 534 | 0.0064 | 0 | 14 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter534_spread0075 | reject | 101 | 534 | 0.0075 | 0 | 22 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter534_spread0082 | reject | 101 | 534 | 0.0082 | 0 | 32 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter534_spread0085 | reject | 101 | 534 | 0.0085 | 0 | 33 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter534_spread0097 | reject | 101 | 534 | 0.0097 | 0 | 58 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 101, "max_ws_jitter_ms_for_caution": 300, "max_spread_ratio_for_caution": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
